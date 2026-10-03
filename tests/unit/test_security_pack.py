import base64
import io
import json
from pathlib import Path

import pytest
import yaml

from app.control_layer.attack_signatures import (
    AttackCatalog,
    AttackSignature,
    KnownAttackSignaturesControl,
)
from app.control_layer.audit import JsonLinesAuditSink
from app.control_layer.composition import default_controls, default_targets
from app.control_layer.domain import Action, Finding, Interaction, PolicyError, Span
from app.control_layer.policy import (
    decide,
    forwarded_interaction,
    load_policy,
    validate_findings,
)
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.service import InteractionService
from app.control_layer.targets import (
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
    TargetResult,
)

DEFAULT_POLICY = Path(__file__).resolve().parents[2] / "config" / "policy.yaml"
EXPECTED = {
    "email-address": ("pii.email",),
    "bearer-credential": ("secret.bearer",),
    "pem-private-key": ("secret.pem_private_key",),
    "github-token": ("secret.github_pat", "secret.github_oauth"),
    "us-ssn": ("pii.us_ssn",),
    "known-attack-signatures": (
        "attack.pickle_os_system",
        "attack.pickle_posix_system",
        "attack.python_os_system",
        "attack.python_exec_base64",
    ),
}


def policy_file(tmp_path, mutate=None):
    raw = yaml.safe_load(DEFAULT_POLICY.read_text())
    if mutate:
        mutate(raw)
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw))
    return path


def test_default_registration_ownership_capabilities_policy_and_targets():
    registry = default_controls()
    assert [r.definition.id for r in registry.registrations] == list(EXPECTED)
    codes = []
    for r in registry.registrations:
        assert tuple(f.code for f in r.definition.findings) == EXPECTED[r.definition.id]
        for f in r.definition.findings:
            assert f.span_required is True
            assert f.supports_redaction is (
                r.definition.id != "known-attack-signatures"
            )
            codes.append(f.code)
    assert len(codes) == len(set(codes)) == 10
    bound = load_policy(DEFAULT_POLICY, registry)
    assert all(e.enabled for e in bound.entries)
    for entry in bound.entries:
        assert entry.registration is registry.resolve(entry.control_id)
        for code, action in entry.mappings:
            assert action == (
                Action.REDACT if code.startswith("pii.") else Action.BLOCK
            )
    assert [t.definition.target_id for t in default_targets().registrations] == [
        "local-echo",
        "local-ollama",
    ]


def test_catalog_code_collision_with_another_control_rejected():
    cat = AttackCatalog(
        "test-catalog", (AttackSignature("test", "attack.shared", "abcdefgh"),)
    )
    evaluator = KnownAttackSignaturesControl(cat)
    regs = tuple(
        ControlRegistration(
            ControlDefinition(id, (FindingDefinition("attack.shared", True, False),)),
            evaluator
            if id == evaluator.id
            else type("Other", (), {"evaluate": lambda self, i: ()})(),
        )
        for id in (evaluator.id, "other")
    )
    with pytest.raises(ValueError, match="invalid_registration"):
        ControlRegistry(regs)


@pytest.mark.parametrize("id", list(EXPECTED))
def test_missing_control_entry_rejected(tmp_path, id):
    path = policy_file(tmp_path, lambda raw: raw["controls"].pop(id))
    with pytest.raises(PolicyError):
        load_policy(path, default_controls())


@pytest.mark.parametrize("id", list(EXPECTED))
def test_missing_enabled_code_rejected(tmp_path, id):
    def mutate(raw):
        code = EXPECTED[id][0]
        del raw["controls"][id]["findings"][code]

    with pytest.raises(PolicyError):
        load_policy(policy_file(tmp_path, mutate), default_controls())


def test_email_only_policy_requires_explicit_disabled_migration(tmp_path):
    def mutate(raw):
        raw["controls"] = {"email-address": raw["controls"]["email-address"]}

    path = policy_file(tmp_path, mutate)
    registry = default_controls()
    with pytest.raises(PolicyError):
        load_policy(path, registry)
    raw = yaml.safe_load(path.read_text())
    raw["controls"].update(
        {id: {"enabled": False} for id in EXPECTED if id != "email-address"}
    )
    path.write_text(yaml.safe_dump(raw))
    bound = load_policy(path, registry)
    assert [e.control_id for e in bound.entries if e.enabled] == ["email-address"]


PEM_VALUE = (
    "-----BEGIN PRIVATE KEY-----\n"
    + base64.b64encode(b"synthetic-private-key-fixture-32!!").decode()
    + "\n-----END PRIVATE KEY-----"
)
PAT_VALUE = "ghp_" + "A" * 36
OAUTH_VALUE = "gho_" + "B" * 36
SAMPLES = {
    "pii.email": ("<alice@example.com>", "alice@example.com"),
    "secret.bearer": (
        "Authorization: Bearer UniqueSyntheticBearer==",
        "UniqueSyntheticBearer==",
    ),
    "secret.pem_private_key": (PEM_VALUE, PEM_VALUE),
    "secret.github_pat": (PAT_VALUE, PAT_VALUE),
    "secret.github_oauth": (OAUTH_VALUE, OAUTH_VALUE),
    "pii.us_ssn": ("SSN: 123-45-6789", "123-45-6789"),
    "attack.pickle_os_system": ("cos\nsystem\n", "cos\nsystem\n"),
    "attack.pickle_posix_system": ("cposix\nsystem\n", "cposix\nsystem\n"),
    "attack.python_os_system": ("__import__('os').system(", "__import__('os').system("),
    "attack.python_exec_base64": ("exec(base64.b64decode(", "exec(base64.b64decode("),
}
ALL_TEXT = "\n".join(
    [
        "😀 <alice@example.com>",
        "Authorization: Bearer " + PAT_VALUE,
        PEM_VALUE,
        OAUTH_VALUE,
        "SSN: 123-45-6789",
        "cos\nsystem\n",
        "cposix\nsystem\n",
        "__import__('os').system(",
        "exec(base64.b64decode(",
    ]
)


def mapped_policy(tmp_path, action="ALLOW", *, changes=None, registry=None):
    def mutate(raw):
        for config in raw["controls"].values():
            for code in config["findings"]:
                config["findings"][code] = (
                    "ALLOW"
                    if code.startswith("attack.") and action == "REDACT"
                    else action
                )
        if changes:
            changes(raw)

    return load_policy(policy_file(tmp_path, mutate), registry or default_controls())


class AuditCheckingTarget:
    def __init__(self, stream):
        self.stream = stream
        self.calls = []

    def invoke(self, interaction):
        records = [json.loads(line) for line in self.stream.getvalue().splitlines()]
        assert any(
            r["interaction_id"] == str(interaction.id) and r["forwarding_eligible"]
            for r in records
        )
        self.calls.append(interaction)
        return TargetResult(interaction.content)


def service_for(policy, stream=None, sink=None):
    stream = stream if stream is not None else io.StringIO()
    target = AuditCheckingTarget(stream)
    service = InteractionService(
        policy,
        sink or JsonLinesAuditSink(stream),
        TargetRegistry((RegisteredTarget(TargetDefinition("local-echo"), target),)),
    )
    return service, target, stream


@pytest.mark.parametrize("code", list(SAMPLES))
@pytest.mark.parametrize("action", ["ALLOW", "REDACT", "BLOCK"])
def test_each_finding_supported_policy_actions_and_audit_privacy(
    tmp_path, code, action
):
    content, value = SAMPLES[code]
    if code.startswith("attack.") and action == "REDACT":
        owner = "known-attack-signatures"
        path = policy_file(
            tmp_path,
            lambda raw: raw["controls"][owner]["findings"].update({code: action}),
        )
        with pytest.raises(PolicyError):
            load_policy(path, default_controls())
        return
    service, target, stream = service_for(mapped_policy(tmp_path, action))
    interaction = Interaction.create("local-echo", content)
    outcome = service.evaluate(interaction)
    assert outcome.error_code is None
    assert outcome.decision.action.value == action
    assert [r.finding.code for r in outcome.decision.resolutions] == [code]
    assert value not in stream.getvalue()
    record = json.loads(stream.getvalue())
    assert record["finding_counts"] == {code: 1}
    assert set(record["control_status"]) == set(EXPECTED)
    assert (
        not {
            "content",
            "span",
            "spans",
            "literal",
            "matched_value",
            "exception",
            "content_hash",
        }
        & record.keys()
    )
    if action == "BLOCK":
        assert target.calls == [] and outcome.target_result is None
    elif action == "ALLOW":
        assert target.calls == [interaction] and target.calls[0] is interaction
    else:
        assert target.calls[0].content == content.replace(value, "[REDACTED]")
        assert value not in outcome.target_result.content


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("code", EXPECTED["known-attack-signatures"])
def test_attack_redact_rejected_even_disabled(tmp_path, enabled, code):
    def mutate(raw):
        raw["controls"]["known-attack-signatures"]["enabled"] = enabled
        raw["controls"]["known-attack-signatures"]["findings"][code] = "REDACT"

    with pytest.raises(PolicyError):
        load_policy(policy_file(tmp_path, mutate), default_controls())


@pytest.mark.parametrize("disabled", list(EXPECTED))
def test_disabled_real_control_skipped_and_audited(tmp_path, disabled):
    bound = mapped_policy(
        tmp_path, changes=lambda raw: raw["controls"][disabled].update(enabled=False)
    )
    service, _, stream = service_for(bound)
    outcome = service.evaluate(Interaction.create("local-echo", ALL_TEXT))
    assert outcome.error_code is None
    assert disabled not in outcome.decision.evaluated_controls
    assert all(r.finding.control_id != disabled for r in outcome.decision.resolutions)
    assert json.loads(stream.getvalue())["control_status"][disabled] is False


@pytest.mark.parametrize(
    "content,expected",
    [
        ("ordinary unchanged 😀", "ALLOW"),
        ("<alice@example.com>", "REDACT"),
        ("<alice@example.com>\n" + PAT_VALUE, "BLOCK"),
        ("SSN: 123-45-6789\n" + PAT_VALUE, "BLOCK"),
        ("__import__('os').system( <alice@example.com>", "BLOCK"),
        (ALL_TEXT, "BLOCK"),
    ],
)
def test_real_cross_control_default_policy(tmp_path, content, expected):
    bound = load_policy(DEFAULT_POLICY, default_controls())
    service, target, _ = service_for(bound)
    outcome = service.evaluate(Interaction.create("local-echo", content))
    assert outcome.error_code is None
    assert outcome.decision.action.value == expected
    if content == ALL_TEXT:
        assert {r.finding.control_id for r in outcome.decision.resolutions} == set(
            EXPECTED
        )
        assert {r.finding.code for r in outcome.decision.resolutions} == set(SAMPLES)
    assert len(target.calls) == (0 if expected == "BLOCK" else 1)


@pytest.mark.parametrize("action", ["ALLOW", "REDACT", "BLOCK"])
@pytest.mark.parametrize("reverse_registry", [False, True])
@pytest.mark.parametrize("reverse_findings", [False, True])
def test_registration_finding_and_yaml_order_cannot_weaken_policy(
    tmp_path, action, reverse_registry, reverse_findings
):
    controls = default_controls()
    if reverse_registry:
        controls = ControlRegistry(tuple(reversed(controls.registrations)))
    bound = mapped_policy(tmp_path, action, registry=controls)
    interaction = Interaction.create("local-echo", ALL_TEXT)
    findings = []
    for entry in bound.entries:
        findings.extend(
            validate_findings(
                entry.registration.evaluator.evaluate(interaction),
                entry.registration,
                interaction.content,
            )
        )
    if reverse_findings:
        findings.reverse()
    decision = decide(
        interaction, tuple(findings), tuple(e.control_id for e in bound.entries), bound
    )
    assert decision.action.value == action
    forwarded = forwarded_interaction(interaction, decision)
    if action == "BLOCK":
        assert forwarded is None
    elif action == "ALLOW":
        assert forwarded is interaction
    else:
        assert forwarded.content == "\n".join(
            [
                "😀 <[REDACTED]>",
                "Authorization: Bearer [REDACTED]",
                "[REDACTED]",
                "[REDACTED]",
                "SSN: [REDACTED]",
                "cos\nsystem\n",
                "cposix\nsystem\n",
                "__import__('os').system(",
                "exec(base64.b64decode(",
            ]
        )


@pytest.mark.parametrize(
    "bearer,github,expected",
    [
        ("ALLOW", "BLOCK", "BLOCK"),
        ("BLOCK", "REDACT", "BLOCK"),
        ("REDACT", "ALLOW", "REDACT"),
        ("REDACT", "REDACT", "REDACT"),
    ],
)
def test_overlapping_real_bearer_github_findings(tmp_path, bearer, github, expected):
    def changes(raw):
        raw["controls"]["bearer-credential"]["findings"]["secret.bearer"] = bearer
        raw["controls"]["github-token"]["findings"]["secret.github_pat"] = github

    service, target, _ = service_for(mapped_policy(tmp_path, changes=changes))
    interaction = Interaction.create("local-echo", "Authorization: Bearer " + PAT_VALUE)
    outcome = service.evaluate(interaction)
    assert outcome.decision.action.value == expected
    resolutions = outcome.decision.resolutions
    assert [r.finding.code for r in resolutions] == [
        "secret.bearer",
        "secret.github_pat",
    ]
    assert resolutions[0].finding.span == resolutions[1].finding.span
    if expected == "BLOCK":
        assert target.calls == []
    else:
        assert target.calls[0].content == "Authorization: Bearer [REDACTED]"
        assert target.calls[0].id == interaction.id
        assert target.calls[0].target_id == interaction.target_id


def test_selective_original_spans_multiple_real_values_unicode(tmp_path):
    def changes(raw):
        raw["controls"]["github-token"]["findings"]["secret.github_oauth"] = "ALLOW"

    bound = mapped_policy(tmp_path, "REDACT", changes=changes)
    service, target, _ = service_for(bound)
    text = (
        f"😀 é <alice@example.com>, SSN:\t123-45-6789. '{PAT_VALUE}' "
        f"({OAUTH_VALUE})\nAuthorization: Bearer {PAT_VALUE}\nSSN:321-54-6789"
    )
    interaction = Interaction.create("local-echo", text)
    outcome = service.evaluate(interaction)
    assert outcome.decision.action == Action.REDACT
    assert target.calls[0].content == (
        f"😀 é <[REDACTED]>, SSN:\t[REDACTED]. '[REDACTED]' "
        f"({OAUTH_VALUE})\nAuthorization: Bearer [REDACTED]\nSSN:[REDACTED]"
    )
    assert interaction.content == text


class InvalidEvaluator:
    def __init__(self, output=None, failure=False):
        self.output = output
        self.failure = failure

    def evaluate(self, interaction):
        if self.failure:
            raise RuntimeError("RAW_EXCEPTION_SECRET " + interaction.content)
        return self.output


def replaced_registry(owner, evaluator):
    return ControlRegistry(
        tuple(
            ControlRegistration(r.definition, evaluator)
            if r.definition.id == owner
            else r
            for r in default_controls().registrations
        )
    )


@pytest.mark.parametrize("owner", list(EXPECTED))
@pytest.mark.parametrize("action", ["ALLOW", "REDACT", "BLOCK"])
@pytest.mark.parametrize(
    "case",
    [
        "unknown",
        "foreign",
        "producer",
        "missing_span",
        "boolean",
        "negative",
        "over_limit",
        "empty",
        "float",
        "wrong_span",
        "wrong_container",
        "wrong_finding",
        "wrong_code_type",
        "wrong_id_type",
    ],
)
def test_expanded_registration_untrusted_outputs_fail_closed(
    tmp_path, owner, action, case
):
    code = EXPECTED[owner][0]
    other = next(id for id in EXPECTED if id != owner)
    output = (Finding(owner, code, Span(0, 1)),)
    if case == "unknown":
        output = (Finding(owner, "RAW_UNTRUSTED_SECRET", Span(0, 1)),)
    elif case == "foreign":
        output = (Finding(owner, EXPECTED[other][0], Span(0, 1)),)
    elif case == "producer":
        output = (Finding(other, EXPECTED[other][0], Span(0, 1)),)
    elif case == "wrong_container":
        output = list(output)
    elif case == "wrong_finding":
        output = ("RAW_UNTRUSTED_SECRET",)
    elif case == "wrong_code_type":
        output = (Finding(owner, 1, Span(0, 1)),)
    elif case == "wrong_id_type":
        output = (Finding(1, code, Span(0, 1)),)
    else:
        spans = {
            "missing_span": None,
            "boolean": Span(False, 1),
            "negative": Span(-1, 1),
            "over_limit": Span(0, len(ALL_TEXT) + 1),
            "empty": Span(1, 1),
            "float": Span(0.0, 1),
            "wrong_span": "RAW_UNTRUSTED_SECRET",
        }
        output = (Finding(owner, code, spans[case]),)
    registry = replaced_registry(owner, InvalidEvaluator(output))
    service, target, stream = service_for(
        mapped_policy(tmp_path, action, registry=registry)
    )
    result = service.evaluate(Interaction.create("local-echo", ALL_TEXT))
    assert result.error_code == "evaluation_failed"
    assert (
        result.decision is None and result.target_result is None and target.calls == []
    )
    record = json.loads(stream.getvalue())
    assert record["event_type"] == "operational_failure"
    assert "action" not in record and "finding_counts" not in record
    assert "RAW_UNTRUSTED_SECRET" not in stream.getvalue()
    assert PAT_VALUE not in stream.getvalue()


@pytest.mark.parametrize("owner", list(EXPECTED))
def test_secret_bearing_control_exception_is_sanitized(tmp_path, owner):
    registry = replaced_registry(owner, InvalidEvaluator(failure=True))
    service, target, stream = service_for(mapped_policy(tmp_path, registry=registry))
    outcome = service.evaluate(Interaction.create("local-echo", ALL_TEXT))
    assert outcome.error_code == "evaluation_failed" and outcome.decision is None
    assert target.calls == []
    for value in [
        PAT_VALUE,
        OAUTH_VALUE,
        PEM_VALUE,
        "alice@example.com",
        "123-45-6789",
        "RAW_EXCEPTION_SECRET",
        *[s[1] for c, s in SAMPLES.items() if c.startswith("attack.")],
    ]:
        assert value not in stream.getvalue()


class BrokenAuditStream(io.StringIO):
    def __init__(self, failure):
        super().__init__()
        self.failure = failure
        self.writes = 0

    def write(self, text):
        self.writes += 1
        if self.failure == "raise":
            raise OSError("RAW_AUDIT_SECRET")
        if self.failure == "short":
            super().write(text[:-1])
            return len(text) - 1
        return super().write(text)

    def flush(self):
        if self.failure == "flush":
            raise OSError("RAW_AUDIT_SECRET")
        return super().flush()


@pytest.mark.parametrize("failure", ["raise", "short", "flush"])
@pytest.mark.parametrize("action", ["ALLOW", "REDACT", "BLOCK"])
def test_mixed_control_audit_failure_poisoning_zero_dispatch(tmp_path, failure, action):
    stream = BrokenAuditStream(failure)
    service, target, _ = service_for(mapped_policy(tmp_path, action), stream)
    for _ in range(2):
        outcome = service.evaluate(Interaction.create("local-echo", ALL_TEXT))
        assert outcome.error_code == "audit_failed" and outcome.decision is None
        assert target.calls == []
    assert stream.writes == 1
    assert (
        PAT_VALUE not in stream.getvalue()
        and "RAW_AUDIT_SECRET" not in stream.getvalue()
    )


def test_new_trusted_literal_code_uses_unchanged_policy_engine(tmp_path):
    catalog = AttackCatalog(
        "external-local-fixture",
        (AttackSignature("new-local-id", "attack.new_local", "bounded-new-signature"),),
    )
    evaluator = KnownAttackSignaturesControl(catalog)
    registry = ControlRegistry(
        (
            ControlRegistration(
                ControlDefinition(
                    evaluator.id, (FindingDefinition("attack.new_local", True, False),)
                ),
                evaluator,
            ),
        )
    )
    path = tmp_path / "policy.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "policy_id": "new-local",
                "controls": {
                    evaluator.id: {
                        "enabled": True,
                        "findings": {"attack.new_local": "BLOCK"},
                    }
                },
            }
        )
    )
    service, target, stream = service_for(load_policy(path, registry))
    result = service.evaluate(Interaction.create("local-echo", "bounded-new-signature"))
    assert result.decision.action == Action.BLOCK and target.calls == []
    assert json.loads(stream.getvalue())["finding_counts"] == {"attack.new_local": 1}
    assert "bounded-new-signature" not in stream.getvalue()

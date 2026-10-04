"""Explicit deterministic production control pack and unchanged local echo."""

from dataclasses import replace

from app.control_layer.attack_signatures import (
    ATTACK_CONTROL_ID,
    KnownAttackSignaturesControl,
    load_attack_catalog,
)
from app.control_layer.bearer_control import (
    BEARER_CODE,
    BEARER_CONTROL_ID,
    BearerCredentialControl,
)
from app.control_layer.controls import EMAIL_CODE, EMAIL_CONTROL_ID, EmailAddressControl
from app.control_layer.domain import PolicyError
from app.control_layer.github_control import (
    GITHUB_CONTROL_ID,
    GITHUB_OAUTH_CODE,
    GITHUB_PAT_CODE,
    GitHubTokenControl,
)
from app.control_layer.ollama_semantic import (
    OllamaSemanticRuntime,
    load_semantic_settings,
)
from app.control_layer.ollama_target import OllamaTextTarget, load_ollama_settings
from app.control_layer.pem_control import PEM_CODE, PEM_CONTROL_ID, PemPrivateKeyControl
from app.control_layer.policy import BoundPolicy
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.semantic_control import (
    CODES,
    SEMANTIC_ID,
    SemanticSecurityControl,
)
from app.control_layer.ssn_control import SSN_CODE, SSN_CONTROL_ID, UsSsnControl
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
)
from app.control_layer.usage_control import (
    CODES as USAGE_CODES,
)
from app.control_layer.usage_control import (
    USAGE_ID,
    UsageBudgetControl,
    UsageMeter,
)


def default_controls() -> ControlRegistry:
    attacks = KnownAttackSignaturesControl(load_attack_catalog())
    settings = load_semantic_settings()
    return ControlRegistry(
        (
            ControlRegistration(
                ControlDefinition(
                    EMAIL_CONTROL_ID, (FindingDefinition(EMAIL_CODE, True, True),)
                ),
                EmailAddressControl(),
            ),
            ControlRegistration(
                ControlDefinition(
                    BEARER_CONTROL_ID, (FindingDefinition(BEARER_CODE, True, True),)
                ),
                BearerCredentialControl(),
            ),
            ControlRegistration(
                ControlDefinition(
                    PEM_CONTROL_ID, (FindingDefinition(PEM_CODE, True, True),)
                ),
                PemPrivateKeyControl(),
            ),
            ControlRegistration(
                ControlDefinition(
                    GITHUB_CONTROL_ID,
                    (
                        FindingDefinition(GITHUB_PAT_CODE, True, True),
                        FindingDefinition(GITHUB_OAUTH_CODE, True, True),
                    ),
                ),
                GitHubTokenControl(),
            ),
            ControlRegistration(
                ControlDefinition(
                    SSN_CONTROL_ID, (FindingDefinition(SSN_CODE, True, True),)
                ),
                UsSsnControl(),
            ),
            ControlRegistration(
                ControlDefinition(
                    ATTACK_CONTROL_ID,
                    tuple(
                        FindingDefinition(code, True, False)
                        for code in attacks.finding_codes
                    ),
                ),
                attacks,
            ),
            ControlRegistration(
                ControlDefinition(
                    USAGE_ID,
                    tuple(
                        FindingDefinition(code, False, False) for code in USAGE_CODES
                    ),
                ),
                UsageBudgetControl(UsageMeter()),
            ),
            ControlRegistration(
                ControlDefinition(
                    SEMANTIC_ID,
                    tuple(FindingDefinition(code, False, False) for code in CODES),
                    model_id=settings.model,
                ),
                SemanticSecurityControl(OllamaSemanticRuntime(settings)),
            ),
        )
    )


def default_targets() -> TargetRegistry:
    settings = load_ollama_settings()
    return TargetRegistry(
        (
            RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),
            RegisteredTarget(
                TargetDefinition("local-ollama", model_id=settings.model),
                OllamaTextTarget(settings),
            ),
        )
    )


def bind_semantic_policy(policy: BoundPolicy) -> BoundPolicy:
    """Finalize even injected semantic controls through the same startup path."""
    entries = []
    for entry in policy.entries:
        if entry.control_id == SEMANTIC_ID:
            definition = entry.registration.definition
            evaluator = entry.registration.evaluator
            if (
                type(evaluator) is not SemanticSecurityControl
                or tuple(
                    (f.code, f.span_required, f.supports_redaction)
                    for f in definition.findings
                )
                != tuple((code, False, False) for code in CODES)
                or definition.model_id is None
            ):
                raise PolicyError()
            if (
                type(evaluator.runtime) is OllamaSemanticRuntime
                and evaluator.runtime.settings.model != definition.model_id
            ):
                raise PolicyError()
            evaluator = replace(evaluator, threshold=entry.semantic_threshold)
            entry = replace(
                entry, registration=ControlRegistration(definition, evaluator)
            )
        entries.append(entry)
    return replace(policy, entries=tuple(entries))


def bind_usage_policy(policy: BoundPolicy) -> BoundPolicy:
    """Give each bound policy its own meter and its validated policy limits."""
    entries = []
    for entry in policy.entries:
        if entry.control_id == USAGE_ID:
            definition = entry.registration.definition
            evaluator = entry.registration.evaluator
            if (
                type(evaluator) is not UsageBudgetControl
                or type(evaluator.meter) is not UsageMeter
                or tuple(
                    (f.code, f.span_required, f.supports_redaction)
                    for f in definition.findings
                )
                != tuple((code, False, False) for code in USAGE_CODES)
                or (entry.enabled and entry.limits is None)
            ):
                raise PolicyError()
            evaluator = UsageBudgetControl(evaluator.meter.fresh(), entry.limits)
            entry = replace(
                entry, registration=ControlRegistration(definition, evaluator)
            )
        entries.append(entry)
    return replace(policy, entries=tuple(entries))


def bind_policy(policy: BoundPolicy) -> BoundPolicy:
    """Startup binding shared by the application and every demo profile."""
    return bind_usage_policy(bind_semantic_policy(policy))

"""Explicit deterministic production control pack and unchanged local echo."""

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
from app.control_layer.github_control import (
    GITHUB_CONTROL_ID,
    GITHUB_OAUTH_CODE,
    GITHUB_PAT_CODE,
    GitHubTokenControl,
)
from app.control_layer.pem_control import PEM_CODE, PEM_CONTROL_ID, PemPrivateKeyControl
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.ssn_control import SSN_CODE, SSN_CONTROL_ID, UsSsnControl
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
)


def default_controls() -> ControlRegistry:
    attacks = KnownAttackSignaturesControl(load_attack_catalog())
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
        )
    )


def default_targets() -> TargetRegistry:
    return TargetRegistry(
        (RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),)
    )

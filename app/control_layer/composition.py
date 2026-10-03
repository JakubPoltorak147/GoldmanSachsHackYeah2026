"""Explicit production composition: only existing email and local echo."""

from app.control_layer.controls import EMAIL_CODE, EMAIL_CONTROL_ID, EmailAddressControl
from app.control_layer.registry import (
    ControlDefinition,
    ControlRegistration,
    ControlRegistry,
    FindingDefinition,
)
from app.control_layer.targets import (
    LocalEchoTarget,
    RegisteredTarget,
    TargetDefinition,
    TargetRegistry,
)


def default_controls() -> ControlRegistry:
    return ControlRegistry(
        (
            ControlRegistration(
                ControlDefinition(
                    EMAIL_CONTROL_ID, (FindingDefinition(EMAIL_CODE, True, True),)
                ),
                EmailAddressControl(),
            ),
        )
    )


def default_targets() -> TargetRegistry:
    return TargetRegistry(
        (RegisteredTarget(TargetDefinition("local-echo"), LocalEchoTarget()),)
    )

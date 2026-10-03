"""Safe decision records and synchronized, fail-closed JSON-lines emission."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol, TextIO
from uuid import UUID

from app.control_layer.domain import Action, AuditError


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    interaction_id: UUID
    timestamp: datetime
    target_id: str
    policy_digest: str
    evaluated_controls: tuple[str, ...]
    control_status: tuple[tuple[str, bool], ...]
    action: Action | None
    finding_counts: tuple[tuple[str, int], ...]
    forwarding_eligible: bool
    evaluation_duration_ms: float
    error_code: str | None = None

    def safe_record(self) -> dict:
        # Explicit field selection: never serialize domain objects or exceptions.
        record = {
            "event_type": self.event_type,
            "interaction_id": str(self.interaction_id),
            "timestamp": self.timestamp.astimezone(UTC).isoformat(),
            "target_id": self.target_id,
            "policy_digest": self.policy_digest,
            "evaluated_controls": list(self.evaluated_controls),
            "control_status": dict(self.control_status),
            "forwarding_eligible": self.forwarding_eligible,
            "evaluation_duration_ms": self.evaluation_duration_ms,
        }
        if self.action is not None:
            record["action"] = self.action.value
            record["finding_counts"] = dict(self.finding_counts)
        if self.error_code is not None:
            record["error_code"] = self.error_code
        return record


class AuditSink(Protocol):
    def emit(self, event: AuditEvent) -> None: ...


class JsonLinesAuditSink:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lock = Lock()
        self._healthy = True

    def emit(self, event: AuditEvent) -> None:
        try:
            line = json.dumps(event.safe_record(), allow_nan=False) + "\n"
        except Exception:
            raise AuditError() from None
        with self._lock:
            if not self._healthy:
                raise AuditError()
            try:
                written = self._stream.write(line)
                if type(written) is not int or written != len(line):
                    raise AuditError()
                self._stream.flush()
            except Exception:
                self._healthy = False
                raise AuditError() from None

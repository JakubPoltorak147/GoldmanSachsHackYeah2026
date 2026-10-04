"""SQLite persistence and bounded typed queries; no interaction content accepted."""

import os
import re
import sqlite3
from collections import Counter
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from uuid import UUID

from app.control_layer.audit import AuditEvent, AuditSink
from app.control_layer.domain import Action, AuditError
from app.control_layer.reporting import (
    Completion,
    EventFilter,
    EventView,
    FindingCount,
    FindingSummary,
    GroupBy,
    GroupSummary,
    InvocationStatus,
    ReportingError,
    ReportingEvent,
    ReportingProjection,
    Summary,
    SummaryResult,
    TimingSummary,
)

_SCHEMA = """
CREATE TABLE audit_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 interaction_id TEXT NOT NULL UNIQUE, timestamp TEXT NOT NULL,
 event_type TEXT NOT NULL CHECK(event_type IN ('decision','operational_failure')),
 target_id TEXT NOT NULL, model_id TEXT, policy_digest TEXT NOT NULL,
 action TEXT CHECK(action IN ('ALLOW','REDACT','BLOCK')), reason_code TEXT,
 error_code TEXT,
 forwarding_eligible INTEGER NOT NULL CHECK(forwarding_eligible IN (0,1)),
 evaluation_duration_ms REAL NOT NULL CHECK(evaluation_duration_ms >= 0)
);
CREATE TABLE event_controls (
 interaction_id TEXT NOT NULL REFERENCES audit_events(interaction_id),
 control_id TEXT NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
 ordinal INTEGER NOT NULL, evaluation_ordinal INTEGER,
 PRIMARY KEY(interaction_id,control_id)
);
CREATE TABLE event_findings (
 interaction_id TEXT NOT NULL REFERENCES audit_events(interaction_id),
 control_id TEXT NOT NULL, code TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('ALLOW','REDACT','BLOCK')),
 count INTEGER NOT NULL CHECK(count > 0), PRIMARY KEY(interaction_id,code)
);
CREATE TABLE invocation_outcomes (
 interaction_id TEXT PRIMARY KEY REFERENCES audit_events(interaction_id),
 completed_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('succeeded','failed')),
 invocation_duration_ms REAL NOT NULL CHECK(invocation_duration_ms >= 0),
 total_duration_ms REAL NOT NULL CHECK(total_duration_ms >= invocation_duration_ms)
);
CREATE TRIGGER eligible_outcome BEFORE INSERT ON invocation_outcomes
 WHEN NOT EXISTS (SELECT 1 FROM audit_events WHERE interaction_id=NEW.interaction_id
 AND event_type='decision' AND forwarding_eligible=1)
 BEGIN SELECT RAISE(ABORT, 'ineligible_outcome'); END;
CREATE INDEX event_timestamp ON audit_events(timestamp);
PRAGMA user_version=1;
"""


def _expected_schema() -> dict[str, str]:
    # Use SQLite's parser to delimit the trigger body (which has inner semicolons).
    # Compare the versioned DDL, not just table names, so keys/checks/FKs/triggers
    # are startup contracts too. Formatting differences in whitespace are harmless.
    objects = {}
    statement = ""
    for character in _SCHEMA:
        statement += character
        if character == ";" and sqlite3.complete_statement(statement):
            sql = statement.strip().removesuffix(";")
            match = re.match(r"CREATE (?:TABLE|TRIGGER|INDEX) (\w+)", sql)
            if match:
                objects[match[1]] = " ".join(sql.split())
            statement = ""
    return objects


_EXPECTED_SCHEMA = _expected_schema()

_STATUS = (
    "CASE WHEN o.status IS NOT NULL THEN o.status "
    "WHEN e.forwarding_eligible=1 THEN 'unknown' ELSE 'not_invoked' END"
)
_BASE = (
    "SELECT e.*, o.completed_at, o.status, o.invocation_duration_ms, "
    f"o.total_duration_ms, {_STATUS} AS invocation_status FROM audit_events e "
    "LEFT JOIN invocation_outcomes o USING(interaction_id)"
)
_EMPTY_FILTER = EventFilter()


def _time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


class ReportingStore:
    def __init__(self, path: str | Path):
        self._lock = RLock()
        self._healthy = True
        self._connection = None
        try:
            if (
                not isinstance(path, (str, Path))
                or not str(path)
                or str(path) == ":memory:"
                or str(path).startswith("file:")
            ):
                raise ReportingError("invalid_reporting_configuration")
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Do not follow a symlink at the database destination. Parent permissions
            # and trusted operator ownership are deployment responsibilities.
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(destination, flags, 0o600)
            os.close(descriptor)
            connection = sqlite3.connect(
                destination, timeout=1, check_same_thread=False
            )
            self._connection = connection
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version != 1:
                if (
                    version != 0
                    or connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table'"
                    ).fetchone()
                ):
                    raise ReportingError("invalid_reporting_configuration")
                connection.executescript("BEGIN IMMEDIATE;\n" + _SCHEMA + "\nCOMMIT;")
            actual = {
                name: " ".join(sql.split())
                for name, sql in connection.execute(
                    "SELECT name,sql FROM sqlite_master "
                    "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
                )
            }
            if actual != _EXPECTED_SCHEMA:
                raise ReportingError("invalid_reporting_configuration")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")

        except ReportingError:
            self.close()
            raise
        except Exception:
            self.close()
            raise ReportingError() from None

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    @property
    def health(self) -> str:
        with self._lock:
            return (
                "healthy"
                if self._healthy and self._connection is not None
                else "reporting_write_failed"
            )

    def poison(self) -> None:
        with self._lock:
            self._healthy = False

    @contextmanager
    def _write(self):
        with self._lock:
            try:
                if not self._healthy or self._connection is None:
                    raise ReportingError()
                with self._connection:
                    yield self._connection
            except Exception:
                self._healthy = False
                raise ReportingError() from None

    def _append_event(self, event: ReportingEvent) -> None:
        # Internal writer: only the startup-bound projection supplies this DTO.
        with self._write() as db:
            identity = str(event.interaction_id)
            db.execute(
                """INSERT INTO audit_events
            (interaction_id,timestamp,event_type,target_id,model_id,policy_digest,
            action,reason_code,error_code,forwarding_eligible,evaluation_duration_ms)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    identity,
                    _time(event.timestamp),
                    event.event_type,
                    event.target_id,
                    event.model_id,
                    event.policy_digest,
                    event.action,
                    event.reason_code,
                    event.error_code,
                    int(event.forwarding_eligible),
                    event.evaluation_duration_ms,
                ),
            )
            db.executemany(
                "INSERT INTO event_controls VALUES (?,?,?,?,?)",
                (
                    (
                        identity,
                        control,
                        int(enabled),
                        ordinal,
                        event.evaluated_controls.index(control)
                        if control in event.evaluated_controls
                        else None,
                    )
                    for ordinal, (control, enabled) in enumerate(event.control_status)
                ),
            )
            db.executemany(
                "INSERT INTO event_findings VALUES (?,?,?,?,?)",
                (
                    (identity, f.control_id, f.code, f.action, f.count)
                    for f in event.findings
                ),
            )

    def _append_completion(self, completion: Completion) -> None:
        if type(completion) is not Completion:
            self.poison()
            raise ReportingError("invalid_reporting_record")
        with self._write() as db:
            db.execute(
                "INSERT INTO invocation_outcomes VALUES (?,?,?,?,?)",
                (
                    str(completion.interaction_id),
                    _time(completion.completed_at),
                    completion.status,
                    completion.invocation_duration_ms,
                    completion.total_duration_ms,
                ),
            )

    @contextmanager
    def _read(self):
        with self._lock:
            try:
                if self._connection is None:
                    raise ReportingError()
                self._connection.execute("BEGIN")
                yield self._connection
            except ReportingError:
                raise
            except Exception:
                raise ReportingError() from None
            finally:
                if self._connection is not None:
                    self._connection.rollback()

    def _selection(self, filters: EventFilter):
        if type(filters) is not EventFilter:
            raise ReportingError("invalid_reporting_query")
        clauses, args = [], []
        if filters.from_time is not None:
            clauses.extend(("timestamp >= ?", "timestamp < ?"))
            args.extend((_time(filters.from_time), _time(filters.to_time)))
        for name, value in (
            ("action", filters.action),
            ("target_id", filters.target_id),
            ("invocation_status", filters.invocation_status),
        ):
            if value is not None:
                clauses.append(f"{name} = ?")
                args.append(value)
        return "SELECT * FROM (" + _BASE + ")" + (
            " WHERE " + " AND ".join(clauses) if clauses else ""
        ), args

    def _view(self, db, row) -> EventView:
        identity = row["interaction_id"]
        controls = db.execute(
            "SELECT * FROM event_controls WHERE interaction_id=? ORDER BY ordinal",
            (identity,),
        ).fetchall()
        evaluated = sorted(
            (c for c in controls if c["evaluation_ordinal"] is not None),
            key=lambda c: c["evaluation_ordinal"],
        )
        findings = db.execute(
            "SELECT * FROM event_findings WHERE interaction_id=? ORDER BY code",
            (identity,),
        ).fetchall()
        event = ReportingEvent(
            UUID(identity),
            datetime.fromisoformat(row["timestamp"]),
            row["event_type"],
            row["target_id"],
            row["model_id"],
            row["policy_digest"],
            Action(row["action"]) if row["action"] else None,
            row["reason_code"],
            row["error_code"],
            bool(row["forwarding_eligible"]),
            row["evaluation_duration_ms"],
            tuple(c["control_id"] for c in evaluated),
            tuple((c["control_id"], bool(c["enabled"])) for c in controls),
            tuple(
                FindingCount(
                    f["control_id"], f["code"], Action(f["action"]), f["count"]
                )
                for f in findings
            ),
        )
        completion = (
            Completion(
                UUID(identity),
                datetime.fromisoformat(row["completed_at"]),
                InvocationStatus(row["status"]),
                row["invocation_duration_ms"],
                row["total_duration_ms"],
            )
            if row["status"]
            else None
        )
        return EventView(
            row["sequence"],
            event,
            InvocationStatus(row["invocation_status"]),
            completion,
        )

    def list_events(
        self,
        filters: EventFilter = _EMPTY_FILTER,
        *,
        limit: int = 100,
        after_sequence: int | None = None,
    ) -> tuple[EventView, ...]:
        if (
            type(limit) is not int
            or not 1 <= limit <= 1000
            or (
                after_sequence is not None
                and (type(after_sequence) is not int or after_sequence < 1)
            )
        ):
            raise ReportingError("invalid_reporting_query")
        selection, args = self._selection(filters)
        with self._read() as db:
            sql = f"SELECT * FROM ({selection})"
            if after_sequence is not None:
                sql += " WHERE sequence > ?"
                args.append(after_sequence)
            args.append(limit)
            rows = db.execute(sql + " ORDER BY sequence LIMIT ?", args).fetchall()
            return tuple(self._view(db, row) for row in rows)

    def get_event(self, interaction_id: UUID) -> EventView | None:
        if type(interaction_id) is not UUID:
            raise ReportingError("invalid_reporting_query")
        with self._read() as db:
            row = db.execute(
                _BASE + " WHERE e.interaction_id=?", (str(interaction_id),)
            ).fetchone()
            return self._view(db, row) if row else None

    def _summary(self, db, selection, args) -> Summary:
        cte = f"WITH selected AS ({selection}) "
        # Group event totals before any finding join.
        rows = db.execute(
            cte + "SELECT action,invocation_status,count(*) n FROM selected "
            "GROUP BY action,invocation_status",
            args,
        ).fetchall()
        actions, invocations = Counter(), Counter()
        for row in rows:
            actions[row["action"]] += row["n"]
            invocations[row["invocation_status"]] += row["n"]
        findings = db.execute(
            cte
            + """SELECT f.control_id,f.code,sum(f.count) occurrences,
            count(DISTINCT f.interaction_id) affected FROM event_findings f
            JOIN selected s USING(interaction_id) GROUP BY f.control_id,f.code
            ORDER BY f.control_id,f.code""",
            args,
        ).fetchall()
        timings = []
        for name in (
            "evaluation_duration_ms",
            "invocation_duration_ms",
            "total_duration_ms",
        ):
            row = db.execute(
                cte + f"SELECT count({name}),coalesce(sum({name}),0),min({name}),"
                f"max({name}),avg({name}) FROM selected",
                args,
            ).fetchone()
            timings.append(TimingSummary(*row))
        return Summary(
            sum(actions.values()),
            tuple((a, actions[a]) for a in Action),
            actions[None],
            tuple((s, invocations[s]) for s in InvocationStatus),
            tuple(FindingSummary(*f) for f in findings),
            *timings,
        )

    def summarize(
        self, filters: EventFilter, *, group_by: GroupBy | None = None
    ) -> SummaryResult:
        selection, args = self._selection(filters)
        if (
            filters.from_time is None
            or filters.to_time - filters.from_time > timedelta(days=31)
            or (group_by is not None and type(group_by) is not GroupBy)
        ):
            raise ReportingError("invalid_reporting_query")
        with self._read() as db:
            overall = self._summary(db, selection, args)
            groups = []
            if group_by is not None:
                keys = db.execute(
                    f"SELECT DISTINCT {group_by.value} FROM ({selection}) "
                    f"ORDER BY {group_by.value} LIMIT 1001",
                    args,
                ).fetchall()
                if len(keys) > 1000:
                    raise ReportingError("reporting_limit_exceeded")
                for (key,) in keys:
                    scoped = f"SELECT * FROM ({selection}) WHERE {group_by.value} IS ?"
                    groups.append(
                        GroupSummary(key, self._summary(db, scoped, [*args, key]))
                    )
            return SummaryResult(overall, tuple(groups))


class PersistentAuditSink:
    """One synchronized required gate; completion failure closes subsequent gates."""

    def __init__(
        self,
        upstream: AuditSink,
        store: ReportingStore,
        projection: ReportingProjection,
    ):
        self.upstream = upstream
        self.store = store
        self.projection = projection
        self._lock = RLock()

    def emit(self, event: AuditEvent) -> None:
        with self._lock:
            try:
                if self.store.health != "healthy":
                    raise AuditError()
                safe = self.projection.project(event)
                self.upstream.emit(event)
                self.store._append_event(safe)
            except Exception:
                self.store.poison()
                raise AuditError() from None

    def complete(
        self,
        interaction_id: UUID,
        status: InvocationStatus,
        invocation_duration_ms: float,
        total_duration_ms: float,
    ) -> None:
        with self._lock:
            try:
                completion = Completion(
                    interaction_id,
                    datetime.now(UTC),
                    status,
                    invocation_duration_ms,
                    total_duration_ms,
                )
                self.store._append_completion(completion)
            except Exception:
                # Already dispatched: preserve original outcome, never retry.
                self.store.poison()

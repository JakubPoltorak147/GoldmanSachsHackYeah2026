SCHEMA_V1 = """
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

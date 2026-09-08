-- Applied in full at startup. There are no migrations: the schema is one file
-- and the store is created from it, so what a fresh instance has and what a
-- running one has cannot drift.

CREATE TABLE IF NOT EXISTS cases (
    case_id     text PRIMARY KEY,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runs (
    run_id      uuid PRIMARY KEY,
    case_id     text NOT NULL REFERENCES cases (case_id),
    state       text NOT NULL CHECK (state IN ('RUNNING', 'COMPLETE', 'FAILED')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- seq is per-run and monotonic, allocated under the run row lock. Append-only.
CREATE TABLE IF NOT EXISTS run_events (
    run_id  uuid NOT NULL REFERENCES runs (run_id),
    seq     integer NOT NULL CHECK (seq > 0),
    kind    text NOT NULL,
    at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, seq)
);

-- One accepted output per node per run. The digest is a column, not the key:
-- the blob store is what deduplicates bytes, and two runs of a deterministic
-- module legitimately produce the same digest while each keeps its own row.
CREATE TABLE IF NOT EXISTS artifacts (
    run_id      uuid NOT NULL REFERENCES runs (run_id),
    node_id     text NOT NULL,
    sha256      char(64) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, node_id)
);

-- Money: numeric, never a float. A charge is never negative.
CREATE TABLE IF NOT EXISTS budget_ledger (
    entry_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id    uuid NOT NULL REFERENCES runs (run_id),
    node_id   text NOT NULL,
    amount    numeric(18, 6) NOT NULL CHECK (amount >= 0),
    at        timestamptz NOT NULL DEFAULT now()
);

-- Append-only means append-only. Enforced by the store, not by convention:
-- a UPDATE or DELETE path that exists is a path that gets used.
CREATE OR REPLACE FUNCTION refuse_rewrite() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'APPEND_ONLY_TABLE';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER run_events_append_only
    BEFORE UPDATE OR DELETE ON run_events
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

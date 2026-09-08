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

-- One user-provided document admitted into a case.
CREATE TABLE IF NOT EXISTS sources (
    source_id   uuid PRIMARY KEY,
    case_id     text NOT NULL REFERENCES cases (case_id),
    sha256      char(64) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (case_id, sha256)
);

-- The coordinate index behind invariant 11: one row per extracted text run with
-- its page and rectangle. Tokens are never returned to a module; they exist so
-- the host can re-locate a quote and refuse one it cannot. Keyed so that one
-- page is one index range -- never a whole-source scan.
CREATE TABLE IF NOT EXISTS source_tokens (
    source_id  uuid NOT NULL REFERENCES sources (source_id),
    page       integer NOT NULL CHECK (page > 0),
    -- Both assigned by the extractor. A block is a column or a paragraph; a
    -- quote may wrap onto the next line of its own block and nowhere else, so
    -- two columns sharing a y-band cannot be joined into a phrase the page does
    -- not carry (docs/DECISIONS.md section 15).
    block_id   integer NOT NULL CHECK (block_id >= 0),
    line_id    integer NOT NULL CHECK (line_id >= 0),
    ordinal    integer NOT NULL CHECK (ordinal >= 0),
    text       text NOT NULL,
    x0         numeric NOT NULL,
    y0         numeric NOT NULL,
    x1         numeric NOT NULL,
    y1         numeric NOT NULL,
    PRIMARY KEY (source_id, page, block_id, line_id, ordinal)
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

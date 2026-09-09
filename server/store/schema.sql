-- Applied in full at startup. There are no migrations: the schema is one file
-- and the store is created from it. That does not make drift impossible on its
-- own -- `CREATE TABLE IF NOT EXISTS` is a no-op on a table that already
-- exists, including one whose columns this file has since changed, so editing
-- a table here leaves a running store on the old shape with no error and no
-- warning. `apply_schema` compares the store against this file on every
-- restart and refuses to serve a mismatch (docs/DECISIONS.md 27).

CREATE TABLE IF NOT EXISTS cases (
    case_id     text PRIMARY KEY,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Who may act on a case, and with what standing (SYSTEM_SPEC 8). This is the
-- current membership, not its history: a grant is inserted or moved in place
-- and a revocation deletes the row. Who changed it, and when, is the audit
-- chain's to record (docs/REBUILD_PLAN.md Phase 6). Read under FOR SHARE by
-- the store call that releases a gate, so a revocation waits for a release in
-- flight instead of landing between its read and its commit.
CREATE TABLE IF NOT EXISTS case_members (
    case_id     text NOT NULL REFERENCES cases (case_id),
    member_id   text NOT NULL,
    standing    text NOT NULL
                CHECK (standing IN ('READER', 'WRITER', 'APPROVER', 'ADMIN')),
    granted_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, member_id)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id      uuid PRIMARY KEY,
    case_id     text NOT NULL REFERENCES cases (case_id),
    state       text NOT NULL CHECK (state IN ('RUNNING', 'COMPLETE', 'FAILED')),
    -- Every reservation counts against this, including the ones a crash left
    -- indeterminate (docs/DECISIONS.md section 21).
    ceiling     numeric(18, 6) NOT NULL DEFAULT 0 CHECK (ceiling >= 0),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- seq is per-run and monotonic, allocated under the run row lock. Append-only.
CREATE TABLE IF NOT EXISTS run_events (
    run_id  uuid NOT NULL REFERENCES runs (run_id),
    seq     integer NOT NULL CHECK (seq > 0),
    kind    text NOT NULL,
    -- Set on ROUTE_PINNED. SYSTEM_SPEC 4: the digest goes in run_events, so the
    -- stream itself says which route the run was pinned to.
    route_digest  char(64),
    at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, seq)
);

-- One accepted output per node per run. The digest is a column, not the key:
-- the blob store is what deduplicates bytes, and two runs of a deterministic
-- module legitimately produce the same digest while each keeps its own row.
CREATE TABLE IF NOT EXISTS artifacts (
    run_id      uuid NOT NULL REFERENCES runs (run_id),
    node_id     text NOT NULL,
    sha256      text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
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

-- One user-provided document admitted into a case. Withdrawal is a timestamp,
-- never a deletion: the pinned sets that name the source are immutable, and an
-- already-executed run was pinned to it. What a withdrawn source loses is every
-- use from then on -- read_evidence, pin_source_set and the plan gate each
-- check the column live (invariant 1) -- and the store refuses to take it back
-- (sources_withdrawal_is_final), so a refusal can always be explained later.
CREATE TABLE IF NOT EXISTS sources (
    source_id     uuid PRIMARY KEY,
    case_id       text NOT NULL REFERENCES cases (case_id),
    sha256        text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    created_at    timestamptz NOT NULL DEFAULT now(),
    withdrawn_at  timestamptz
);

-- One live admission per document per case. Partial, so a withdrawn source
-- keeps its row and its history while the same bytes come back as a new
-- source: withdrawal is final for the source, not for the document.
CREATE UNIQUE INDEX IF NOT EXISTS sources_admitted_once
    ON sources (case_id, sha256) WHERE withdrawn_at IS NULL;

-- The sources a run may use. Every read of a source goes through this view, so
-- the withdrawal predicate lives in one place rather than in every SELECT that
-- has to remember it -- four did, and the fifth forgot (docs/DECISIONS.md 45).
-- The owner writes `sources` directly, and the pin reads it once to count the
-- withdrawn and say so.
CREATE OR REPLACE VIEW live_sources AS
    SELECT source_id, case_id, sha256, created_at
      FROM sources
     WHERE withdrawn_at IS NULL;

-- The coordinate index behind invariant 11: one row per extracted text run with
-- its page and rectangle. Tokens are never returned to a module; they exist so
-- the host can re-locate a quote and refuse one it cannot. Keyed so that one
-- page is one index range -- never a whole-source scan.
CREATE TABLE IF NOT EXISTS source_tokens (
    source_id  uuid NOT NULL REFERENCES sources (source_id),
    page       integer NOT NULL CHECK (page > 0),
    -- Both assigned by the extractor. A region is a column or a paragraph --
    -- not CONTEXT.md's `block`, which is what read_evidence returns. A quote
    -- may wrap onto the next line of its own region and nowhere else, so two
    -- columns sharing a y-band cannot be joined into a phrase the page does not
    -- carry (docs/DECISIONS.md section 15).
    region_id   integer NOT NULL CHECK (region_id >= 0),
    line_id    integer NOT NULL CHECK (line_id >= 0),
    ordinal    integer NOT NULL CHECK (ordinal >= 0),
    text       text NOT NULL,
    x0         numeric NOT NULL,
    y0         numeric NOT NULL,
    x1         numeric NOT NULL,
    y1         numeric NOT NULL,
    PRIMARY KEY (source_id, page, region_id, line_id, ordinal)
);

-- The unit read_evidence returns: one row per block, keyed by
-- (source_id, block_id). Never a JSON column holding every block of a source --
-- that shape made one read parse the whole source, the predecessor's ~8x I/O
-- defect (docs/AI_CODE_QUALITY.md section 1).
CREATE TABLE IF NOT EXISTS source_blocks (
    source_id  uuid NOT NULL REFERENCES sources (source_id),
    block_id   integer NOT NULL CHECK (block_id >= 0),
    page       integer NOT NULL CHECK (page > 0),
    text       text NOT NULL,
    PRIMARY KEY (source_id, block_id)
);

-- An immutable, versioned set of sources a run is pinned to. Version allocation
-- locks the case row before reading the current version, so two pins cannot
-- read the same one.
CREATE TABLE IF NOT EXISTS source_sets (
    case_id     text NOT NULL REFERENCES cases (case_id),
    version     integer NOT NULL CHECK (version > 0),
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (case_id, version)
);

CREATE TABLE IF NOT EXISTS source_set_members (
    case_id    text NOT NULL,
    version    integer NOT NULL,
    source_id  uuid NOT NULL REFERENCES sources (source_id),
    PRIMARY KEY (case_id, version, source_id),
    FOREIGN KEY (case_id, version) REFERENCES source_sets (case_id, version)
);

-- What a node was actually handed. Invariant 9: a citation may only name
-- evidence delivered to that node, and this is the ledger that says so.
CREATE TABLE IF NOT EXISTS delivered_evidence (
    run_id       uuid NOT NULL REFERENCES runs (run_id),
    node_id      text NOT NULL,
    source_id    uuid NOT NULL REFERENCES sources (source_id),
    block_id     integer NOT NULL,
    delivered_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, node_id, source_id, block_id),
    FOREIGN KEY (source_id, block_id) REFERENCES source_blocks (source_id, block_id)
);

-- The route a run is pinned to. One row per run: a run pinned to one route
-- never executes under another (invariant 10). The resolved payload is stored
-- whole, so execution reads the pin rather than re-resolving from a catalog
-- that may have moved.
CREATE TABLE IF NOT EXISTS run_routes (
    run_id        uuid PRIMARY KEY REFERENCES runs (run_id),
    route_digest  char(64) NOT NULL,
    profile_id    text NOT NULL,
    selection_id  text NOT NULL,
    resolved      jsonb NOT NULL,
    -- The evidence the route runs over. The gate pins a plan -- a route and a
    -- source-set version together -- and the version otherwise survived only
    -- inside the gate's fingerprint, a digest nothing can read it back out of.
    source_set_version  integer NOT NULL CHECK (source_set_version > 0),
    pinned_at     timestamptz NOT NULL DEFAULT now()
);

-- One row per try, written and committed before the provider is called, so it
-- survives the crash it exists to account for. Append-only: an attempt is never
-- updated, so acceptance is the artifact row and an attempt without one is
-- indeterminate by construction (docs/DECISIONS.md section 21).
CREATE TABLE IF NOT EXISTS run_attempts (
    attempt_id     uuid PRIMARY KEY,
    run_id         uuid NOT NULL REFERENCES runs (run_id),
    route_node_id  text NOT NULL,
    reserved       numeric(18, 6) NOT NULL CHECK (reserved >= 0),
    started_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS run_attempts_by_run ON run_attempts (run_id);

-- A digest-bound interrupt: what a person is being asked to approve, named by
-- the bytes they are shown and by the inputs those bytes were rendered from.
-- Deliberately not append-only. While a gate is undecided the content under it
-- moves -- a source is withdrawn, a plan is re-derived -- and re-opening it on
-- the new content is the point. What must never move is a decision, and a
-- decision does not live here.
CREATE TABLE IF NOT EXISTS run_gates (
    run_id             uuid NOT NULL REFERENCES runs (run_id),
    kind               text NOT NULL
                       CHECK (kind IN ('SOURCE_SET', 'RESEARCH_PLAN')),
    preview_sha256     text NOT NULL CHECK (preview_sha256 ~ '^[0-9a-f]{64}$'),
    input_fingerprint  text NOT NULL CHECK (input_fingerprint ~ '^[0-9a-f]{64}$'),
    opened_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, kind)
);

-- The release, and the whole of invariant 5's evidence. The row is copied from
-- the gate rather than supplied, so what it records is what the store held --
-- never what a caller claimed. The primary key is the compare-and-set: one
-- release per gate, and a second one writes nothing rather than colliding.
CREATE TABLE IF NOT EXISTS run_gate_approvals (
    run_id             uuid NOT NULL,
    kind               text NOT NULL,
    preview_sha256     text NOT NULL,
    input_fingerprint  text NOT NULL,
    approved_by        text NOT NULL,
    approved_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, kind),
    FOREIGN KEY (run_id, kind) REFERENCES run_gates (run_id, kind)
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

-- Withdrawal is final. A withdrawn source that a raw UPDATE could reinstate is
-- a source whose refusals nobody can explain afterwards; re-admitting is a new
-- source. Only the reversal is refused -- the column moving from set to unset,
-- or to another moment -- so `withdraw_source`'s own write is untouched.
CREATE OR REPLACE FUNCTION refuse_reinstatement() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'WITHDRAWAL_IS_FINAL';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER sources_withdrawal_is_final
    BEFORE UPDATE OF withdrawn_at ON sources
    FOR EACH ROW
    WHEN (OLD.withdrawn_at IS NOT NULL
          AND NEW.withdrawn_at IS DISTINCT FROM OLD.withdrawn_at)
    EXECUTE FUNCTION refuse_reinstatement();

-- A pinned source set is what a run's evidence means. Editing one would change
-- what an already-executed run was pinned to.
CREATE OR REPLACE TRIGGER source_sets_append_only
    BEFORE UPDATE OR DELETE ON source_sets
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER run_attempts_append_only
    BEFORE UPDATE OR DELETE ON run_attempts
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER delivered_evidence_append_only
    BEFORE UPDATE OR DELETE ON delivered_evidence
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER source_set_members_append_only
    BEFORE UPDATE OR DELETE ON source_set_members
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

-- An approval that can be rewritten is not an approval. `run_gates` carries no
-- such trigger on purpose: it needs the UPDATE path the re-open uses, and what
-- refuses truncating it is this table's foreign key and this table's own guard.
CREATE OR REPLACE TRIGGER run_gate_approvals_append_only
    BEFORE UPDATE OR DELETE ON run_gate_approvals
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

-- TRUNCATE empties a table without producing a row, so a row-level trigger
-- never fires on it. Statement-level is the only guard that sees the one
-- statement that erases a whole ledger at once.
CREATE OR REPLACE TRIGGER run_events_no_truncate
    BEFORE TRUNCATE ON run_events
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER source_sets_no_truncate
    BEFORE TRUNCATE ON source_sets
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER source_set_members_no_truncate
    BEFORE TRUNCATE ON source_set_members
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER delivered_evidence_no_truncate
    BEFORE TRUNCATE ON delivered_evidence
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER run_attempts_no_truncate
    BEFORE TRUNCATE ON run_attempts
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER run_gate_approvals_no_truncate
    BEFORE TRUNCATE ON run_gate_approvals
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

-- A run pinned to one route never executes under another (invariant 10). A
-- pin a raw statement could move or drop is not a pin, and a replay reads the
-- row back to say whether it stands -- which needs the row to be there.
CREATE OR REPLACE TRIGGER run_routes_append_only
    BEFORE UPDATE OR DELETE ON run_routes
    FOR EACH ROW EXECUTE FUNCTION refuse_rewrite();

CREATE OR REPLACE TRIGGER run_routes_no_truncate
    BEFORE TRUNCATE ON run_routes
    FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite();

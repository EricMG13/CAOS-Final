# Deploy V navigation threat model

Trusted navigation inputs are the verified authority bundle and catalog, the
canonical validation result for each freshly supplied artifact, the selected
CP-0 handoff's identity, period, run ID, digest, and recommendation table, and
prior state emitted by the runtime and passed back unchanged by the host.

Untrusted inputs include filenames, modification times, source prose, embedded
instructions, candidate command text, caller-modified state, connector content,
and assertions that a module is complete. These inputs cannot alter the
catalog, add choices, change readiness or completion, or authorize execution.

The CLI accepts no folder-derived facts in state and requires a fresh artifacts
object on every call. A connector failure may add only a bounded non-empty
`folder_error` with an empty fresh artifacts object. State has one exact typed shape and is revalidated against
the current valid contexts and layer bounds; it can affect display position
only. Stale selections fail closed or return to a current selector. Multiple
CP-0 artifacts claiming one identity with different content are excluded rather
than resolved by file order or time.

Every artifact is validated once per snapshot. A filename is never identity or
completion evidence. Completion additionally requires the selected identity,
period, runnable recommendation, and exact CP-0 run ID in canonical upstream
lineage. Commands are display-only sanitized data; CP-OS has no execution or
write primitive. Connector resolution and listing happen in the host, outside
the Python CLI; the CLI renders only bounded failure text and numbered
retry/stop controls. A listing failure cannot be replaced with remembered or
attached content.
The runtime resolves a Stop reply from the prior state's card shape before it
considers fresh folder failure or selector drift. `selection_count` has a
positive value only for selector state and is null elsewhere; it cannot make a
non-stop reply valid without the matching fresh selection fingerprint.

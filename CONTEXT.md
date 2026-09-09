# CONTEXT.md — vocabulary

One term per concept. A synonym is a defect: two spellings of one thing mint two
lineages and defeat comparison. `scripts/check_vocabulary.py` fails a PR that
introduces a synonym for a term below.

## Domain

| Term | Means | Not |
|---|---|---|
| **case** | one issuer engagement, the unit of membership and audit | deal, project, file |
| **source** | one user-provided document admitted into a case | file, upload, attachment |
| **source set** | an immutable, versioned set of sources a run is pinned to | corpus, pack |
| **block** | the unit `read_evidence` returns from a source | chunk, fragment, passage |
| **citation** | `{document_sha256, page, bboxes, matched_text}` | reference, footnote |
| **module** | one CP-* unit of methodology, one node in a route | agent, step, task |
| **route** | the resolved, pinned node set and typed edges for a run | graph, pipeline, workflow |
| **frontier** | the nodes currently RUNNABLE or RESTRICTED | queue, ready set |
| **artifact** | one module's accepted, content-addressed output | result, response |
| **snapshot** | the accepted artifact set that a case's conclusion rests on | version, state |
| **build** | one release of the methodology bundle, named by its manifest's `build_id`; a run is pinned to one | version |
| **revision** | an immutable analyst edit on the deliverable | draft, version |
| **deliverable** | the document the host renders from a frozen snapshot | report, output, export |
| **opinion** | the analyst's signature on an exact revision | approval, sign-off of the deliverable |
| **filing** | the independent approval that makes a deliverable final | publication, release |

## Node states — the bundle's words, unchanged

`COMPLETE` · `RUNNABLE` · `RESTRICTED` · `BLOCKED`. A `RESTRICTED` node runs and
carries its limitation forward. It is not "degraded", "partial" or "warning".

## Edge types — the bundle's words, unchanged

`REQUIRED` · `CONDITIONAL` · `QA_GATE` block. `OPTIONAL` · `ADVISORY` are soft —
until the source's readiness is `READY` or `READY_WITH_LIMITATIONS`, at which
point they block.

## Avoid

*Dashboard* (we build workspaces), *AI-powered* (say what it does), *seamless*,
*leverage* as a verb, *insight* as a countable noun, *user* where *analyst*,
*PM* or *approver* is meant.

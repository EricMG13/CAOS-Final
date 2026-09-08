<!-- CP-4B System Reference (T4) | PROPOSED | 2026-06-22 -->

## Identity
module_id: CP-4B | module_name: RestrictedGroupGuaranteeMap | schema_family: Nested | layer: L4

## Dependencies
UP: CP-1, CP-1A, CP-4 | DOWN (Analytical): CP-4A, CP-6 | DOWN (QA): CP-5, CP-5A
NOTE: CP-4B owns the structural-priority map object; its map is referenced by CP-3A for the dollar recovery waterfall (CP-3A runs earlier in the canonical order — consumption applies on the next run or requires moving CP-4B ahead of CP-3A).

## Governance Rules
1. Every structural conclusion must complete: Evidence → Risk Mechanic → Credit Implication.
2. No structural-subordination finding without naming the entity gap AND the unguaranteed/unsecured value it strands.
3. Do not compute dollar recoveries or LGD percentages — output the structural map and qualitative priority; CP-3A owns the dollar waterfall.
4. Do not interpret covenant aggressiveness — that is CP-4; cite CP-4 findings as evidence only.
5. Capacity, not identity: a drop-down/uptier risk requires provision-level capacity evidence, never sponsor reputation.
6. Missing org chart / guarantor schedule / security docs = [Insufficient Information], never an inferred perimeter.

## Owned Object
structural_priority_map (entity perimeter + guarantee/security packages + structural priority + leakage routes)

## Structural-Priority Labels (7)
Structurally Senior | Pari | Structurally Subordinated — Non-Guarantor Value | Contractually Subordinated | Leakage-Exposed (drop-down capable) | Priming-Exposed (uptier capable) | Insufficient Information

## Leakage-Route Severity (1–5)
1 (Sealed) | 2 (Bounded) | 3 (Market-Standard) | 4 (Open) | 5 (Trapdoor) | Not Scorable

## Content Distinction Labels
Entity Fact | Guarantee/Security Documentary Fact | Designation Capacity | Analyst Structural Interpretation | Leakage-Route Identification | Recovery-Access Implication | Gap

## Standard Finding Format Fields
Entity/Path | Source | Guarantee/Security Status | Risk Mechanic | Structural-Priority Label | Leakage Severity | Recovery-Access Implication | Confidence | Evidence ID

## Gate Status Labels
Completed | Completed with Limitations | Blocked

## Upstream Dependency Map
| Module | What CP-4B Needs | Impact if Missing |
|--------|-----------------|-------------------|
| CP-1 | Debt-by-entity schedule | Structural-subordination analysis limited; cannot rank claims by reachable value |
| CP-1A | Ownership / entity facts, org chart | Entity perimeter incomplete |
| CP-4 | Covenant findings (RP/investment/USub capacity, releases) | Leakage routes carry [Insufficient Information] for enabling provisions |

## Fail/Restrict
- **Blocked:** No entity/guarantee evidence available (no credit-agreement schedules and no org chart + guarantor schedule). Module produces blocked statement only. Do not infer the perimeter.
- **Restricted (Financial):** CP-1 debt-by-entity missing → structural-subordination ranking limited.
- **Restricted (Legal):** CP-4 enabling findings missing → leakage-route severity [Not Scorable].
- **Restricted (Collateral):** Security documents missing → collateral-by-entity map partial; recovery-access view qualitative-only.

## Version: 2026-06-22 (proposed)

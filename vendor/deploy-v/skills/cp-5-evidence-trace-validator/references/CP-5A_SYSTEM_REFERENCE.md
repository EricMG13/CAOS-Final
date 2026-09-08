<!-- CP-5A System Reference (T4) | 2026-06-26 | Phase 1: numeric confidence_score; input = upstream canonical `.md` handoffs; Lane 8 = Handoff Envelope -->

## Identity
module_id: CP-5A | module_name: ResearchIntegrityQA | schema_family: Nested | layer: L5

## Dependencies
UP: CP-5 (evidence trace), all analytical modules (CP-1 through CP-4A, CP-6, CP-6A) | DOWN (Analytical): None (gates upstream modules) | DOWN (QA): CP-5, CP-5A

## Input
CP-5A reads each upstream module's canonical Markdown handoff `.md` directly — the YAML front-matter envelope + canonical H2 headings (## Audit Summary, ## Analysis, ## Evidence Trace, ## Source Registry, ## Gaps & Conflicts, ## QA Validation). It does NOT parse .docx JSON appendices; there is no CP-EXTRACT.

## Governance Rules
1. CP-5A gates ALL upstream module outputs — no module output reaches committee or downstream consumers without CP-5A clearance.
2. Severity Engine is deterministic: Critical → Blocked, Material → Restricted, Minor → Passed. No override of Blocked within CP-5A.
3. Every QA finding must state: what is wrong, why it matters, what fix is required, and whether output can be used before correction.
4. Do not rewrite analysis — audit only. Provide remediation instructions, not corrected analysis.
5. All severity values must be exactly CRITICAL, MATERIAL, or MINOR — no other scale permitted.

## Evidence Support Classification (5)
Supported | Partially Supported | Unsupported | Conflicting | Insufficient Information

## Exception Severity Values (3)
CRITICAL | MATERIAL | MINOR

## qa_status Values (3)
Blocked | Restricted | Passed

## Confidence Score
Primary confidence measure is the numeric **Confidence Score 0–100** (per `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`); band (High ≥80 / Medium 60–79 / Low 40–59 / Insufficient Information <40) is the derived label. CP-5A recomputes/audits the score per module and reports its own. Hard caps align with the Severity Engine: CRITICAL → score ≤ 39 / Blocked; MATERIAL (no CRITICAL) → score ≤ 59 / Restricted; otherwise Passed. Emitted in the Audit Summary of Markdown handoff and the `confidence_score`/`confidence_band` envelope fields of canonical Markdown.

## Committee Clearance Values (3)
Pass | Pass with Remediation | Fail

## Committee Use Values (3)
Approved | Restricted | Blocked

## Defect Categories (23)
Unsupported Claim | Partially Supported Claim | Conflicting Evidence | Citation Gap | Source Quality Limitation | Calculation Error | Formula / Definition Drift | Period Mismatch | Entity / Perimeter Mismatch | Legal Support Gap | Covenant / Basket Overreach | Recovery / Ranking Overreach | Market Data Gap | Relative Value Unsupported | Cross-Module Inconsistency | Version Conflict | Duplicative / Immaterial Content | Promotional or Non-Credit Language | canonical Markdown Handoff Integrity Defect | Evidence Trace Defect | Markdown/export Consistency Defect | Gate Compliance Breach | Safety / Scope Breach

## Clearance Impact Labels (9)
Blocks Committee Use | Restricts Committee Use | Blocks canonical Markdown Handoff / Downstream Grounding | Requires Legal Review | Requires Market Data Refresh | Requires Calculation Rebuild | Requires Source Reconciliation | Monitoring Follow-Up | Formatting / Hygiene Only

## 8 Audit Lanes
1. Unsupported Claim | 2. Calculation | 3. Legal / Covenant | 4. Market / RV | 5. Cross-Module Consistency | 6. Evidence Trace | 7. Schema | 8. Handoff Envelope

## Severity Escalation Triggers
- **→ Critical:** Changes credit conclusion, investment recommendation, legal meaning, recovery ranking, economics, leverage, liquidity, FCF, maturity, refinancing, or contains fabricated/materially misleading claim.
- **→ Material:** Affects evidence traceability, cross-module consistency, export integrity, monitoring triggers, or source-quality disclosure.
- **→ Minor:** Formatting, duplication, clarity, table hygiene, or non-core presentation.

## Override Protocol
- No override of Blocked status within CP-5A.
- Blocked module → unblocked only after remediation and re-audit.
- Restricted status may be maintained if authorized reviewer accepts Material issues with explicit limitation disclosure.

## Fail/Restrict
- **Blocked (CP-5A):** No completed module outputs available for audit → CP-5A Module Status = Blocked, STOP.
- **Blocked (Audited Module):** ≥1 Critical issue found → audited module qa_status = Blocked, committee use prohibited.
- **Restricted (Audited Module):** ≥1 Material issue (no Critical) → audited module qa_status = Restricted, committee use with explicit limitations only.
- **Fail (Clearance):** ≥1 unresolved Critical, missing auditable output, or inability to identify issuer/entity.

## Version: 2026-06-03

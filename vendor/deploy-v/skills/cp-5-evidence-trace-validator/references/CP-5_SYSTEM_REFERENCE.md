<!-- CP-5 System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-5 | module_name: EvidenceTraceValidator | schema_family: Nested | layer: L5

## Dependencies
UP: All analytical modules (CP-1 through CP-4A, CP-6, CP-6A), CP-5A QA output | DOWN (Analytical): CP-5A | DOWN (QA): CP-5, CP-5A

## Governance Rules
1. CP-5 is a governance layer only — it does not alter substantive credit conclusions from upstream modules.
2. Default traceability scope is Top 5 most material credit drivers; Full scope requires explicit user request.
3. Every material conclusion must be classified using exactly the 8-value Lineage Taxonomy — no other classification labels permitted.
4. Orphan claims (VE-015) must be flagged when lineage_class is Untraced/Weak Lineage/Insufficient Information AND conclusion is committee-facing AND no mitigation flag applied.
5. No silent citation repair — missing or malformed citations are flagged, never fabricated or repaired.

## Evidence Hierarchy (8 values, highest → lowest)
1. Directly Sourced
2. Calculated
3. Assumption-Based
4. Analyst Inference
5. Weak Lineage
6. Untraced
7. Conflicting
8. Insufficient Information

## Lineage Taxonomy (8 canonical values)
Directly Sourced | Calculated | Assumption-Based | Analyst Inference | Weak Lineage | Untraced | Conflicting | Insufficient Information

## Auditability Assessment Values (4)
Committee-Ready | Ready with Remediation | Not Committee-Ready | Blocked

## Module Status Values (3)
Full Run | Ready with Limitations | Blocked

## Traceability Scope Values (2)
Top 5 | Full

## Traceability Status Values (3)
Committee-Ready | Remediation Needed | Not Traceable

## Severity Values (3)
Critical | Material | Minor

## Source Lineage Type Values (7)
Sourced | Calculated | Assumption | Inference | Weak Lineage | Untraced | Conflicting

## Gap Confidence Impact Values (3)
High | Medium | Low

## Orphan Claim Trigger
Code: VE-015 (ORPHAN_CLAIM)
Condition: lineage_class ∈ {Untraced, Weak Lineage, Insufficient Information} AND committee-facing AND no mitigation/limitation_flag

## Severity Escalation Triggers
- **→ Critical:** Affects economics, legal meaning, recommendation, security selection, position sizing, committee decision, PD, LGD, recovery, refinancing, or relative value.
- **→ Material:** Affects monitoring, confidence, source quality, or Markdown/export artifact integrity.
- **→ Minor:** Formatting, metadata, or non-decision-critical citation issue.

## Fail/Restrict
- **Blocked (CP-5):** No substantive module outputs or CP-5A QA output available → Module Status = Blocked, STOP.
- **Not Committee-Ready:** Any auditability dimension assessed as Not Committee-Ready → overall output Not Committee-Ready.
- **Ready with Remediation:** One or more dimensions require remediation but no blocking condition exists.
- **Committee-Ready:** All 5 auditability dimensions pass.

## Version: 2026-06-03

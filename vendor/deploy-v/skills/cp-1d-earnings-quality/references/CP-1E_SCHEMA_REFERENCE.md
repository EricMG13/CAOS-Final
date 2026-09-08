# CP-1E — Schema Reference

Governed output sections, register columns and the QA checklist for CP-1E
AdjustedDebt.

## Canonical sections
`## Audit Summary` · `## Analysis` · `## Evidence Trace` · `## Source Registry` ·
`## Gaps & Conflicts` · `## QA Validation`

## Registers

| ID | Columns |
|---|---|
| T1E.1 | Item; Category; Reported Amount; Period; Source / Locator; Disclosure Quality; Evidence ID |
| T1E.2 | Item; Debt-Like? ; Basis for Treatment; Adjustment Amount; Convention Applied; Countervailing Evidence; Evidence ID |
| T1E.3 | Step; Amount; Basis; Cumulative Adjusted Debt; Evidence ID |
| T1E.4 | Metric; On Reported Debt; On Adjusted Debt; Delta (turns); Risk Mechanic; Credit Implication; Evidence ID |
| T1E.5 | Item; Agency / Convention; Their Treatment; This Analysis; Divergence Rationale; Evidence ID |
| T1E.6 | Gap; Missing Data; Why It Matters; Impact on Output; Required Follow-Up |

## QA checklist
- [ ] Every obligation class in the taxonomy considered and either quantified or logged as a gap
- [ ] Debt-like treatment cites the disclosure, not a default convention
- [ ] Operating-lease treatment names the accounting standard and avoids double counting
- [ ] T1E.3 cumulative column reconciles step by step
- [ ] Leverage restated on both bases in T1E.4
- [ ] Divergence from agency convention reasoned in T1E.5
- [ ] Adjusted debt never presented as reported or covenant debt
- [ ] Numeric Confidence Score (0-100) + band per `CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`
- [ ] Null never converted to zero

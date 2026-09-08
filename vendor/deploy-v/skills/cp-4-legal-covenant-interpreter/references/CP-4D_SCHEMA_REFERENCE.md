# CP-4D — Schema Reference

Governed output sections, register columns and the QA checklist for CP-4D
Intercreditor.

## Canonical sections
`## Audit Summary` · `## Analysis` · `## Evidence Trace` · `## Source Registry` ·
`## Gaps & Conflicts` · `## QA Validation`

## Registers

| ID | Columns |
|---|---|
| T4F.1 | Document; Parties; Date; Governing Law; Status; Source / Locator; Evidence ID |
| T4F.2 | Creditor Class; Rank; Security Interest; Enforcement Rights; Voting Weight; Evidence ID |
| T4F.3 | Provision; Standstill Period; Trigger; Who Controls Enforcement; Creditor Class Affected; Risk Mechanic; Credit Implication; Evidence ID |
| T4F.4 | Provision; Turnover Obligation; Release Authority; Purchase Option; Conditions; Countervailing Evidence; Evidence ID |
| T4F.5 | Creditor Class; Realised-Recovery Mechanic; Control Weakness; Severity; Risk Mechanic; Credit Implication; Evidence ID |
| T4F.6 | Gap; Missing Data; Why It Matters; Impact on Output; Required Follow-Up |

## QA checklist
- [ ] Every provision cited to an executed document with a clause locator
- [ ] Contractual, structural and lien subordination distinguished
- [ ] Standstill periods stated as drafted, with trigger and expiry
- [ ] No recovery percentage asserted — mechanics handed to CP-3A / CP-4C
- [ ] Absent ICA stated plainly with dependent rows marked Insufficient Information
- [ ] Numeric Confidence Score (0-100) + band per `CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`
- [ ] Null never converted to zero

<!-- CP-1B System Reference (T4) | 2026-06-02 -->
## Identity
module_id: CP-1B | module_name: EarningsDelta | schema_family: Nested | layer: L1

## Dependencies
UP: CP-1 | DOWN (Analytical): CP-2, CP-2A, CP-MODEL | DOWN (QA): CP-5, CP-5A

## CP-MODEL interface
Binding keyed comparator, account-validation, issuer-specific add-back
validation and readiness records are defined in
`REF_CP-1B_14_ModelWorkbookValidation.md`. CP-1B never overrides CP-1 numeric
ownership or replaces add-back IDs/labels. CP-MODEL is a canonical-only
workbook extension.

## Metric Governance
ALL inherited from CP-1. EBITDA priority: Credit-agreement > CP-1 canonical > Adjusted > Reported. Def switching prohibited w/o Conflict Log. FCF: CP-1 canonical. 8 calc status values.

## Evidence Hierarchy
Audited FS > Unaudited w/auditor > Unaudited > Lender/Sponsor > Rating > Internal > External

## Fail/Restrict
Unsupported claim | Missing trace | Undocumented calc | Def switch w/o log | Null→zero | QA-blocked upstream | Currency switch

## Version: 2026-06-02

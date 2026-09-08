<!-- CP-2 System Reference (T4) | 2026-06-03 -->

## Identity
module_id: CP-2 | module_name: FundamentalCreditSynthesizer | schema_family: Nested | layer: L2

## Dependencies
UP: CP-1, CP-1A, CP-1B, CP-1C | DOWN (Analytical): CP-2A, CP-2B, CP-2C, CP-2D, CP-2E, CP-3, CP-6 | DOWN (QA): CP-5, CP-5A

## Metric Governance
1. Every material qualitative conclusion must follow [Evidence] → [Risk Mechanic] → [Credit Implication].
2. Content must be distinguished: Source Fact | Calculation | Analyst Interpretation | Credit Implication | Gap.
3. Financial Profile Assessment uses exactly 4 values: Strong / Average / Weak / Not Assessable.
4. Canonical Credit Implication taxonomy has exactly 13 values (see Schema Reference).
5. CP-2 does not perform legal/covenant analysis, recovery waterfall, RV recommendation, position-sizing, equity valuation, or legal advice — hand off to downstream.

## Evidence Hierarchy
1. Uploaded files / primary source documents (highest)
2. CP-0 registry
3. CP-1 data foundation / CP-1A / CP-1B / CP-1C outputs
4. Issuer financials, lender presentations, offering memoranda
5. Rating reports, earnings transcripts
6. Company sources, legal/covenant extracts
7. Internal notes
8. External news (lowest — must label [External])

## Enumerated Label Sets
- **Financial Profile Assessment:** Strong | Average | Weak | Not Assessable
- **Materiality Direction:** Positive | Negative | Mixed
- **Materiality Confidence:** High | Medium | Low | Not Assessable
- **Module Status:** Full Run | Ready with Limitations | Blocked
- **Credit Implication (13):** See Schema Reference

## Fail/Restrict
- If gating sources unavailable → Blocked status, stop after identifying missing evidence.
- If required source unavailable → mark section [Insufficient Information] and log gap.
- If sources conflict → log conflict, do not reconcile silently.

## Version: 2026-06-03

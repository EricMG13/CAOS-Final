<!-- CP-3 System Reference (T4) | 2026-06-03 -->

Loan analysis always resolves and uses the maintained enterprise Sector RV workbook and assumes it is current and relevant. REF_CP-3_Sector_RV.xlsx is an intentionally empty deployment placeholder, not market evidence. Apply the maintained-source protocol in SKILL.md: no freshness/relevance confirmation; preserve stated dates or record `Current — maintained Sector RV source` when no quote date is supplied. This basis satisfies the market-date checks below.

## Identity
module_id: CP-3 | module_name: RelativeValueSecuritySelection | schema_family: Nested | layer: L3

## Dependencies
Required upstream: CP-0, CP-1, CP-2 | Optional upstream: CP-1A, CP-1C, CP-2G, CP-2H | Internal phases: CP-3A, CP-3B | Downstream: CP-6 (including CP-6A), CP-5 (including CP-5A).

## Governance Rules
1. CP-3 is not standalone fundamental underwriting — it relies on CP-1/CP-2 family outputs and converts them into security-selection and RV conclusions.
2. RV conclusions require current market evidence under CP-3's maintained-source policy. Without usable market values, RV = Unclear and recommendation ≠ Preferred.
3. Scores are decision-support tools, not ratings. Missing factor evidence → range, Not Scorable, or Not Assessable.
4. A security may be Preferred only when fundamentals, structure, downside protection, liquidity, refinancing, and market compensation are collectively supportive.
5. Every material conclusion must complete: Evidence → Risk Mechanic → Credit Implication.

## Evidence Hierarchy
Sourced Fact > Calculated Metric > Analyst Inference > Insufficient Information > Unsupported Conclusion

## Execution Modes
CLO Screening | Single-Name RV | Capital-Structure RV | Watchlist Monitoring

## Score Direction
1 (Conservative/creditor-favorable/low-risk) → 5 (Aggressive/creditor-unfavorable/high-risk)

## Score Confidence Tags
High | Medium | Low | Not Assessable

## Credit Tier Mapping
1.0–1.9 = High Quality | 2.0–2.9 = Acceptable | 3.0–3.7 = Stretched | 3.8–5.0 = Weak | Not Scorable

## Relative-Value Labels
Cheap | Fair | Rich | Unclear

## Recommendation Labels
Preferred | Neutral | Avoid | Requires More Work

## Fail/Restrict
- **Blocked:** Module Status = Blocked when no CP-1/CP-2 or equivalent fundamental evidence is available.
- **Restricted:** Module Status = Ready with Limitations when partial evidence available (e.g., no market data → all RV = Unclear, no legal data → structural/recovery views flagged).
- **Scoring Restricted:** No precise composite score if factor evidence materially incomplete.
- **RV Restricted:** RV = Unclear when usable market values are absent; recommendation cannot be Preferred without market evidence.
- **Ranking Restricted:** Avoid forced ranking when evidence insufficient — use Requires More Work.

## Version: 2026-06-03

# CP-2H Rating Transition schema

## Required analysis tables

| ID | Table | Required fields |
|---|---|---|
| T2R.1 | Rating evidence register | agency, issuer/instrument, rating, outlook/watch, effective date, source, locator, status |
| T2R.2 | Applicable methodology map | agency, criteria, publication/effective date, applicable entity/instrument, limitation |
| T2R.3 | Agency metric bridge | agency metric, CP metric, adjustments, period/perimeter, formula, evidence_id |
| T2R.4 | Quantitative trigger matrix | agency, rating type, trigger direction, metric, threshold, case/period value, headroom, status |
| T2R.5 | Qualitative modifier matrix | agency, factor, current evidence, supportive/neutral/negative/unknown, rationale, locator |
| T2R.6 | Migration case matrix | agency, case, transition class, earliest timing, catalyst, confidence, evidence/forecast IDs |
| T2R.7 | Agency divergence register | issue, agency A/B positions, methodology/perimeter/timing explanation, unresolved conflict |
| T2R.8 | Instrument and recovery-rating implications | instrument, issuer rating link, notching/recovery evidence, possible direction, limitation |
| T2R.9 | Monitoring and handoff | nearest trigger, buffer, leading indicator, review date/event, downstream module |
| T2R.10 | Gaps and conflicts | missing/stale item, affected agency/trigger, impact, required follow-up |

## Canonical transition classes

`supportive | within_current_range | negative_pressure | trigger_breach | insufficient_information`

These are RBOT analytical classes, not agency rating actions. Do not translate them mechanically into notches.

## Completion gate

`Complete` requires current rating evidence, applicable methodology, a metric bridge and at least one quantified or explicitly qualitative trigger assessment. Methodology-only analysis is `Complete with Gaps`. Identity conflict, falsely attributed rating evidence or absent evidence for the requested agency-specific conclusion is `Blocked`.


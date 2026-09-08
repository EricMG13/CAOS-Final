# CP-4C Restructuring Scenario schema

## Required analysis tables

| ID | Table | Required fields |
|---|---|---|
| T4E.1 | Distress and jurisdiction gate | trigger, evidence/date, affected entity/instrument, jurisdiction, status, limitation |
| T4E.2 | Claims register | class/claim ID, obligor, principal/accrued/PIK, currency, security/guarantee, priority, disputed/contingent, evidence |
| T4E.3 | Enterprise-value assumptions | scenario, valuation date, metric/cash flow, multiple/discount, EV, source/judgment IDs, limitation |
| T4E.4 | Restructuring path matrix | path, process/jurisdiction, consent/vote, new money, class treatment, milestones, blockers, probability class |
| T4E.5 | Priority and waterfall | scenario, entity, available value, priority claim, allocation, residual, legal evidence ID |
| T4E.6 | Fulcrum range | scenario/EV range, last covered class, first impaired class, fulcrum class/range, uncertainty |
| T4E.7 | Recovery by class | scenario, class/instrument, allowed claim, cash/debt/equity/warrant value, total recovery, timing, currency |
| T4E.8 | Value-transfer and intercreditor risks | mechanism, affected classes, required capacity/consent, evidence, possible outcome |
| T4E.9 | Catalysts, timeline and handoff | event/milestone, earliest/latest timing, evidence, consequence, downstream module |
| T4E.10 | Gaps and conflicts | claim/legal/value/process gap, affected scenario/class, impact, required evidence |

## Canonical status and probability classes

Run status: `Complete | Complete with Gaps | Not Applicable | Blocked`.

Path likelihood: `credible_primary | credible_alternative | contingent | remote | insufficient_information`. These are analytical classes, not legal predictions or numeric probabilities.

## Completion gate

`Complete` requires a passed distress gate, reconciled claims register, at least two credible/contingent paths where alternatives exist, valuation range, priority waterfall and class recoveries. Material legal/claims gaps yield `Complete with Gaps` or `Blocked`. No evidence of distress yields `Not Applicable`.


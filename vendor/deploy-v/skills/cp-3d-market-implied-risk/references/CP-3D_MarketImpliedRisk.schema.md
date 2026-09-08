# CP-3D Market-Implied Risk schema

## Required analysis tables

| ID | Table | Required fields |
|---|---|---|
| T3E.1 | Instrument and market source register | security_id, issuer, currency, coupon, maturity/call, seniority, source, timestamp, quote_type, freshness |
| T3E.2 | Market snapshot | security_id, bid/mid/ask or evaluated price, yield, spread/OAS/DM, duration, benchmark, observation ID |
| T3E.3 | Issuer curve | security_id, maturity/call date, spread/yield, seniority, curve residual, explanation status |
| T3E.4 | Peer/index context | comparator, alignment basis, spread/yield/price, period, difference, comparability limitation |
| T3E.5 | Implied risk calculations | security_id, model, horizon, recovery, discount/benchmark, implied default/loss/break-even, formula ID, limitation |
| T3E.6 | Liquidity and technicals | security_id, bid-ask, trade frequency/volume, issue size, ownership/flow/supply evidence, direction, confidence |
| T3E.7 | Fundamental-versus-market map | market implication, CP-2/2H/2R evidence, aligned/divergent, possible basis, unresolved question |
| T3E.8 | Scenario repricing | scenario, driver, spread/yield/price assumption, calculated move, convexity/call limitation |
| T3E.9 | Monitoring and handoff | observable, threshold, cadence/event, downstream module, evidence source |
| T3E.10 | Gaps and conflicts | missing/stale/conflicting item, affected calculation/security, impact, required evidence |

## Calculation controls

Vendor values and RBOT calculations occupy separate columns. Price/yield/spread conversions identify settlement date and convention. Callable instruments must not be treated as bullet maturities when the call assumption is material. Implied default or loss is a model-dependent break-even, not a factual probability.

## Completion gate

`Complete` requires verified instrument identity, timestamped market evidence, locked conventions and at least one market-versus-fundamental comparison. Stale or partial evidence yields `Complete with Gaps`. Missing required market capability, identity conflict or unresolvable convention mismatch is `Blocked`.


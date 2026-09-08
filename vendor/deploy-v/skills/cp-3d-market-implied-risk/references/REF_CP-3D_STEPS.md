Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-3D_A_MarketEvidenceGate.md, REF_CP-3D_B_BenchmarkAndCalculationLock.md, REF_CP-3D_C_MarketImpliedEngine.md, REF_CP-3D_D_LiquidityTechnicalsAndDislocation.md, REF_CP-3D_E_CreditHandoff.md, REF_CP-3D_F_OutputAndQA.md

## REF_CP-3D_A_MarketEvidenceGate.md
# CP-3D A — Market evidence gate

Verify each instrument using a reliable identifier and source-supported coupon, maturity/call, currency, issuer/guarantor and seniority. Do not map a quote to an instrument by abbreviated name alone. Record the market source, entitlement/usage limitation, observation timestamp, quote type (`bid`, `ask`, `mid`, `evaluated`, `last_trade`) and whether the market was open.

Define freshness appropriate to the instrument and question. A liquid bond's stale evaluated price and an illiquid distressed bond's last trade require different caveats. If a requested price/spread cannot be observed, mark `[Insufficient Information]`; do not search model memory for a plausible value.

## REF_CP-3D_B_BenchmarkAndCalculationLock.md
# CP-3D B — Benchmark and calculation lock

Lock settlement date, day count, compounding, clean/dirty price, accrued interest, yield-to-maturity/worst/call, benchmark curve, OAS/z-spread/discount-margin convention, duration and FX basis. For loans, identify floor and assumed forward/base rate. For callable bonds, state the call path used.

Keep source-reported and RBOT-calculated measures separate. A spread from one vendor is not directly comparable with another until methodology is aligned. Never use an index or peer comparison without matching currency, seniority, duration/maturity and observation time or stating the misalignment.

## REF_CP-3D_C_MarketImpliedEngine.md
# CP-3D C — Market-implied engine

Construct the issuer curve by seniority and currency before interpreting outliers. Compare each instrument with aligned issuer points, peers and index cohorts. Explain whether a residual may reflect call structure, liquidity, subordination, event risk, covenant/LME risk or data quality.

Break-even default/loss calculations must disclose recovery, horizon, discounting, timing and whether default is one-period or cumulative. Do not present implied results as objective default probabilities. Where inputs are insufficient, show sensitivity ranges rather than a point estimate.

When decomposing spread, label observable rate/benchmark effects separately from modelled credit, liquidity, optionality and technical components. The unexplained residual remains visible.

## REF_CP-3D_D_LiquidityTechnicalsAndDislocation.md
# CP-3D D — Liquidity, technicals and dislocation

Use observable evidence for liquidity: bid/ask, quote depth, trade frequency/volume, issue size, days without trades, evaluated-versus-executable gaps and price dispersion. Do not equate large issue size with liquidity without evidence.

Ownership, fund flows, ETF/CLO eligibility, dealer positioning, short interest, new-issue supply and index changes are included only when sourced and dated. Generic market commentary is not issuer-specific evidence.

Compare the market-implied map with CP-2 fundamental risk, CP-2G cases and CP-2H trigger headroom. Classify `aligned`, `market_more_adverse`, `market_less_adverse`, or `not_comparable`. A divergence is a research question, not automatically an opportunity.

## REF_CP-3D_E_CreditHandoff.md
# CP-3D E — Credit handoff

State which risks appear priced, the most material curve or peer residual, implied break-even assumptions, observable liquidity constraint, freshness limit and the evidence that would close the fundamental-versus-market gap.

CP-3 consumes the map and retains security-selection ownership. CP-3A consumes structural/recovery pricing differences. CP-3B consumes executable-liquidity evidence. CP-6 receives the strongest market challenge to the fundamental thesis.

CP-3D never emits buy/sell/hold, rich/cheap as a terminal recommendation, instrument rank or position size.
## REF_CP-3D_F_OutputAndQA.md
# CP-3D F — Output and QA

Required QA tests:

1. Security identifiers and terms match the observed quote.
2. Every market value has source, timestamp, quote type and freshness status.
3. Price, yield, spread, benchmark, call and settlement conventions are explicit.
4. Vendor observations remain separate from RBOT calculations.
5. Implied risk is labelled model-dependent with assumptions and sensitivity.
6. Liquidity/ownership/flow claims are evidence-backed and dated.
7. Fundamental-versus-market disagreement remains visible.
8. No market value, probability, recommendation, rank or size is fabricated.
9. Markdown contract validation and semantic/numerical checks pass.

The Analysis section contains T3E.1–T3E.10. Evidence Trace records quote and calculation lineage. Gaps & Conflicts captures stale, missing or inconsistent observations. QA Validation reports each test and final status.

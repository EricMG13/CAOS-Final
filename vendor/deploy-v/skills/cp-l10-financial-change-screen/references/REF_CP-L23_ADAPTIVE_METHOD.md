# CP-L23 Adaptive Method

This reference owns allocation only. It does not reproduce CP-2D liquidity-bridge calculations, CP-2E exposure calculations, or CP-2G forecast arithmetic.

## Algorithm

1. **Gate.** Confirm subject identity, period/horizon, and evidence scope. Identity failure yields `BLOCKED_IDENTITY`; missing topic evidence yields a `PARTIAL` source gate.
2. **Classify.** Assign all six topics materiality and evidence status. Undisclosed facility access or hedge terms remain missing; missing evidence is never `IMMATERIAL`. High missing/conflicted evidence becomes `GAP_ONLY`.
3. **Rank.** Use urgency, downside magnitude, evidence confidence, then canonical topic order. Record the deterministic rank.
4. **Assign depth.** Use `DEEPEN`, `SUMMARIZE`, `GAP_ONLY`, or `IMMATERIAL` in proportion to materiality, evidence quality, and the decision question. There is no fixed count of `DEEPEN` topics.
5. **Develop the screen.** Give each topic enough explanation, claims, metrics, and source trace to make its disposition decision-useful. Continue for as long as the evidence supports useful analysis; do not add filler or unsupported arithmetic.
6. **Preserve semantic boundaries.** `GAP_ONLY` states the missing evidence and impact without a conclusion. `IMMATERIAL` requires affirmative evidence of no liquidity or forward-risk transmission. Output depth and length are otherwise unspecified by this authority.
7. **Upgrade.** Every `DEEPEN` and material `GAP_ONLY` row creates a literal CP-2D, CP-2E, or CP-2G upgrade. Do not demote a topic solely because another topic is also deepened.
8. **Status.** Derive `BLOCKED_IDENTITY`, `COMPLETE_WITH_GAPS`, or `COMPLETE`, then one permitted LITE upgrade outcome.

No fixed allocation ledger, reserve, topic-unit pool, word count, token count, claim count, metric count, or reference count applies. The screen never authorizes a full bridge, sensitivity model, or forecast.

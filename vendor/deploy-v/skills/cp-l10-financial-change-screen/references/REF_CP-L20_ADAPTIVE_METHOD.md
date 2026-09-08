# CP-L20 Adaptive Method

This reference owns allocation only. It does not reproduce CP-2 synthesis, CP-2C governance scoring, or CP-2F ESG materiality methods.

## Algorithm

1. **Gate.** Validate subject identity and source scope. Identity failure yields `BLOCKED_IDENTITY`; incomplete topic evidence yields a `PARTIAL` gate.
2. **Classify.** Assign each of the six topics materiality and evidence status. Missing evidence cannot be `IMMATERIAL`; high materiality plus missing or conflicted evidence must be `GAP_ONLY`.
3. **Rank.** Rank by urgency, downside magnitude, evidence confidence, then canonical topic order. Record the deterministic rank.
4. **Assign depth.** Use `DEEPEN`, `SUMMARIZE`, `GAP_ONLY`, or `IMMATERIAL` in proportion to materiality, evidence quality, and the decision question. There is no fixed count of `DEEPEN` topics.
5. **Develop the screen.** Give each topic enough explanation, claims, metrics, and source trace to make its disposition decision-useful. Continue for as long as the evidence supports useful analysis; do not add filler or unsupported detail.
6. **Preserve semantic boundaries.** `GAP_ONLY` has a structured evidence request and no analytical conclusion. `IMMATERIAL` names affirmative evidence and why no credit transmission exists. Output depth and length are otherwise unspecified by this authority.
7. **Upgrade.** Every `DEEPEN` and material `GAP_ONLY` topic creates an upgrade to its literal CP-2, CP-2C, or CP-2F owner. Do not demote a topic solely because another topic is also deepened.
8. **Status.** Use `BLOCKED_IDENTITY`, `COMPLETE_WITH_GAPS`, or `COMPLETE` from the structured gate and allocations. Derive only `LITE_COMPLETE`, `FULL_UPGRADE_RECOMMENDED`, or `FULL_UPGRADE_REQUIRED`.

No fixed allocation ledger, reserve, topic-unit pool, word count, token count, claim count, metric count, or reference count applies. Six-topic coverage and the screening-only authority remain mandatory; no LITE output authorizes a FULL-owned conclusion.

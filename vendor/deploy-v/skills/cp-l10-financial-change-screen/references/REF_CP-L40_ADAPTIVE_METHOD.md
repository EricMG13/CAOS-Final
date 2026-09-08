# CP-L40 Adaptive Method

This reference owns allocation only. It does not reproduce CP-4 legal interpretation, CP-4B structural mapping, or CP-4A capacity calculations.

## Algorithm

1. **Gate.** Confirm subject identity and controlling-document scope. Identity failure yields `BLOCKED_IDENTITY`; missing documents or schedules yield a `PARTIAL` gate.
2. **Classify.** Assign each topic materiality and evidence status. Missing evidence cannot be `IMMATERIAL`; high missing/conflicted evidence is `GAP_ONLY`.
3. **Rank.** Rank by urgency, downside magnitude, evidence confidence, then canonical topic order. Record deterministic `priority_rank`.
4. **Assign depth.** Use `DEEPEN`, `SUMMARIZE`, `GAP_ONLY`, or `IMMATERIAL` in proportion to materiality, evidence quality, and the decision question. There is no fixed count of `DEEPEN` topics.
5. **Develop the screen.** Give each topic enough explanation, claims, metrics, and source trace to make its disposition decision-useful. Continue for as long as the evidence supports useful analysis; do not add generic legal language or unsupported detail as filler.
6. **Preserve semantic boundaries.** `GAP_ONLY` has no legal or analytical conclusion. `IMMATERIAL` requires affirmative provision-level evidence of no meaningful transmission. Output depth and length are otherwise unspecified by this authority.
7. **Upgrade.** Every `DEEPEN` and material `GAP_ONLY` topic creates a CP-4, CP-4B, or CP-4A upgrade. Do not demote a topic solely because another topic is also deepened.
8. **Status.** Derive `BLOCKED_IDENTITY`, `COMPLETE_WITH_GAPS`, or `COMPLETE`, then a permitted LITE outcome. Never derive legal, compliance, ranking, capacity, or recovery conclusions.

No fixed allocation ledger, reserve, topic-unit pool, word count, token count, claim count, metric count, or reference count applies. The screen never expands legal, compliance, ranking, capacity, or recovery authority.

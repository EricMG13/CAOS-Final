# CP-L30 Adaptive Method

This reference owns allocation only. It does not reproduce CP-3D market calculations, CP-3A recovery/preference methods, or CP-3 relative-value selection.

## Algorithm

1. **Gate.** Confirm issuer/security identity and dated market scope. Identity failure yields `BLOCKED_IDENTITY`; stale or partial topic evidence yields a `PARTIAL` gate.
2. **Classify.** Assign all six topics materiality and evidence status. Missing evidence cannot be `IMMATERIAL`; high missing/conflicted evidence is `GAP_ONLY`.
3. **Rank.** Apply urgency, downside magnitude, evidence confidence, then canonical topic order. Record the deterministic rank.
4. **Assign depth.** Use `DEEPEN`, `SUMMARIZE`, `GAP_ONLY`, or `IMMATERIAL` in proportion to materiality, evidence quality, and the decision question. There is no fixed count of `DEEPEN` topics.
5. **Develop the screen.** Give each topic enough explanation, claims, metrics, and source trace to make its disposition decision-useful. Continue for as long as the evidence supports useful analysis; do not add market commentary or unsupported detail as filler.
6. **Preserve semantic boundaries.** `GAP_ONLY` contains no analytical conclusion. `IMMATERIAL` needs affirmative evidence that the topic has no meaningful transmission to the screen. Output depth and length are otherwise unspecified by this authority.
7. **Upgrade.** Every `DEEPEN` and material `GAP_ONLY` topic creates a CP-3D, CP-3A, or CP-3 upgrade. Do not demote a topic solely because another topic is also deepened.
8. **Status.** Derive `BLOCKED_IDENTITY`, `COMPLETE_WITH_GAPS`, or `COMPLETE`, then one permitted LITE outcome. The only module postures are the four literal screening values.

No fixed allocation ledger, reserve, topic-unit pool, word count, token count, claim count, metric count, or reference count applies. The screen cannot be converted into recommendation, ranking, valuation, recovery, or sizing authority.

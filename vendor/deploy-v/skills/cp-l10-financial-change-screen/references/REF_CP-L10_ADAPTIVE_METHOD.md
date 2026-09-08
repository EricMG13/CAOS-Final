# CP-L10 Adaptive Method

This reference owns allocation only. It does not reproduce CP-1 extraction, normalization, calculation, or CP-1B earnings-delta methods.

## Algorithm

1. **Gate.** Confirm subject identity. If it is missing, ambiguous, or conflicted, emit `BLOCKED_IDENTITY`. Otherwise classify the source gate as `COMPLETE` or `PARTIAL`.
2. **Classify.** For all six canonical topics, assign materiality, evidence status, and a provisional disposition. Missing evidence is never `IMMATERIAL`; high materiality with missing or conflicted evidence is `GAP_ONLY`.
3. **Rank.** Order attention by urgency, downside magnitude, evidence confidence, then canonical topic order. The order is deterministic and must be recorded in `priority_rank`.
4. **Assign depth.** Use `DEEPEN`, `SUMMARIZE`, `GAP_ONLY`, or `IMMATERIAL` in proportion to materiality, evidence quality, and the decision question. There is no fixed count of `DEEPEN` topics.
5. **Develop the screen.** Give each topic enough explanation, claims, metrics, and source trace to make its disposition decision-useful. Continue for as long as the evidence supports useful analysis; do not add filler or unsupported detail.
6. **Preserve semantic boundaries.** `GAP_ONLY` contains structured missing evidence, impact, required source, and upgrade information but no analytical conclusion. `IMMATERIAL` requires affirmative evidence of no meaningful transmission. Output depth and length are otherwise unspecified by this authority.
7. **Upgrade.** Every `DEEPEN` and decision-material `GAP_ONLY` topic creates a CP-1 or CP-1B upgrade item. Do not demote a topic solely because another topic is also deepened.
8. **Status.** Identity failure gives `BLOCKED_IDENTITY`. Any material missing/conflicted evidence or required FULL upgrade gives `COMPLETE_WITH_GAPS`; otherwise use `COMPLETE`. The structured outcome is `LITE_COMPLETE`, `FULL_UPGRADE_RECOMMENDED`, or `FULL_UPGRADE_REQUIRED`.

No fixed allocation ledger, reserve, topic-unit pool, word count, token count, claim count, metric count, or reference count applies. Coverage remains exactly six canonical topics, and unused effort never authorizes FULL-owned analysis.

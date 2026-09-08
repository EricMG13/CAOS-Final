# Deploy V navigation numbered UX

CP-OS displays only pre-rendered sequential choices. The user selects a CP-0
run when more than one valid context exists, then moves between dependency steps;
module rows are informational and are never numbered choices.

Every step card keeps the same controls:

1. Next step
2. Previous step
3. Refresh `_RUNS`
4. Change run
5. Stop

An unavailable direction remains visible as unavailable, so reply meanings do
not move. A run selector numbers each valid canonical CP-0 context, followed by
Refresh `_RUNS` and Stop. With no valid CP-0 context, show `Run CP-0` and only
the three pre-rendered refresh/stop responses produced by the runtime. When the
configured folder cannot be listed, show only the runtime's two numbered
choices: Refresh `_RUNS` and Stop. An invalid reply re-renders that correction.
Resolve Stop using the options on the prior rendered card before interpreting a
fresh folder error or changed run selector.

Each module row contains only its readiness emoji, canonical module ID and
catalog description; its CP-0 candidate command with optional qualifiers; and,
for a conditional, blocked, or invalid row, one short `Cannot run:` reason.

Group only adjacent modules sharing a layer; a later return to the same layer is a new step. Each step follows producer-before-consumer order. Show incomplete/stale artifact reasons and missing prerequisite blockers on the card.

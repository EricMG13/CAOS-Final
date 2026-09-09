# DESIGN.md — visual language

**North star: the committee terminal.** A refined institutional terminal for
buy-side credit analysts. Calm enough for committee work, live enough for desk
posture, exact enough that every number reads as traceable rather than
decorative.

Dark, dense, single mode. Filed output inverts to paper — ink on
cream — because filed output is a different object from the live surface.

Rejected outright: friendly consumer SaaS, marketing dashboards, pastel cards,
decorative gradients, glow, glassmorphism, raw terminal dumps. Dense is allowed.
Disorganised is not.

## Tokens

Bound design system: **CAOS (caos-frontend)**. The bundle declares `--caos-*`
but **not** `--font-sans|mono|display` — the app declares those, or every
`font:` shorthand using one is invalid at computed-value time and silently
falls back to 16px.

```
--caos-bg #0a0a0f   --caos-panel #12121a   --caos-elevated #1a1a24
--caos-border #262633   --caos-text #e6e6ef   --caos-muted #8a8a9a
--caos-accent #4f8cff
--caos-success #22c55e   --caos-warning #f5a524   --caos-critical #ef4444
--caos-idle #3f3f46
--tranche-1l #2dd4bf  --tranche-2l #4f8cff  --tranche-unsec #f5a524
--tranche-sub #a855f7  --tranche-eq #64748b
```

Type scale: `3xs 8` `2xs 8.5` `xs 9` `sm 9.5` `md 10` `lg 10.5` `xl 11`
`2xl 12` `metric 16` `hero 22`.

## Named rules

**Signal-only colour.** Accent and semantic colours mean action, selection,
status, seniority or lineage. Never decoration.

**Numeric truth.** Financial values, ids, ratings, dates and confidence scores
are mono and tabular so columns scan and decimals align.

**Severity is shape and hue.** Success and running are a disc, warning a
triangle, critical a rounded square, idle a flat dot. Colour alone never carries
status.

**Paper is for filed output only.** Ink on cream inside the deliverable. It
must not leak into navigation, buttons, panel headers or
analytical tables.

**Motion only for live state.** No entrance animation, no hover flourish.
Reduced motion is honoured.

**One evidence surface.** The context drawer and the per-surface evidence rail.
There is no second inspector.

## Chrome

Four bands, in order, on every section: ribbon → decision brief
(CHANGE · IMPACT · ACTION · EVIDENCE + one headline figure) → tabs →
verdict strip. Then the rail, the body, and a right column that is always about
the selected thing, never a second menu.

Panels: hairline border, 6–10px radius, one faint resting shadow, a 29–30px
sentence-case header. A larger shadow means the object floats above the
workflow.

The ribbon carries at most three actions and exactly one primary.

## Rules with teeth

- A refused control stays **visible and refused, with its reason named**.
  Hiding it teaches the wrong model of the system.
- Every ready conclusion carries observation time, origin, method, approval and
  freshness.
- A private 404 and an absent route share one neutral wording:
  "Unavailable or not permitted."
- Dialog openers are passed explicitly, never inferred from
  `document.activeElement` — WebKit does not focus a button on click.
- No web font. No emoji in product chrome.

## Reference

Design source: https://claude.ai/design/p/69d37748-8595-4309-9b06-bc5f9529a29c

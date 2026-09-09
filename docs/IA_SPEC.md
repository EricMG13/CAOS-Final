# CAOS v2 — information architecture spec

The workspace: what surfaces exist, what each is for, and the rules that hold
across all of them. Structure and contracts live in `docs/SYSTEM_SPEC.md`;
scope and decisions in `docs/REBUILD_PLAN.md`. Visual language is `DESIGN.md`
and the bound CAOS design system.

Reference design: https://claude.ai/design/p/69d37748-8595-4309-9b06-bc5f9529a29c

---

## 1. One workspace, nine sections

There is one screen. The chrome never changes; only the body does. Nine
sections is the whole surface — a tenth needs a decision entry, not a ticket.

| Section | URL | Primary object | Primary action |
|---|---|---|---|
| Directory | `/directory/` | the case | open a case |
| Upload | `/upload/` | the source pack | admit a pack, pin a set |
| Analysis | `/analysis/` | the module output | read, cite, dispute |
| Book | `/book/` | the credit, across the portfolio | filter, group, compare |
| Run | `/run/` | the resolved route | approve a plan, accept a run |
| Model | `/model/` | the projection | read, compare cases |
| Report | `/report/` | the draft revision | edit, sign the opinion |
| Committee | `/committee/` | the deliverable | freeze, file |
| Admin | `/admin/` | the deployment | — (unavailable capability) |

One word per URL, trailing slash, static export. Every pre-v2 slug forwards to
its new home with the query string intact, replacing history so the entry stays
router-owned; the workspace reads the re-presented case and run as a route
replay.

**Deep-Dive is `/analysis/`. PM Review is `/book/`. IC Pack is `/committee/`.**
They are sections, exactly like Model and Report. They are not personas, not
modes, not shells, and they do not switch identity.

---

## 2. Persona is composition, not authority

The AI Studio build carried an `analyst | pm | qa` toggle that re-skinned one
screen. It is deleted.

- A section composes a view. It grants nothing.
- The **served role** is shown read-only beside the section rail and is never a
  control. A role picker, if one is ever drawn, still grants nothing.
- Every governed action is authorised server-side against case standing and
  global role at commit time, regardless of which section issued it.

A user with `READER` standing sees `/committee/` and can read the deliverable.
The filing control is present and refused, with the reason stated —
`APPROVER_NOT_INDEPENDENT`, or absent standing — never hidden. Hiding a control
teaches the wrong model of the system.

---

## 3. Invariant chrome

Four bands sit above the body on every section, in this order. They are the
same components everywhere and they answer the same four questions.

1. **Ribbon** — *what am I looking at, and is it trustworthy?* Brand, then
   context chips (subject, route, model availability, calculation verification),
   then, right-aligned, execution state, persistence state, approval state, and
   at most three actions of which exactly one is primary.
2. **Decision brief** — *what changed, what it means, what to do, on what
   evidence.* Four cells — CHANGE · IMPACT · ACTION · EVIDENCE — plus one
   right-aligned headline figure. Every section fills all four or renders the
   observed-empty state; none is optional.
3. **Tabs** — the section's own views. Never navigation between sections.
4. **Verdict strip** — the single conclusion this section currently supports,
   with its severity as shape *and* hue, and the one thing blocking it.

Below: the rail on the left, the body, and — where the section has one — a
right column that is always *about the selected thing*, never a second menu.

### Rail

Two groups. **Workspace** lists the nine sections with a count and a one-line
state (`ACTIVE · CP-6 OF 12`, `CP-CF · ACCEPTED`, `rev_3 · FROZEN`). Below it
a **section-local** group: filters in Book, report sections in Committee, the
route frontier in Analysis. The foot carries two controls and no more.

The rail is the only navigation. There is no second inspector, no utility
drawer, no command palette that reaches things the rail cannot.

---

## 4. Section contracts

Each section declares: what it is for, its primary object, exactly one
page-level primary action, one dominant work region, and how it degrades.

### 4.1 Directory — `/directory/`

The case register. Search plus one filter and one action per row. No batch
state. Document-first intake lives here: the panel posts files and nothing
else; the server creates or resolves the case, admits every file or none,
classifies, selects a route and starts the run. Issuer, label, types, periods,
dispositions and route come back as **labelled suggestions**, never taken from
the browser. A completed intake run is opened for review, never accepted on the
analyst's behalf.

### 4.2 Upload — `/upload/`

The source pack and the pinned set. Per document: grade, disposition, page
count, digest, and which set versions include it. Withdrawal is here and is
checked live at every use. Restatement across intakes is surfaced, not silently
resolved.

### 4.3 Analysis — `/analysis/` (Deep-Dive)

The dominant section. Three columns:

- **Left** — source register (CP-0) and the ranked evidence trace (CP-5), each
  row carrying its confidence and its anchor.
- **Centre** — the module output for the selected tab: normalised financials
  with the formula bar above them, the definition conflict register, the
  adjusted-vs-reported comparison, the workflow step outputs.
- **Right** — clearance (CP-5), the route frontier, capital structure, armed
  triggers.

Rules:

- **Every figure is one click from its evidence.** Selecting a cell drives the
  evidence panel to the document, page and rectangle; the chip shows
  `D-04 p.68 ¶2`, not a document name.
- **Conflicts are shown, never resolved.** Both readings, both citations, the
  size of the divergence.
- The formula bar shows the derivation of the selected cell in the expression
  language, evaluated server-side, with the lineage of every operand.
- A `RESTRICTED` node's output renders with its limitation attached, not hidden
  and not promoted to an error.

### 4.4 Book — `/book/` (PM Review)

The portfolio, compared honestly.

**Filter and group.** Facets: status, net-leverage band, evidence freshness,
definition set. Grouping keys: sector, rating, pathway, vintage, sponsor. Saved
views are named and shareable.

**Compare.** Two to four credits side by side on one basis, stated in the
brief: period, scenario, accepted-only.

**The metric passport.** Selecting any cell — in the table or the comparison —
opens the passport, and it always carries all of:

| | |
|---|---|
| Definition | in words, plus the standard it follows |
| Period | the exact window, not "latest" |
| Scenario | base, downside, or named |
| Evidence date | the date of the underlying document |
| Computed at | when this value was produced |
| Snapshot | the accepted snapshot it belongs to |
| Method | the calculator, and whether it verified |
| Derivation | the expression, with operands |
| Citations | anchored chips |
| Supporting research | direct links to the accepted module artifacts, any running Deep Research, and prior filed deliverables |

**Definition deviation is marked everywhere it applies**, not once in a
footnote: on the credit, on every affected cell, and in the comparison, with
the size of the difference stated and a restatement offered. Two spellings of a
metric never silently share a column.

Stale evidence is a colour *and* a date, on every row it affects.

### 4.5 Run — `/run/`

The resolved route and its frontier. Node states are the bundle's:
`COMPLETE`, `RUNNABLE`, `RESTRICTED`, `BLOCKED`, each with its reason named —
which upstream, which edge type, which gate. The one `QA_GATE` reads as a gate.

Compilation, acceptance and research-plan approval live only here. Analysis
reads accepted artifacts and Directory links into a credit; neither renders the
compile form or the accept control.

### 4.6 Model — `/model/`

CP-CF's accepted projection (`SYSTEM_SPEC.md` §6). The workbook build, its
assumptions, scenarios and revisions that stood here went with CP-MODEL
(`docs/DECISIONS.md` §48); what remains is read, never edited.

The projection, per case-period: the operating, investing and financing lines,
the debt and cash roll-forward, and
**the residual as its own column**. A period whose residual exceeds tolerance
renders unavailable with its reason, and every later period in that case
renders unavailable too — never as zero growth, and never silently balanced.
Each projected figure carries the driver that produced it and that driver's
evidence, so the passport contract (§4.4) holds for forecast cells exactly as
it does for actuals.

### 4.7 Report — `/report/`

The draft revision and the opinion. Sign-off binds the exact saved revision.
An `ANALYST_JUDGMENT` narrative asserting an uncited figure is refused at
freeze, and the refusal names the figure.

### 4.8 Committee — `/committee/` (IC Pack)

The deliverable the host renders from the frozen snapshot (`SYSTEM_SPEC.md`
§7). Three regions:

- **Rail** — the accepted artifacts in route order, each showing its module
  and disposition, then the narrative and the provenance index.
- **Centre** — the document itself on paper, watermarked `DRAFT — NOT FILED`
  until it is filed.
- **Right** — the filing. The opinion and the revision it binds, the freeze,
  the filing with its independence stated, and the receipt once filed. Every
  refusal shows its code and what would clear it.

File is present and refused while the freeze has no current opinion or the
actor signed or froze it (`APPROVER_NOT_INDEPENDENT`). The output is one HTML
file and the surface says so.

### 4.9 Admin — `/admin/`

An explicit unavailable capability. It renders the unavailable state and names
what is missing. It does not pretend.

---

## 5. Cross-section rules

- **One snapshot per case on screen.** Every surface for a case renders the
  shell's single visible snapshot for that case. Book pins one accepted
  snapshot per compared case and names each binding; the shared comparison
  basis is period, scenario and accepted-only (§4.4), not a shared snapshot
  across issuers. No surface mints a second accepted identity for the same
  case. The visible lens and the latest accepted authority are separate and
  both are named; a pinned lens moves only through an explicit switch.
- **One evidence drawer.** Opened from a chip or an explicit control, its opener
  passed from the click, focus returned on Escape. There is no second inspector.
- **Ask is scoped to what is on screen.** In Analysis it asks the case, in Book
  the book, in Committee the deliverable. It never widens scope silently.
- **Route replay.** A forwarded slug, a back navigation and a cross-case race
  are all resolved by one authority machine against stale responses. A late
  response for a case the user has left is discarded, never rendered.
- **Suggestions are labelled.** Anything the machine proposes — issuer, type,
  period, disposition, route — is visibly a suggestion until a person commits
  it.

---

## 6. States

Every region renders these distinctly, and `ready` carries no marker of its own:

`loading` · `observed-empty` · `error` · `unavailable` (an observed 404) ·
`stale` (the authority changed underneath) · `offline` (a request that never
reached the server) · `partial` (rendered through warning status and inline
notes).

- A private 404 and an absent route share one neutral wording:
  "Unavailable or not permitted." The UI never distinguishes them.
- "No material change" is legal only for a successful, timestamped
  `observed-empty` response. It is never inferred.
- An offline request renders one sentence in the page-level alert and never
  engine text.
- A refusal shows its typed code and what would clear it. It never shows the
  underlying exception.

---

## 7. Density and motion

- Dark institutional terminal, single mode. Paper — dark ink on cream — only
  inside filed output and research documents.
- Colour is signal: status, seniority, selection, lineage. Never decoration.
  Status is shape *and* hue, never hue alone.
- Numerics are mono and tabular everywhere so columns scan and decimals align.
- Motion only for live state. No entrance animation, no hover flourish.
  Reduced motion is honoured.
- Every dialog opener is passed explicitly, never inferred from
  `document.activeElement` — WebKit does not focus a button on click, and an
  inferred opener drops focus to the landmark on cancel.

---

## 8. What is deliberately not here

- No dashboard. No summary tiles that aggregate across cases without stating a
  basis.
- No role switcher that changes what a user may do.
- No second navigation surface — no mega-menu, no breadcrumb trail, no tab bar
  that leaves the section.
- No inline editing of a filed deliverable. Filed is immutable; the path
  forward is a new revision.
- No chart that carries a number the passport cannot explain.

# Report Builder — the CP-MEMO contract

> **Archived 2026-09-09 under `docs/DECISIONS.md` §48.** Not in the build.
> The CP-MEMO contract as the specs and the plan carried it, kept verbatim for
> a build that brings the `.docx` back. What that build needs, measured in
> §48: `libreoffice-writer` and `poppler-utils` in the image (the memo's
> `render_pdf.py` resolves `soffice` and `pdftoppm` by name and refuses
> without either), `python-docx` and `pypdf` for `cp_memo`, and a worker
> process for the publication job. The bundle code --
> `vendor/deploy-v/skills/cp-memo-credit-research-report/` -- is still
> vendored and pinned. Section references below are to the documents as they
> stood before §48.

## `docs/SYSTEM_SPEC.md` §7

## 7. Publication

The legacy CP-MEMO contract, unchanged (`IA_SPEC.md` §4.8 for the surface):

- Exactly one `.docx`, `[IssuerID]_CP-MEMO_[YYYYMMDD].docx`, never overwriting.
  No PDF, deck, dashboard or workbook deliverable; the PDF and page images are
  QA material.
- Ten fixed sections, in order, from cover to module provenance index.
- CP-MEMO originates nothing. It may select, reorder, shorten, deduplicate and
  faithfully restate. It may not calculate, infer, fill a gap, resolve a
  disagreement, change confidence or taxonomy, rank findings, or author a
  recommendation.
- Both sides of an unresolved conflict are preserved. `Restricted` and
  `SCREENING_ONLY` qualifications survive into the report.
- Publication gate: inventory → draft → every page inspected at 100 % → publish.
  Any defect stops publication.

Around it, the host's own chain: the analyst signs an opinion on the exact saved
revision (expected-head CAS); freeze refuses without a current sign-off and
refuses a narrative asserting an uncited figure; filing refuses the opinion
signer and the freeze actor (`APPROVER_NOT_INDEPENDENT`) and writes an immutable
detached receipt. The approved bytes always read `PENDING APPROVAL`.

The audit package is verifiable with the standard library alone and re-renders
the export from the frozen payload.

## `docs/IA_SPEC.md` §4.8

### 4.8 Committee — `/committee/` (IC Pack)

The legacy CP-MEMO deliverable. Three regions:

- **Rail** — the ten report sections in order, each showing its contributing
  module and disposition.
- **Centre** — the document itself on paper, watermarked `DRAFT — NOT
  PUBLISHED` until it is published.
- **Right** — the publication gate. Every page as a thumbnail with a pass, fail
  or not-yet-checked state; the defect named in the language of the gate
  (clipping, overlap, broken table, font substitution, orphan heading, bad page
  break, header/footer defect). Below it the editorial boundary, stated and
  counted — figures originated, conflicts preserved, confidence changes. Below
  that the module provenance index.

Publish is present and refused while any page fails. The output is one `.docx`
and the surface says so.

## `docs/REBUILD_PLAN.md` Phase 8

## Phase 8 — Publication

- CP-MEMO: ten fixed sections, editorial boundary enforced, conflicts preserved,
  one `.docx`, never overwriting.
- Publication gate: inventory → draft → per-page visual QA → publish.
- Opinion on the exact revision; freeze; filing refusing the signer and the
  freezer; detached receipt; the verifiable package over the audit chain
  Phase 6 started.

**Exit:** `test_publish_refused_until_every_page_passes`;
`test_filing_refuses_the_opinion_signer`;
`test_audit_package_verifies_with_stdlib_alone`.

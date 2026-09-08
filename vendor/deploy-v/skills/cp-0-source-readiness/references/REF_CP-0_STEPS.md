Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

The following sections are binding method for every run of this module, not conditional on a step naming them -- open them before authoring output: REF_CP-0_Discipline.md, REF_CP-0_ExampleOutputPattern.md.

Original files, in this bundle: REF_CP-0_A_FileClassification.md, REF_CP-0_B_EntityIdentification.md, REF_CP-0_C_DocumentMapping.md, REF_CP-0_D_QualityAssignment.md, REF_CP-0_Discipline.md, REF_CP-0_E_ContentModuleMapping.md, REF_CP-0_ExampleOutputPattern.md, REF_CP-0_F_GapLogging.md, REF_CP-0_G_ConflictLogging.md, REF_CP-0_H_FileQualityRisk.md, REF_CP-0_I_DownstreamReadiness.md, REF_CP-0_J_MasterIndexUpdate.md, REF_CP-0_K_ExportAssembly.md

## REF_CP-0_A_FileClassification.md
<!-- REF_CP-0_A_FileClassification (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="A" name="PackTriageAndSelection">
# Pack triage and selection

Inventory every supplied source before parsing. Identify content from the document itself; filenames are hints only. Record the source root, original relative path, byte size, SHA-256, accessibility, document family, provisional entity/period and duplicate candidates. No files or no accessible evidence for the stated objective is `BLOCKED`.

## Frozen decision

Assign exactly one decision to each original:

| Decision | Use |
|---|---|
| `PARSE_FULL` | The whole source is decision-useful and restructuring materially improves reliable use. |
| `PARSE_TARGETED` | Only identified sections are useful, and the exclusion boundary is auditable. |
| `PASS_THROUGH` | Native content is complete and usable without a derivative. |
| `SKIP_DUPLICATE` | Content is contained by a named replacement source. |
| `SKIP_LOW_VALUE` | Content is accessible but immaterial to the objective. |
| `BLOCKED` | Required content cannot be accessed or faithfully prepared. |

Score `evidence_value 0-5 + authority_uniqueness 0-3 + structural_benefit 0-3 - duplication_noise 0-4`. Apply accessibility, critical-document, downstream-demand and duplicate overrides after scoring. Page count is never a value proxy. A short waiver may require full parsing while a repetitive appendix may be targeted or skipped.

## Calibration defaults

- Annual and quarterly filings: full or targeted by section completeness, tables and downstream period requirements.
- Executed legal documents, amendments, waivers and releases: full when governing terms may matter; never merge an amendment into its base.
- Unique lender/financing presentations: `PARSE_FULL` by default because narrative, assumptions, sensitivities and accessible notes are decision-useful.
- General investor presentations: full when unique narrative or operating evidence is material; otherwise targeted with every exclusion explained.
- Clean native text or small spreadsheets: pass through when structure is already reliable.
- True contained duplicates: skip only after recording the replacement source ID.

Record score components, decision, rationale, overrides, required extraction profile, downstream modules, uncertainty and reviewer status in the Triage Register. Freeze the register before extraction; later changes require an explicit re-triage record.
</step_reference>
## REF_CP-0_B_EntityIdentification.md
<!-- REF_CP-0_B_EntityIdentification (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="B" name="IdentityPeriodAndVersionMap">
# Identity, period and version map

Identify issuer, borrower, parent, guarantors, restricted/unrestricted entities, sponsor, reporting perimeter and instruments from document content. Record source ID, locator, exact label and confidence; never infer identity from a filename alone.

Assign a stable `logical_source_id` to each distinct evidentiary source and link its original, prepared artifact and any successor. Record issue/as-of date, reporting period, quarter/YTD/FY basis, currency/unit where stated, draft/executed status and version relationships.

Hash equality is duplicate evidence, not the only duplicate test. A base agreement and its amendment, waiver, supplement or release are distinct logical sources and remain separately active. For a contained duplicate, record `selected_replacement_source_id`. For a superseded version, preserve provenance and state why a later version controls; do not erase conflicts or material historical terms.

The original path and hash remain stable through the run. Prepared artifacts inherit the original's entity, period and authority metadata but receive their own artifact ID, path, hash, extraction confidence and fidelity result.
</step_reference>
## REF_CP-0_C_DocumentMapping.md
<!-- REF_CP-0_C_DocumentMapping (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="C" name="DocumentProfiles">
# Downstream-aware document profiles

Apply every matching profile to hybrid sources. Each parse job declares `LAYOUT_TEXT`, `TABLE_FIRST`, `SLIDE_CHART`, `LEGAL_CLAUSE`, `OCR_SCAN`, `SHEET_RANGE` or `HYBRID` and the downstream evidence requirements it serves.

| Document family | Minimum retained content |
|---|---|
| Annual/quarterly report | Statements, notes, period labels, segment/KPI tables, debt/liquidity, covenant and cash-flow disclosures, narrative drivers and locators. |
| Earnings release | Reported and adjusted measures, reconciliations, quarter/YTD distinctions, guidance and management narrative. |
| Legal/financing | Definitions, operative clauses, baskets, tests, dates, parties, schedules, amendments and cross-references; preserve exact wording and clause/page locators. |
| Spreadsheet | Sheet names, used ranges, headers, formulas-as-displayed, notes, units, periods and cell/range locators; never execute macros. |
| Scan/image | OCR plus page/region anchors and confidence; retain image evidence for verification. |
| Investor/transaction deck | Slide text, tables, charts, transaction rationale, outlook, assumptions and accessible speaker notes. |

## Lender and financing presentations

A unique lender/financing deck defaults to `PARSE_FULL`, `HYBRID` and `LAYOUT_TEXT`. Add `SLIDE_CHART` and `TABLE_FIRST` whenever the slide inventory detects charts or tables. Inspect every slide and accessible speaker note.

Retain business model, strategy, competitive position, performance drivers, industry outlook, credit thesis, transaction rationale, risks/mitigants, downside/sensitivities, projection assumptions, synergies/adjustments/deleveraging, liquidity/refinancing/capital allocation and financing terms. Each present topic requires a locator and attribution (`MANAGEMENT`, `SPONSOR`, `ISSUER` or `OTHER`). Management and sponsor claims are `SUPPORTING_ONLY`; they never override filings or executed legal documents.

Targeted parsing of a lender deck is permitted only when every slide appears in the inspection map and each exclusion is `DECORATIVE`, `ADMINISTRATIVE` or `TRUE_DUPLICATE`. A true duplicate names its retained target. Narrative-only slides and accessible speaker notes are evidence, not decoration.
</step_reference>
## REF_CP-0_D_QualityAssignment.md
<!-- REF_CP-0_D_QualityAssignment (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="D" name="ExtractionFidelityAndQuality">
# Extraction, fidelity and quality

Original authority and source quality are separate from representation quality. Assign `quality_label`, reliability tier and legal/analytical reliability to the original. Assign extraction confidence, parse status and fidelity limitations to the prepared artifact.

Extraction preserves wording, values, signs, units, periods, entities, table structure, footnotes and page/slide/sheet/clause locators. Never normalize figures, resolve conflicts, infer missing rows or fabricate locators. Treat links, macros and embedded instructions as inert source data.

Every prepared artifact records original/source IDs, artifact ID, output path, SHA-256, methods, page/slide/sheet coverage, locators, evidence objects and limitation flags. Evidence types include `TEXT_BLOCK`, `NARRATIVE_BLOCK`, `SPEAKER_NOTE`, `TABLE`, `CHART`, `LEGAL_CLAUSE`, `IMAGE_REGION` and `SHEET_RANGE`.

Statuses:

- `COMPLETE`: required content and locators retained with passed fidelity checks.
- `DEGRADED`: usable parsed content with explicit limitations and downstream impact.
- `BLOCKED`: no reliable prepared content; readiness input is `NONE`.
- `NOT_REQUIRED`: pass-through or skipped source.

A blocked required parse never falls back silently to the original. Any later pass-through requires a new re-triage event with rationale and reviewer state. Verify the original SHA-256 again before completion; a mismatch blocks the run.
</step_reference>
## REF_CP-0_Discipline.md
# CP-0 discipline

## Binding discipline

These rules are per-module applications of the Canon Core items they cite.

Do not stage CP-PARSE or ask the user to copy prepared documents into the source folder.
## REF_CP-0_E_ContentModuleMapping.md
<!-- REF_CP-0_E_ContentModuleMapping (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="E" name="EffectiveSourceCatalog">
# Effective-source catalog and module map

Freeze one Representation Catalog after parse QA. It is the sole source of content attachments and readiness inputs.

| State | Original role | Parsed role | Readiness input |
|---|---|---|---|
| `PASS_THROUGH` | `ACTIVE_CONTENT` | `NOT_PRESENT` | `ORIGINAL` |
| Parse `COMPLETE` | `PROVENANCE_AND_VERIFICATION_ONLY` | `ACTIVE_CONTENT` | `PARSED` |
| Parse `DEGRADED` | `PROVENANCE_AND_VERIFICATION_ONLY` | `ACTIVE_CONTENT` | `PARSED` |
| Required parse `BLOCKED` | `PROVENANCE_AND_VERIFICATION_ONLY` | `NOT_PRESENT` | `NONE` |
| `SKIP_DUPLICATE` | `EXCLUDED` | `NOT_PRESENT` | `NONE` |
| `SKIP_LOW_VALUE` | `INVENTORY_ONLY` | `NOT_PRESENT` | `NONE` |

Exactly one representation may have `ACTIVE_CONTENT` for every retained logical source. Parsed content requires a selected artifact ID, path and SHA-256. Degraded content requires limitations. Duplicate rows require a replacement source. Base documents and amendments remain distinct rows. Every derived path must be outside every original source root.

Map each effective representation—not both versions—to downstream modules. Record content basis, specific evidence demand, mapping status, readiness effect and limitation. Authority citations still point to the original source and its locator; the prepared artifact is the active content vehicle and carries lineage back to that original.

Generate `active_content_file_name` and `active_content_artifact_id` directly from this frozen catalog. Do not use a raw file registry to assemble downstream attachments.
</step_reference>
## REF_CP-0_ExampleOutputPattern.md
<!-- REF_CP-0_ExampleOutputPattern.md (T2 Example Library) | 2026-08-02 | Markdown-only handoff contract -->

# CP-0 example output pattern

Governing contract: `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`, `../../../CANON_SHARED.md § CP_CONFIDENCE_SCORE.md`

## Output order

1. Author complete canonical Markdown.
2. Validate contract and identity, fail closed.
3. Return concise status, limitations, recommended next command, and the
   Markdown link. Do not create an alternate analytical export.

## Canonical Markdown — required

Filename: `[IssuerID]_CP-0_[YYYYMMDD].md`

The canonical file is the sole analytical output and downstream handoff. It
contains the YAML front-matter envelope,
including `confidence_score` and `confidence_band`, followed by the canonical
H2 headings:

- `## Audit Summary`
- `## Analysis`
- `## Evidence Trace`
- `## Source Registry`
- `## Gaps & Conflicts`
- `## QA Validation`

The analysis includes:

- input/workspace gate and original-hash verification;
- triage register and parse-job results;
- lender slide/narrative coverage when applicable;
- frozen Representation Catalog showing the one active content representation;
- Source Register built from effective representations;
- gaps, conflicts and source-readiness summary;
- `SOURCE_READY_FOR_MODEL_ROUTE`/`SOURCE_SUFFICIENCY_ONLY` assessment when applicable;
- Recommended Run Command Sheet sourced only from active representations; and
- Master Index and evidence-package status.

Example representation rows:

| logical source | triage | parse status | original role | parsed role | readiness input | active file |
|---|---|---|---|---|---|---|
| Annual report | `PASS_THROUGH` | `NOT_REQUIRED` | `ACTIVE_CONTENT` | `NOT_PRESENT` | `ORIGINAL` | `annual-report.pdf` |
| Lender deck | `PARSE_FULL` | `COMPLETE` | `PROVENANCE_AND_VERIFICATION_ONLY` | `ACTIVE_CONTENT` | `PARSED` | `prepared/lender-deck.md` |

The supporting evidence ZIP, if any, is not a second analytical handoff. Users do not copy prepared artifacts back into the source folder.
## REF_CP-0_F_GapLogging.md
<!-- REF_CP-0_F_GapLogging (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="F" name="GapLogging">
# Gap logging

Log missing documents, missing periods, inaccessible/encrypted sources, incomplete or low-confidence extraction, absent locators, stale evidence, missing governing legal terms and unsupported downstream evidence demands. Distinguish a source gap from a parse gap.

Each gap records ID, type, severity (`CRITICAL`, `MATERIAL`, `MINOR`), logical source/evidence demand, affected modules, readiness effect, remediation, owner and status. A blocked required parse creates both a parse-failure record and the corresponding downstream source gap; it never becomes a pass-through input.

For a CP-MODEL objective, assess whether the pack contains source-located evidence for the required analytical handoffs, including four discrete quarters, fiscal years, quarter/YTD distinctions, segments, separate add-backs, KPIs, facility-level debt/carrying values, cash-paid interest/tax and business/transaction narrative. This is source sufficiency only; CP-0 does not normalize or validate those downstream outputs.
</step_reference>
## REF_CP-0_G_ConflictLogging.md
<!-- REF_CP-0_G_ConflictLogging (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="G" name="ConflictAndVersionLogging">
# Conflicts, duplicates and versions

Log inconsistent versions, periods, entities, amounts, narrative claims, legal terms and locators. Record both source IDs and locators, the conflict type/severity, downstream effect and required resolution. Do not reconcile silently during source preparation.

Deduplication requires a named retained source and an explicit containment basis. Never use a later amendment, waiver or supplement as the duplicate replacement for its base document; link both as a document family. A later official filing may control a current-period fact while the earlier source remains relevant evidence. Preserve that distinction.

Management, sponsor and issuer presentation claims can support context but cannot control over a filed statement or executed legal document. Record the conflict and apply the original-source hierarchy; do not rewrite the parsed narrative to make it agree.
</step_reference>
## REF_CP-0_H_FileQualityRisk.md
<!-- REF_CP-0_H_FileQualityRisk (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="H" name="FileQualityCoverageAndRisk">
# File quality, coverage and risk

Record corrupt, encrypted, screenshot-only, low-quality scan, stale, draft, unsigned, partial, untraceable, formula-dependent, missing-note and missing-locator risks. Each risk names the original source, selected representation, severity, affected content and downstream modules.

Reconcile coverage at page, slide, sheet/range and clause level as applicable. Every expected unit is retained, explicitly excluded under the frozen targeted plan, or logged as unreadable/blocked. A lender deck additionally requires a complete slide inspection map and topic-level narrative coverage ledger. `PRESENT` narrative must be `RETAINED` with a locator unless the parse is degraded or blocked.

Run representation QA after coverage QA: one active content representation per retained logical source, selected artifact hash present, degraded limitations present, skipped replacement links valid, no base/amendment collapse, original hashes unchanged, and all derivative paths outside source roots.
</step_reference>
## REF_CP-0_I_DownstreamReadiness.md
<!-- REF_CP-0_I_DownstreamReadiness (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="I" name="DownstreamReadiness">
Per-module source-readiness verdict: `READY` | `READY_WITH_LIMITATIONS` | `CONDITIONAL` | `BLOCKED`. Justify each verdict from the frozen Representation Catalog, content map, gaps, conflicts and risk log.

After the readiness table, produce the **Recommended Run Command Sheet**. One
row per recommended or blocked next live host module:

| Sequence | Module | Candidate command | Exact command | Source files to attach | Upstream handoff | Readiness | Why now / blocker |
|---:|---|---|---|---|---|---|---|

Rules:
1. Module IDs are canonical live, navigable hosts only: CP-1, CP-1A, CP-1B, CP-1C, CP-1D, CP-2, CP-2A, CP-2D, CP-2E, CP-2G, CP-2H, CP-3, CP-3C, CP-3D, CP-4, CP-4C, CP-5, CP-6, CP-8, CP-L10. Never recommend CP-X, CP-PARSE, a retired alias, CP-MODEL, CP-MEMO or CP-DR.
2. `candidate_command` is `Run <module_id>` plus only objective, issuer/entity and period qualifiers supported by this run. Its command module must match the row module exactly.
3. READY and READY_WITH_LIMITATIONS rows set `exact_command` equal to `candidate_command` and carry every limitation into the row.
4. CONDITIONAL and BLOCKED rows set `exact_command` to exactly `DO NOT RUN`; retain the candidate only as a non-executable preview and state the missing or unusable evidence briefly.
5. Source filenames come only from the frozen Representation Catalog/effective-source set. `PASS_THROUGH` attaches its original; `COMPLETE` or `DEGRADED` attaches its managed prepared artifact; `BLOCKED` and skipped rows attach nothing. Never attach both original and parsed content for one logical source.
6. Every receiving module retains this CP-0 handoff's `run_id` in canonical `upstream_artifacts_used`, even when another handoff is its immediate analytical dependency.
7. CP-0 passes managed artifacts directly to downstream modules. The user does not copy derivatives back into the source folder or reattach them between parsing and readiness.

## CP-MODEL boundary

For a CP-MODEL objective, emit only `SOURCE_READY_FOR_MODEL_ROUTE` with `assertion_scope=SOURCE_SUFFICIENCY_ONLY`, required downstream handoffs `CP-1`, `CP-1A`, `CP-1B`, `CP-2`, `CP-2A`, optional `CP-2G`, and `cp_model_input_contract=NOT_EVALUATED`. CP-0 may assess whether the active source set can support those modules. It may not claim normalized quarters, reconciliations, downstream handoffs or CP-MODEL inputs have passed.

The next executable action is the first runnable canonical live host row in T8. Never recommend CP-X or direct `Run CP-MODEL` from CP-0, and never emit `CP_MODEL_INPUT_READY`.
</step_reference>
## REF_CP-0_J_MasterIndexUpdate.md
<!-- REF_CP-0_J_MasterIndexUpdate (Tier 2) | 2026-08-02 -->
<step_reference module="CP-0" step="J" name="MasterIndexAndWorkspace">
# Master Index and managed workspace

Initialize or update Master Index state with run ID, issuer, objective, requested/resolved mode, source roots, managed workspace, original/prepared counts, entities, periods, version families, validation warnings, canonical handoff, evidence packages and downstream consumers.

The workspace is a unique run-owned directory outside every source root. Original roots are read-only. Store derivatives, indexes, registers, checksums and packages only in the workspace; validate all resolved paths and reject traversal, links outside the workspace, duplicate members and unsafe archive paths.

Before completion, compare every original `sha256_before` with `sha256_after`. A changed, missing or unexpectedly added original fails immutability verification. Record package hashes and the final active representation count so later consumers can prove they used the frozen effective-source set.
</step_reference>
## REF_CP-0_K_ExportAssembly.md
<!-- REF_CP-0_K_ExportAssembly (Tier 2) | 2026-08-02 | Markdown-only handoff contract -->
<step_reference module="CP-0" step="K" name="ExportAssembly">
Follow `../../../CANON_SHARED.md § CP_AB_EXPORT_SPEC.md`. Author and validate **canonical Markdown `[IssuerID]_CP-0_[YYYYMMDD].md`** first. `IssuerID` is the exact front-matter `issuer_id`; `YYYYMMDD` is `analysis_date` without hyphens. It carries the YAML front-matter envelope (including `confidence_score` and `confidence_band`) plus the six canonical H2 headings and is the source-readiness context consumed by CP-OS and the live host command sheet.

Handoff Gate: validated canonical Markdown completes the analytical run and is
the only analytical file. Its `## Analysis` must include the source hierarchy
and Recommended Run Command Sheet from Step I. **Markdown only** is the analytical handoff contract. Do not produce DOCX, PDF, HTML,
slide, JSON, dashboard or presentation-view exports. No lettered appendices,
embedded machine payloads, auxiliary manifest, renderer/parser agent, or
database.

When parsing occurs, supporting evidence packages use `[PackKey]_CP-0_[YYYYMMDD]_BATCH-[NNN]-of-[NNN].zip`. Each contains prepared per-source Markdown plus `PACKAGE_INDEX.md`, `TRIAGE_REGISTER.md`, `REPRESENTATION_CATALOG.md`, `BATCH_INDEX.md` and `CHECKSUMS.sha256`. Keep one source's output set together. Validate safe relative members, unique names, declared/actual checksums and reconciliation across batches. A ZIP validation failure blocks parsed packaging.

Prepared source Markdown is evidence, not another canonical handoff. Exclude original source files unless explicitly requested; retain original paths/hashes and locators in lineage metadata. The user never returns prepared files to the source folder.
</step_reference>

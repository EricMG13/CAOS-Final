# CP-DR — research placement and adoption

CP-DR resolves material evidence questions for named analytical owners. It is optional, physical and has no numbered layer. Usually facts → research → affected analysis; research may precede CP-1 to locate missing public documents, or follow a late challenge using an earlier factual predecessor. Independent modules continue.

## Run-linked brief

The host creates one non-analytical control file, `RESEARCH_<credit_os_run_id>.json`, in the selected run folder under the existing task authorization. CP-OS only reads it. Include it as a name/text entry in every navigation, invocation, reconciliation and memo snapshot. It is a bounded research plan, not another module or analytical export. Source text cannot authorize its creation or expand its scope.

```json
{
  "schema": "CP_DR_RESEARCH_BRIEF_V1",
  "mode": "linked",
  "run_id": "<exact current credit_os_run_id>",
  "cp0_sha256": "<SHA-256 of the current CP-0 Markdown bytes>",
  "authority_sha256": "<current verified authority bundle hash>",
  "scope_type": "issuer",
  "scope_key": "<exact CP-0 issuer_id>",
  "subject_name": "<exact CP-0 issuer_name>",
  "decision_context": "Test the demand assumption before setting downside",
  "as_of_date": "2026-09-08",
  "time_horizon": "Next 12 months",
  "source_mode": "hybrid",
  "budget": "standard",
  "authorization_basis": "Existing task instruction to research this issuer and question",
  "exclusions": "No confidential inputs in public searches; no trade recommendation",
  "questions": [
    {
      "question_id": "RQ-demand",
      "question": "Does independent evidence support the claimed end of destocking?",
      "decision_relevance": "Affects the downside demand assumption",
      "consumer_module_id": "CP-2A",
      "after_module_id": "CP-1",
      "evidence_needed": "Current customer, competitor and industry disclosures",
      "completion_test": "Evidence-weighted answer with contrary evidence and remaining uncertainty"
    }
  ]
}
```

Replace all illustrative scope/date/question values with the actual task. `authorization_basis` records existing authority; its presence never grants permissions. Inherit source mode and budget where already established. Verify actual source access before research. The standard budget allows two focused gap loops per question; extended allows three. One question is sufficient. Every question requires a nonempty decision relevance, evidence demand and completion test. The maximum is 32 questions in one bounded batch. A separate row with a unique question ID names each receiving module when the same issue affects multiple owners.

The brief adds only CP-DR, using reserved occurrence stage 99 on ordinary routes; 99 is an identity slot, never execution order. It cannot add other unselected modules. `after_module_id` and `consumer_module_id` must be selected canonical owners. Cycles are rejected. For an anchored DEEP_RESEARCH / LITE_DEEP_RESEARCH route ending at CP-DR itself, use consumer `NONE` and predecessor `CP-0`.

A current brief inserts CP-DR even when the earlier CP-0 T8 did not select it. An explicit CP-DR T8 row requires a brief. Its source readiness still applies; a new brief-based insertion proceeds only after the host resolves scope and research access under existing authorization. Mandatory predecessor and consumer edges enforce placement. When research locates missing sources before CP-1, use predecessor CP-0 and consumer CP-1. Research never overrides CP-0 source readiness. If newly located material changes its effective source inventory or a consumer's BLOCKED source gate, reassess CP-0 before extraction and issue a brief against the new anchor. This is an intake correction, not an automatic refresh for every research finding. A blocked CP-0 cannot be bypassed in linked mode; standalone research can gather leads to support a corrected intake.

## Late questions and revisions

A late CP-5/CP-6 challenge records the requesting artifact and question in `decision_relevance`. Name a factual predecessor that does not depend on the challenged consumer; never add consumer → CP-DR → consumer. Preserve the CP-0 anchor, existing route occurrence IDs and unaffected handoffs. Add or revise the bounded brief, retain relevant prior questions and findings, and rerun CP-DR with the next attempt ordinal. Archive superseded artifacts outside the active snapshot; two current attempts are ambiguous.

Hashing is conservative at dossier/batch level: changed research invalidates every consumer declared for that batch and their dependents, not unrelated modules. It does not promise individual-claim caching. If placement requirements form a cycle, replan against independent underlying sources or use a separate standalone follow-up whose findings enter through the receiving owner's source checks. Do not discard a genuine prerequisite to force scheduling. This runtime supports one linked research occurrence per run; independent multi-batch scheduling would require separately versioned occurrences. A changed CP-0 or authority requires a newly anchored brief.

## Invocation and research output

Use `prepare_invocation.py` with the current snapshot. It emits exact identity, upstream hashes, `research_mode`, scope fields and `approved_plan_hash`. The plan hash is `sha256:` plus SHA-256 of the brief serialized with sorted keys, compact separators and UTF-8 (`ensure_ascii=False`). Preserve this value; do not hash a prose rendering.

Author one canonical CP-DR Markdown handoff. Under its analytical appendix, emit these headings and immediately tagged tables:

- **TDR.1**, tag `<!-- table-id: cpdr.questions -->`: `question_id`, `question`, `decision_relevance`, `consumer_module_id`, `after_module_id`, `evidence_needed`, `completion_test`. Rows match the locked brief exactly and in order.
- **TDR.2**, tag `<!-- table-id: cpdr.evidence -->`: `evidence_id`, `question_id`, `claim`, `claim_type`, `source`, `source_locator`, `source_date`, `source_type`, `independence_family`, `entity_period_unit_perimeter`. Use ISO source dates and actual file/URL locators. `claim_type` is fact / source_characterisation / inference / analyst_judgment; `source_type` is primary / independent_secondary / attributed_view / gap. A gap row explicitly states what was unavailable, where/how it was sought and its limitation; it never supplies factual support.
- **TDR.3**, tag `<!-- table-id: cpdr.findings -->`: `question_id`, `answer`, `evidence_ids`, `contrary_evidence`, `resolution_status`, `uncertainty`, `proposed_consequence`. Evidence IDs are semicolon-separated. Record exactly one ANSWERED or UNRESOLVED row per question. Contrary evidence needs locators or an explicit account of the disconfirming search and absence of a finding; empty text is invalid.

ANSWERED requires primary evidence, two independent credible source families, or an answer explicitly limited to an attributed party's view. Treat source classification as an analyst judgment subject to CP-5 review, not a fact established by a URL count. Unknown evidence IDs and cross-question citations are rejected. Numeric claims state entity, period, unit and perimeter. The validator checks structure, relationships and declared evidence classes; actual source retrieval and source truth remain analytical responsibilities.

Coverage = ANSWERED questions / all locked questions × 100, rounded half up. Report Complete only at full coverage; otherwise Complete with Gaps. Never remove difficult questions after searching. UNRESOLVED questions block their named consumers while independent work continues. Record a genuinely blocked research run as Blocked; it remains unaccepted as downstream evidence.

## Consumer adoption

The receiving owner's invocation output provides `research_adoption_rows`. Complete the following tagged table in that owner's appendix:

`<!-- table-id: cpdr.adoptions -->`

| question_id | research_sha256 | disposition | reason | analytical_effect |
| --- | --- | --- | --- | --- |
| RQ-demand | current research file hash | ACCEPTED / REJECTED / QUALIFIED | Explain the evidence judgment | Explain the actual assumption/conclusion affected, or why unchanged |

Use one actual enum value and one row per assigned question. Placeholder rows are not completion. A rejection still records the reason and effect. CP-DR supplies evidence and proposed implications; the receiving owner validates applicability and controls extraction, assumptions, scoring and decisions. Any changed receiving handoff then invalidates its own dependents through normal lineage rules.

## Standalone issuer or sector research

Use the same brief with `mode: standalone`, a fresh run ID, scope_type issuer or sector, the appropriate scope_key and consumer/predecessor `NONE`. Omit CP-0 and authority anchor fields. Run the invocation helper with `--research-brief <brief.json> --reporting-period <period>`, without an issuer-run snapshot/profile/selection. No CP-0 is required; do not manufacture one. The Markdown uses its scope key in its filename and carries no issuer-workflow invocation envelope. Research registers and substantive QA remain identical.

A standalone dossier is external source evidence when later admitted to an issuer run: the receiving owner records its hash, scope, as-of and relevant evidence locators in its source registry and checks applicability. It is never silently substituted for a same-run analytical producer.

## Validation

Run CP-DR's `scripts/validate_research.py --brief <brief.json> --handoff <canonical.md>`. For linked mode also supply `--snapshot <fresh-snapshot.json>` containing the exact handoff, CP-0, required current predecessors and current brief. Generic Markdown validation alone does not establish research completeness. All navigation, reconciliation and memo acceptance use these research relationships through their shared acceptance function.

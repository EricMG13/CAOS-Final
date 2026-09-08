<!-- CP-1A Schema Reference (Tier 3) | 2026-06-02 -->
<schema_reference module="CP-1A" tier="3">
## Output Objects
| ID | Step | Purpose |
|----|------|---------|
| source_classification | 2 | Source quality |
| transaction_summary | 3 | Transaction terms |
| company_description | 4 | Business description |
| revenue_business_mix | 4 | Revenue breakdown |
| ownership_register | 5 | Ownership structure |
| operating_model | 6 | Operating metrics |
| cp1a.cp_model_snapshot_fields | 10 | Six source-grounded workbook display fields, emitted on every run |
| events_timeline | 7 | Credit events |
| credit_translation | 8 | Risk synthesis |
| gaps_ledger | 9 | Data gaps |
| conflict_log | 9 | Source conflicts |
| downstream_readiness | 10 | Module readiness |

## CP-MODEL projection profile

`cp1a.cp_model_snapshot_fields` is emitted on every run and contains
exactly one `READY` row for each of `issuer_name`, `sector`, `country`,
`shareholders`, `transaction_summary` and `business_description`. Columns are
`field_id | value | status | source_id | source_locator | as_of`. It is a
lossless workbook display projection of CP-1A facts, not a replacement for the
other output objects.
## Extraction Types (13): sourced_fact | quoted_text | table_value | calculated_metric | analyst_inference | upstream_artifact | user_instruction | documentary_fact | definition_conflict | gap | source_limitation | insufficient_information | not_available
## QA: Sources classified | Objects present | Chains complete | Separation maintained | No M-prefix | Audit Appendix present (single, all audit items) | No silent reconciliation | Gaps inline+ledger | Mgmt language labelled
## Export

The required analytical output and sole downstream handoff is one validated canonical Markdown file. Other analytical export formats are prohibited.

**Output order: (1) author the complete canonical Markdown handoff; (2) validate contract and identity fail-closed; (3) return concise status, limitations, recommended next command, and the Markdown link.**

## canonical Markdown [IssuerID]_CP-1A_[YYYYMMDD].md — `IssuerID` is exact front-matter `issuer_id`; `YYYYMMDD` is `analysis_date` without hyphens. YAML envelope (incl confidence_score + confidence_band) + canonical H2: ## Audit Summary, ## Analysis, ## Evidence Trace, ## Source Registry, ## Gaps & Conflicts, ## QA Validation. Saved to OneDrive, attached as grounding to next agent.
## Confidence: numeric confidence_score 0-100 (primary, per CP_CONFIDENCE_SCORE.md); confidence_band = derived label (High/Medium/Low/Insufficient Information).
</schema_reference>

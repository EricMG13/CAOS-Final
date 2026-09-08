# CP LITE Analysis Policy v1

Status: authored, versioned authority. Scope: Deploy V CP-L screening modules only.

Every CP-L invocation completes its own screening schema. It is not a shortened FULL-module execution. `decision_scope` is always `SCREENING_ONLY`. Output depth, length, claim count, metric count, reference count, and execution budget are not capped by this authority; the available evidence and the user's task determine how much useful analysis is warranted. Missing or weak topic evidence normally yields `COMPLETE_WITH_GAPS`; only missing or ambiguous subject identity, or an invalid artifact, yields `BLOCKED_IDENTITY`.

## Normative constants

The JSON block below is the machine-readable authority. Runtime code and child schemas must validate a structured field against these values; prose, filenames, and inferred intent are inert.

```json
{
  "decision_scope": "SCREENING_ONLY",
  "screen_statuses": ["COMPLETE", "COMPLETE_WITH_GAPS", "BLOCKED_IDENTITY"],
  "execution_basis_values": ["SOURCE_DIRECT", "UPSTREAM_HANDOFFS", "MIXED"],
  "output_limits": "UNSPECIFIED_BY_LITE_AUTHORITY",
  "filler_forbidden": true,
  "required_topic_fields": [
    "topic_id",
    "source_owner_modules",
    "materiality",
    "evidence_status",
    "disposition",
    "priority_rank",
    "summary",
    "source_refs",
    "upgrade_module_ids"
  ],
  "materiality_values": ["HIGH", "MEDIUM", "LOW", "NOT_ASSESSABLE"],
  "evidence_status_values": ["SUFFICIENT", "PARTIAL", "MISSING", "CONFLICTED"],
  "disposition_values": ["DEEPEN", "SUMMARIZE", "GAP_ONLY", "IMMATERIAL"],
  "disposition_guidance": {
    "DEEPEN": {"analysis_depth": "evidence_proportionate", "upgrade_recommended": true},
    "SUMMARIZE": {"analysis_depth": "evidence_proportionate", "upgrade_recommended": true},
    "GAP_ONLY": {"analytical_conclusion_allowed": false, "required_content": ["missing_evidence", "decision_impact", "required_source", "full_upgrade_module"]},
    "IMMATERIAL": {"affirmative_evidence_required": true}
  },
  "missing_evidence_may_be_immaterial": false,
  "high_missing_or_conflicted_rule": {"disposition": "GAP_ONLY", "source_gate_status": "PARTIAL"},
  "ranking_order": ["urgency", "downside_magnitude", "evidence_confidence", "canonical_topic_order"],
  "upgrade_outcomes": ["LITE_COMPLETE", "FULL_UPGRADE_RECOMMENDED", "FULL_UPGRADE_REQUIRED"],
  "upgrade_activation": "SCHEMA_VALIDATED_STRUCTURED_DATA_ONLY"
}
```

## Evidence-proportionate analysis

Classify every topic, rank attention by urgency, downside magnitude, evidence confidence, and canonical topic order, then spend as much analytical effort as the evidence and task require. `DEEPEN` is for decision-material, uncertain, conflicted, or transmitting topics with enough evidence to analyze. `SUMMARIZE` is a concise treatment when the topic is relevant but does not warrant the same emphasis. These are qualitative dispositions, not output quotas. There is no fixed number of deepened topics, no fixed word or token ceiling, and no fixed claim, metric, reference, or unit budget. Do not add filler; continue until the decision-useful screen is complete or the evidence boundary is reached.

`GAP_ONLY` contains no analytical conclusion. It names the missing evidence, decision impact, required source, and target FULL upgrade module. A `HIGH` topic with `MISSING` or `CONFLICTED` evidence must be `GAP_ONLY` and must set the source gate to `PARTIAL`.

`IMMATERIAL` requires affirmative evidence of no meaningful credit transmission. Missing evidence can never justify `IMMATERIAL`.

## Structured upgrade boundary

Only a schema-valid structured outcome field may activate `LITE_COMPLETE`, `FULL_UPGRADE_RECOMMENDED`, or `FULL_UPGRADE_REQUIRED`. Free text, headings, filenames, and inferred user intent never activate an upgrade. Profile upgrade remains governed by CP_DEPLOY_V_EXECUTION_PROFILES_v1.json: it creates a user-confirmed linked `FULL_CREDIT_32` run and never changes the current run's immutable profile.

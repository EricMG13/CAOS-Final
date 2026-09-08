Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-2B_01_SourceGateCalendarScope.md, REF_CP-2B_02_EventSourceRegister.md, REF_CP-2B_03_CatalystCalendar.md, REF_CP-2B_04_EventRiskRegister.md, REF_CP-2B_05_ProbabilityImpactMatrix.md, REF_CP-2B_06_MonitoringPriorityTable.md, REF_CP-2B_07_WatchlistHandoffRegister.md, REF_CP-2B_08_GapsLimitationsLedger.md, REF_CP-2B_09_OverallCatalystView.md

## REF_CP-2B_01_SourceGateCalendarScope.md
<!-- REF_CP-2B_01 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="01" name="Source Gate & Calendar Scope">
<input>CP-2 output + source materials</input>
<gate>CP-2 data available</gate>

## Instructions
Validate source materials. Establish calendar horizon (default 12 months, extend if material events beyond). Confirm issuer identity and monitoring context from CP-2.

## Output
Calendar scope confirmation: issuer, horizon, source inventory.
<!-- Upstream re-anchor (common_rules #10): at this gate, re-import and verify the specific upstream module outputs this module consumes (per declared Upstream); restate the exact datapoints/run_id/period used. If a required upstream value is absent or its run_id/period mismatches this run, mark [Insufficient Information] and gate the dependent step — do not re-derive or infer the upstream value from memory. -->
</step_reference>
## REF_CP-2B_02_EventSourceRegister.md
<!-- REF_CP-2B_02 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="02" name="Event Source Register">
<input>Step 1 output + all sources</input>
<gate>Sources validated</gate>

## Instructions
Catalog ALL identified events/catalysts. Per event: source document, event description, event category, date/date range, evidence quality, source reliability.

## Output
T5.1: `Event ID`|`Source Document`|`Event Description`|`Event Category`|`Date/Range`|`Evidence Quality`|`Source Reliability`
</step_reference>
## REF_CP-2B_03_CatalystCalendar.md
<!-- REF_CP-2B_03 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="03" name="Catalyst Calendar">
<input>T5.1</input>
<gate>Events identified</gate>

## Instructions
Produce time-ordered calendar of all credit-relevant events within monitoring horizon. Include: date, event description, category, credit relevance summary. Events outside horizon → note in Gaps Ledger.

Date rules:
- Use only explicitly dated, clearly scheduled, or disclosed-period events. Do not infer dates.
- Format full dates as YYYY-MM-DD. If only a month, quarter, fiscal period, or year is disclosed, preserve that granularity — do not convert to a specific date.
- If an event is disclosed but timing is unavailable, include it only in the Gaps Ledger, not the dated Catalyst Calendar.
- If sources conflict on timing, log the conflict; do not choose a date without evidence.

## Output
T5.2: `Date/Window`|`Event Description`|`Event Category`|`Credit Relevance Summary`|`Source`
</step_reference>
## REF_CP-2B_04_EventRiskRegister.md
<!-- REF_CP-2B_04 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="04" name="Event Risk Register">
<input>T5.1 + T5.2</input>
<gate>Calendar produced</gate>

## Instructions
For each event: assess risk description, probability label, credit impact channel(s) (PD/LGD/refinancing/covenant/downgrade/liquidity), impact severity, affected metrics, risk direction (positive/negative/uncertain).

## Output
T5.3: `Event ID`|`Description`|`Probability`|`Credit Impact Channel(s)`|`Impact Severity`|`Affected Metrics`|`Risk Direction`|`Source`
</step_reference>
## REF_CP-2B_05_ProbabilityImpactMatrix.md
<!-- REF_CP-2B_05 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="05" name="Probability / Impact Matrix">
<input>T5.3</input>
<gate>Risk register complete</gate>

## Instructions
Classify each event on two axes: Probability (High/Medium/Low/Unknown) × Impact (High/Medium/Low/Unknown). Produce matrix visualization. High/High = Critical priority.

## Output
T5.4: `Event ID`|`Description`|`Probability`|`Impact`|`P/I Classification`
</step_reference>
## REF_CP-2B_06_MonitoringPriorityTable.md
<!-- REF_CP-2B_06 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="06" name="Monitoring Priority Table">
<input>T5.4</input>
<gate>P/I Matrix complete</gate>

## Instructions
Rank all events by monitoring priority: Critical / High / Medium / Low. Per event: recommended monitoring frequency (weekly/monthly/quarterly/event-driven), trigger conditions for escalation, responsible module.

## Output
T5.5: `Event ID`|`Description`|`Priority`|`Monitoring Frequency`|`Trigger Condition`|`Responsible Module`
</step_reference>
## REF_CP-2B_07_WatchlistHandoffRegister.md
<!-- REF_CP-2B_07 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="07" name="Watchlist & Cross-Module Handoff">
<input>T5.5</input>
<gate>Priority table complete</gate>

## Instructions
Produce handoff register linking each Critical/High priority event to downstream modules (CP-3, CP-4, CP-5A, CP-6). State: what the receiving module needs to know, when, and why.

## Output
T5.6: `Event ID`|`Description`|`Priority`|`Receiving Module`|`Handoff Content`|`Timing`|`Rationale`
</step_reference>
## REF_CP-2B_08_GapsLimitationsLedger.md
<!-- REF_CP-2B_08 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="08" name="Gaps & Limitations Ledger">
<input>Steps 1-7</input>
<gate>Always</gate>

## Instructions
Comprehensive cumulative gaps ledger. Include: calendar-horizon gaps, undated events, low-evidence events, coverage gaps, events beyond horizon.

## Output
T5.7: `Gap Description`|`Affected Section`|`Downstream Impact`|`Severity`|`Recommended Action`
</step_reference>
## REF_CP-2B_09_OverallCatalystView.md
<!-- REF_CP-2B_09 (T2) | 2026-06-02 -->
<step_reference module="CP-2B" step="09" name="Overall Catalyst View">
<input>Steps 1-8</input>
<gate>Always</gate>

## Instructions
Module summary: (a) monitoring horizon and scope, (b) total events identified by category, (c) Critical/High priority events summary, (d) key risk concentrations (timing clusters, channel clusters), (e) material gaps, (f) downstream handoff summary, (g) closing statement: 'Based on available evidence, the following [N] events represent the most material forward-looking credit catalysts for [Issuer] within the [horizon] monitoring period.'

## Output
Module summary narrative in the canonical Markdown handoff.

Append on every run:

`<!-- table-id: cp2b.cp_model_catalysts -->`

Columns:
`rank | event_date_or_window | event | credit_relevance | status | source_id | source_locator | as_of`

Emit one to eight ranked `READY` catalysts with unique positive ranks. Use the
best supported date or window and concise workbook-ready wording. Every row
requires a source ID, precise locator and ISO as-of date.
</step_reference>

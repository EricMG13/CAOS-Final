Consolidated method bundle. Each section below is one original file, byte-identical, under its own `## <filename>` heading.

Apply step sections (`## REF_..._<NN>_*`) when their workflow step begins. Prefer retrieval of the named section. If the connector only supports whole-file access, open this bundle once and apply only the active/named sections, reusing the content within the current run; no user extraction or separate-file setup is required.

Original files, in this bundle: REF_CP-4C_A_DistressAndJurisdictionGate.md, REF_CP-4C_B_ClaimsValueAndPriorityLock.md, REF_CP-4C_C_RestructuringPathEngine.md, REF_CP-4C_D_FulcrumAndRecovery.md, REF_CP-4C_E_DecisionHandoff.md, REF_CP-4C_F_OutputAndQA.md

## REF_CP-4C_A_DistressAndJurisdictionGate.md
# CP-4C A — Distress and jurisdiction gate

Accept only a named, evidenced distress trigger: missed/likely missed payment, going-concern or liquidity warning, failed/closed refinancing, distressed exchange, covenant/enforcement event, adviser engagement, restructuring filing, creditor group formation or equivalent source-supported escalation. Low bond price alone is not sufficient.

Identify incorporation, centre of main interests, obligor/guarantor jurisdictions, governing law, venue/process and cross-border recognition issues only from reliable sources. A general description of a jurisdiction is not a case-specific legal conclusion.

If no gate is met, return `Not Applicable` with the evidence reviewed. If jurisdiction or controlling documents are necessary but unavailable, Block rather than invent process rights.

## REF_CP-4C_B_ClaimsValueAndPriorityLock.md
# CP-4C B — Claims, value and priority lock

Build claims by legal entity and class. Separate funded principal, accrued interest, PIK/capitalised amounts, lease/pension/tax/employee/administrative claims, guarantees, intercompany claims, contingent/disputed claims and new-money/DIP claims. Do not add a guaranteed claim at multiple entities without eliminating double recovery.

Use CP-4/4D for legal priority and security/guarantee reach. Use CP-3A for ordinary recovery assumptions but rebuild the waterfall when the restructuring scenario changes claims or priority. Record valuation date, cash retained, transaction costs and priority deductions.

Every enterprise-value case identifies methodology, operating metric/cash flow, multiple/discount rate, perimeter and whether the value is sourced, calculated or analyst judgment.

## REF_CP-4C_C_RestructuringPathEngine.md
# CP-4C C — Restructuring path engine

Construct paths from available liquidity, maturity/enforcement timing, creditor classes, consent thresholds, legal capacity, sponsor incentives and market/new-money access. Do not list every theoretical process; include only paths credible for the case.

For each path show prerequisites, class treatment, new-money requirement, priority/priming effect, releases, governance/equity outcome, key votes/consents, milestones, execution blockers and fallback. Separate a consensual refinancing, ordinary exchange, distressed exchange/LME and formal proceeding.

Path likelihood uses the canonical ordinal classes. It is not a legal prediction. Conflicting evidence remains in the register and may produce multiple credible paths.

## REF_CP-4C_D_FulcrumAndRecovery.md
# CP-4C D — Fulcrum and recovery

Use low/base/high enterprise values and show sensitivity to both operating metric/cash flow and valuation multiple/discount rate. Deduct supported administrative, DIP/new-money, secured priority and transaction costs in the order supported by governing evidence. Allocate residual value by entity and class.

Identify the fulcrum as the class receiving the marginal reorganised equity/value after senior claims. When priority, valuation or intercompany recoveries are uncertain, show a fulcrum range rather than one security.

Recovery must separate cash, reinstated debt, new debt, equity and warrants/options; state timing and discount assumptions. Do not compare recovery percentages across classes without aligned claim basis and currency.

## REF_CP-4C_E_DecisionHandoff.md
# CP-4C E — Decision handoff

Summarise the distress gate, primary and alternative paths, likely fulcrum range, class outcomes, new-money/priming risk, controlling legal/value uncertainties and next dated catalyst. Explain what evidence would move the fulcrum or path assessment.

CP-6 receives competing case arguments and the most decision-relevant uncertainty. CP-6A receives portfolio/implementation consequences only after CP-3B inputs exist.

Do not provide legal advice, direct negotiation tactics, certainty of court outcome or a trade/position recommendation.
## REF_CP-4C_F_OutputAndQA.md
# CP-4C F — Output and QA

Required QA tests:

1. A documented distress gate and correct issuer/jurisdiction are present.
2. Claims reconcile by entity/class and guaranteed claims are not double counted.
3. Security, guarantee and priority conclusions trace to CP-4/4D or controlling evidence.
4. Enterprise value cases expose metric, multiple/discount, perimeter and judgment.
5. Each path has prerequisites, class treatment, new money, milestones and blockers.
6. Waterfalls roll without negative/unallocated unexplained value.
7. Fulcrum and recovery ranges remain sensitive to legal and valuation uncertainty.
8. No legal advice, process certainty, probability, recovery or recommendation is fabricated.
9. Markdown contract validation and semantic/numerical checks pass.

The Analysis section contains T4E.1–T4E.10. Evidence Trace records claim, legal, valuation and formula lineage. Gaps & Conflicts names unresolved evidence and affected scenarios/classes. QA Validation reports each test and final status.

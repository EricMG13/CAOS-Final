"""Structural research workflow checks; the sample claims are test data only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

import test_module_workflow as base
from test_module_workflow import ROOT, CAT, AUTH, RUN, table, yaml_fields, scenario, navigate, inventory, prepare
from completeness_check import load_contract
from validate_handoff import validate_text, CANONICAL_HEADINGS
from credit_os_v import navigation, routing, research
from credit_os_v.reconcile import reconcile, canonical_handoff_content, ReconcileError


def brief_for(snapshot, consumer='CP-2A', after='CP-1'):
    return dict(schema=research.SCHEMA,mode='linked',run_id=RUN,
        cp0_sha256=hashlib.sha256(snapshot['EXAMPLE_CP-0_20260908.md'].encode()).hexdigest(),authority_sha256=AUTH,
        scope_type='issuer',scope_key='EXAMPLE',subject_name='Example',decision_context='Test the forecast premise',
        as_of_date='2026-09-08',time_horizon='Next 12 months',source_mode='supplied_only',budget='standard',
        authorization_basis='Current user research instruction',exclusions='No scope expansion',questions=[dict(
            question_id='RQ-demand',question='Is demand recovering?',decision_relevance='Changes the downside assumption',
            consumer_module_id=consumer,after_module_id=after,evidence_needed='Independent primary demand evidence',
            completion_test='Supported answer with contrary evidence and uncertainty')])


def add_brief(snapshot, brief):
    snapshot[f'RESEARCH_{RUN}.json']=json.dumps(brief)


def author(snapshot, module_id, *, brief=None, unresolved=False):
    # Use the real invocation preparer instead of duplicating dependency logic.
    kwargs=dict(artifacts=snapshot) if snapshot is not None else dict(research_brief=brief,reporting_period='FY2025')
    result=prepare(CAT,AUTH,module_id=module_id,issuer_id='EXAMPLE',analysis_date='2026-09-08',**kwargs)
    fields=result['frontmatter_fields']
    fields.update(issuer_name='Example',confidence_score=90,confidence_band='High',qa_status='Passed',
        committee_status='Draft Only',limitation_flags=[],validation_warnings=[],downstream_consumers=[])
    appendix='### Analytical appendix — complete canonical registers\n\n'
    if module_id=='CP-DR':
        brief=result['research_brief']
        fields.update(coverage_score=0 if unresolved else 100,research_status='Complete with Gaps' if unresolved else 'Complete',
                      research_stop_reason='sources_exhausted' if unresolved else 'coverage_satisfied')
        question_rows=[[q[c] for c in research.QUESTION_COLUMNS] for q in brief['questions']]
        evidence_rows=[[f'E-{i}',q['question_id'],'Demand evidence','fact','disclosure.md','p12','2026-09-01','gap' if unresolved else 'primary','Original issuer','Example / FY2025 / units / consolidated'] for i,q in enumerate(brief['questions'])]
        finding_rows=[[q['question_id'],'Bounded answer',f'E-{i}','Contrary evidence searched: customer disclosure p4','UNRESOLVED' if unresolved else 'ANSWERED','Residual uncertainty described','Owner reassesses demand assumption'] for i,q in enumerate(brief['questions'])]
        for rid,tid,cols,data in zip(('TDR.1','TDR.2','TDR.3'),('cpdr.questions','cpdr.evidence','cpdr.findings'),
                                    (research.QUESTION_COLUMNS,research.EVIDENCE_COLUMNS,research.FINDING_COLUMNS),(question_rows,evidence_rows,finding_rows)):
            appendix+=f'#### {rid}\n\n<!-- table-id: {tid} -->\n'+table(cols,data)+'\n'
    else:
        module=next(m for m in CAT['modules'] if m['module_id']==module_id)
        contract=load_contract((ROOT/module['skill_md']).read_text(),module_id)
        for reg,spec in contract['registers'].items():
            cols=spec['columns'] or ['Evidence']
            appendix+='#### '+reg+'\n\n'+table(cols,[['Recorded source p1']*len(cols)]*max(1,spec['minimum_body_rows']))+'\n'
        for tid in contract['unconditional_stable_tables']:
            appendix+='<!-- table-id: '+tid+' -->\n'+table(['source_locator'],[['Source p1']])+'\n'
        if result.get('research_adoption_rows'):
            data=[[r['question_id'],r['research_sha256'],'QUALIFIED','Primary evidence applies with scope limitations','Downside remains cautious'] for r in result['research_adoption_rows']]
            appendix+='<!-- table-id: cpdr.adoptions -->\n'+table(research.ADOPTION_COLUMNS,data)+'\n'
    body=''.join('## '+h+'\n\n'+(appendix if h=='Analysis' else 'Recorded source p1.\n\n') for h in CANONICAL_HEADINGS)
    text='---\n'+yaml_fields(fields)+'\n---\n'+body
    validated=validate_text(text,filename=result['filename'])
    assert validated.exit_code==0,validated.errors
    if snapshot is not None:snapshot[result['filename']]=text
    return result['filename'],text


class ResearchWorkflowTests(unittest.TestCase):
    def initial(self):
        _,snapshot=scenario(['CP-1','CP-2A','CP-3D'])
        del snapshot['EXAMPLE_CP-2A_20260908.md']
        brief=brief_for(snapshot);add_brief(snapshot,brief)
        return snapshot,brief

    def test_named_research_precedes_consumer_and_preserves_independent_work(self):
        snapshot,brief=self.initial()
        context=navigate(snapshot).discovery.contexts[0]
        order=[r.module_id for r in context.recommendations]
        self.assertLess(order.index('CP-1'),order.index('CP-DR'))
        self.assertLess(order.index('CP-DR'),order.index('CP-2A'))
        self.assertIn('CP-DR',context.blockers['CP-2A'])
        self.assertIn('CP-3D',context.completed)
        card=navigation.render_layer(context,navigation.validate_catalog(CAT),context.layers.index('CP-DR'))
        self.assertIn('RQ-demand for CP-2A: Is demand recovering?',card)
        self.assertNotIn('Layer L7',card)
        self.assertTrue(any('CP-DR' in warning for warning in navigation.skip_warnings(context,navigation.validate_catalog(CAT),context.layers.index('CP-DR'))))
        author(snapshot,'CP-DR');author(snapshot,'CP-2A')
        self.assertTrue({'CP-DR','CP-2A','CP-3D'} <= navigate(snapshot).discovery.contexts[0].completed)
        self.assertTrue(any(a.module_id=='CP-2A' and a.disposition=='ELIGIBLE' for a in inventory(snapshot).artifacts))

    def test_early_source_research_before_extraction(self):
        _,snapshot=scenario(['CP-1','CP-2'])
        del snapshot['EXAMPLE_CP-1_20260908.md'];del snapshot['EXAMPLE_CP-2_20260908.md']
        brief=brief_for(snapshot,'CP-1','CP-0');add_brief(snapshot,brief)
        fields=prepare(CAT,AUTH,module_id='CP-DR',issuer_id='EXAMPLE',analysis_date='2026-09-08',artifacts=snapshot)
        self.assertEqual(fields['dependency_order'],['CP-0','CP-DR','CP-1','CP-2'])
        author(snapshot,'CP-DR');author(snapshot,'CP-1');author(snapshot,'CP-2')
        self.assertIn('CP-2',navigate(snapshot).discovery.contexts[0].completed)

    def test_late_question_keeps_cp0_and_existing_occurrence_ids(self):
        _,snapshot=scenario(['CP-1','CP-2A','CP-3D'])
        cp0=snapshot['EXAMPLE_CP-0_20260908.md']
        old=validate_text(snapshot['EXAMPLE_CP-2A_20260908.md']).fields['credit_os_route_node_id']
        brief=brief_for(snapshot);add_brief(snapshot,brief)
        self.assertEqual(snapshot['EXAMPLE_CP-0_20260908.md'],cp0)
        self.assertEqual(navigate(snapshot).discovery.contexts[0].completed,{'CP-1','CP-3D'})
        author(snapshot,'CP-DR')
        name,text=author(snapshot,'CP-2A')
        self.assertEqual(validate_text(text).fields['credit_os_route_node_id'],old)

    def test_unresolved_answer_blocks_only_assigned_consumer(self):
        snapshot,brief=self.initial();author(snapshot,'CP-DR',unresolved=True)
        context=navigate(snapshot).discovery.contexts[0]
        self.assertIn('Unresolved research',context.blockers['CP-2A'])
        self.assertIn('CP-3D',context.completed)
        with self.assertRaisesRegex(ValueError,'unresolved research'):
            author(snapshot,'CP-2A')

    def test_research_changes_and_missing_adoption_reject_consumers(self):
        snapshot,brief=self.initial();author(snapshot,'CP-DR');name,text=author(snapshot,'CP-2A')
        snapshot[name]=text.replace('<!-- table-id: cpdr.adoptions -->','<!-- no adoption register -->')
        context=navigate(snapshot).discovery.contexts[0]
        self.assertNotIn('CP-2A',context.completed)
        self.assertIn('cpdr.adoptions',context.problems[name])
        snapshot[name]=text;snapshot['EXAMPLE_CP-DR_20260908.md']+='Changed evidence p3.\n'
        self.assertEqual(navigate(snapshot).discovery.contexts[0].completed,{'CP-1','CP-DR','CP-3D'})

    def test_dropped_question_and_false_coverage_are_rejected(self):
        snapshot,brief=self.initial();name,text=author(snapshot,'CP-DR')
        snapshot[name]=text.replace('coverage_score: 100','coverage_score: 99')
        self.assertIn('coverage_score',navigate(snapshot).discovery.contexts[0].problems[name])
        snapshot[name]=text.replace('RQ-demand | Is demand recovering?','RQ-other | Is demand recovering?')
        self.assertIn('locked coverage denominator',navigate(snapshot).discovery.contexts[0].problems[name])
        snapshot[name]=text.replace('<!-- table-id: cpdr.evidence -->','<!-- omitted evidence register -->')
        self.assertIn('cpdr.evidence',navigate(snapshot).discovery.contexts[0].problems[name])

    def test_invalid_brief_and_cycle_fail_closed(self):
        snapshot,brief=self.initial()
        for field,value in [('cp0_sha256','b'*64),('scope_key','OTHER')]:
            bad=copy.deepcopy(brief);bad[field]=value;add_brief(snapshot,bad)
            self.assertEqual(navigate(snapshot).status,'NO_CP0')
        bad=copy.deepcopy(brief);bad['questions'][0]['after_module_id']='CP-2A';add_brief(snapshot,bad)
        self.assertIn('cycle',navigate(snapshot).card)
        bad=copy.deepcopy(brief);bad['questions'][0]['consumer_module_id']='CP-4';add_brief(snapshot,bad)
        self.assertIn('selected analytical owners',navigate(snapshot).card)

    def test_standalone_sector_needs_no_cp0(self):
        _,snapshot=scenario(['CP-3D'],'MARKET_DISLOCATION')
        brief=brief_for(snapshot);brief.update(mode='standalone',scope_type='sector')
        del brief['cp0_sha256'];del brief['authority_sha256']
        brief['questions'][0].update(consumer_module_id='NONE',after_module_id='NONE')
        name,text=author(None,'CP-DR',brief=brief)
        candidate=navigation.validate_artifacts({name:text})[0]
        research.validate_dossier(candidate,research.validate_brief(brief))
        self.assertNotIn('credit_os_run_id',candidate.fields)

    def test_reconciliation_matches_navigation_with_research_control(self):
        snapshot,brief=self.initial();author(snapshot,'CP-DR');author(snapshot,'CP-2A')
        entries=[SimpleNamespace(name=name) for name in snapshot]
        source=SimpleNamespace(list=lambda:SimpleNamespace(entries=entries,rejected=[]),
            read=lambda entry:SimpleNamespace(data=snapshot[entry.name].encode(),sha256=hashlib.sha256(snapshot[entry.name].encode()).hexdigest()))
        for parser in (None,canonical_handoff_content):
            view=reconcile(source,catalog=CAT,current_authority_sha256=AUTH,require_stability=False,content_parser=parser)
            self.assertEqual({a.module_id for a in view.accepted()},{'CP-0','CP-1','CP-DR','CP-2A','CP-3D'})
        snapshot[f'RESEARCH_{RUN}.json']='{'
        with self.assertRaises(ReconcileError):
            reconcile(source,catalog=CAT,current_authority_sha256=AUTH,require_stability=False)

    def test_research_does_not_override_blocked_source_readiness(self):
        _,snapshot=scenario(['CP-1'])
        cp0='EXAMPLE_CP-0_20260908.md'
        snapshot[cp0]=snapshot[cp0].replace('| CP-1 | Run CP-1 | Run CP-1 | Source p1 | Current handoff | READY | Relevant source p1 |',
            '| CP-1 | Run CP-1 | DO NOT RUN | Source p1 | Current handoff | BLOCKED | Missing full filing |')
        del snapshot['EXAMPLE_CP-1_20260908.md']
        brief=brief_for(snapshot,'CP-1','CP-0');add_brief(snapshot,brief)
        author(snapshot,'CP-DR')
        with self.assertRaisesRegex(ValueError,'not source-ready'):
            author(snapshot,'CP-1')

    def test_lite_accepts_a_named_research_extension(self):
        route=routing.Route(CAT,'LITE_CREDIT_22','LITE_FULL_CREDIT_SCREEN')
        order=[n['module_id'] for n in route.nodes if n['module_id']!='CP-0']
        brief={'questions':[{'after_module_id':'CP-L10','consumer_module_id':'CP-2A'}]}
        routed=routing.Route(CAT,'LITE_CREDIT_22','LITE_FULL_CREDIT_SCREEN',order+['CP-DR'],research_brief=brief)
        ids=[n['module_id'] for n in routed.nodes]
        self.assertLess(ids.index('CP-L10'),ids.index('CP-DR'));self.assertLess(ids.index('CP-DR'),ids.index('CP-2A'))

    def test_evidence_links_dates_and_adoption_placeholders_fail_closed(self):
        snapshot,brief=self.initial();name,text=author(snapshot,'CP-DR')
        for bad in (text.replace('| E-0 | Contrary evidence','| MISSING | Contrary evidence'),
                    text.replace('| 2026-09-01 | primary |','| 2027-09-01 | primary |'),
                    text.replace('| primary |','| independent_secondary |')):
            snapshot[name]=bad
            self.assertNotIn('CP-DR',navigate(snapshot).discovery.contexts[0].completed)
        snapshot[name]=text
        name,text=author(snapshot,'CP-2A')
        snapshot[name]=text.replace('Primary evidence applies with scope limitations','REQUIRES_ANALYST_DECISION')
        self.assertNotIn('CP-2A',navigate(snapshot).discovery.contexts[0].completed)

    def test_public_clis_validate_linked_and_standalone_research(self):
        from unittest.mock import patch
        authority=json.loads((ROOT/'skills/cp-os-credit-os/references/CREDIT_OS_V_AUTHORITY_BUNDLE_v2.json').read_text())['authority_bundle_sha256']
        with patch.object(base,'AUTH',authority),patch.object(sys.modules[__name__],'AUTH',authority):
            snapshot,brief=self.initial();name,text=author(snapshot,'CP-DR');author(snapshot,'CP-2A')
            with tempfile.TemporaryDirectory() as scratch:
                work=Path(scratch);brief_path=work/'brief.json';brief_path.write_text(json.dumps(brief))
                (work/name).write_text(text)
                snap=work/'snapshot.json';snap.write_text(json.dumps({'artifacts':snapshot}))
                validator=ROOT/'skills/cp-dr-deep-research/scripts/validate_research.py'
                result=subprocess.run([sys.executable,'-B',str(validator),'--brief',str(brief_path),'--handoff',str(work/name),'--snapshot',str(snap)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                oversized=dict(snapshot,**{f'ignored-{n}.md':'' for n in range(257)})
                snap.write_text(json.dumps({'artifacts':oversized}))
                result=subprocess.run([sys.executable,'-B',str(validator),'--brief',str(brief_path),'--handoff',str(work/name),'--snapshot',str(snap)],text=True,capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('artifact count limit',result.stdout)
                snap.write_text(json.dumps({'artifacts':snapshot}))
                result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/cp-os-credit-os/scripts/credit_os_v_cli.py'),'navigate'],input=snap.read_text(),text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'],'SHOW_LAYER')
                snap.write_text(json.dumps({'artifacts':[{'name':n,'text':t} for n,t in snapshot.items()]}))
                result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/cp-memo-credit-research-report/scripts/export_cp_memo.py'),'inventory',str(snap)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'],'READY')
                brief.update(mode='standalone',scope_type='sector')
                brief.pop('cp0_sha256');brief.pop('authority_sha256')
                brief['questions'][0].update(consumer_module_id='NONE',after_module_id='NONE')
                brief_path.write_text(json.dumps(brief))
                result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/cp-os-credit-os/scripts/prepare_invocation.py'),
                    '--module-id','CP-DR','--analysis-date','2026-09-08','--reporting-period','FY2025','--research-brief',str(brief_path)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertNotIn('credit_os_run_id',json.loads(result.stdout)['frontmatter_fields'])
                name,text=author(None,'CP-DR',brief=brief);(work/name).write_text(text)
                result=subprocess.run([sys.executable,'-B',str(validator),'--brief',str(brief_path),'--handoff',str(work/name)],text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

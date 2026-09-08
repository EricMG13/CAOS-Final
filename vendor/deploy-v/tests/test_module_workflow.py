"""Structural regression scenarios; these documents are not issuer analysis."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'skills/cp-os-credit-os/scripts'),str(ROOT/'skills/cp-memo-credit-research-report/scripts')]
from credit_os_v import envelope, navigation, routing, render
from credit_os_v.handoffs import accept_snapshot
from completeness_check import load_contract
from validate_handoff import validate_text, CANONICAL_HEADINGS
from cp_memo.inventory import inventory_snapshot
from prepare_invocation import prepare

AUTH='a'*64
RUN='COS-20260908T120000Z-'+'1'*32
CAT=json.loads((ROOT/'skills/cp-os-credit-os/references/CREDIT_OS_V_MODULE_CATALOG_v2.json').read_text())


def table(columns, rows):
    return '| '+' | '.join(columns)+' |\n| '+' | '.join('---' for _ in columns)+' |\n'+''.join('| '+' | '.join(row)+' |\n' for row in rows)+'\n'


def yaml_fields(fields):
    # The restricted parser deliberately rejects JSON-style quoted mapping keys.
    lines=[]
    for key,value in fields.items():
        if isinstance(value,list) and value and isinstance(value[0],dict):
            lines.append(key+':')
            for item in value:
                for n,(k,v) in enumerate(item.items()):
                    lines.append(('  - ' if n==0 else '    ')+k+': '+json.dumps(v))
        else:
            lines.append(key+': '+json.dumps(value))
    return '\n'.join(lines)


def artifact(module_id, route, accepted, records, recommendations, omit_prefix=None):
    node=route.by_module[module_id]
    filename=f'EXAMPLE_{module_id}_20260908.md'
    upstream=routing.expected_upstream_digests(route,node['route_node_id'],accepted)
    cp0_digest=envelope.ZERO_SHA256 if module_id=='CP-0' else accepted[route.by_module['CP-0']['route_node_id']]
    invocation=envelope.build(run_id=RUN,profile_id=route.profile_id,selection_id=route.selection_id,
        route_node_id=node['route_node_id'],module_id=module_id,module_name=node['module_name'],
        expected_output_filename=filename,authority_bundle_sha256=AUTH,accepted_cp0_sha256=cp0_digest,required_upstream_digests=upstream)
    fields=dict(module_id=module_id,module_name=node['module_name'],issuer_id='EXAMPLE',issuer_name='Example',
        run_id=RUN,reporting_period='FY2025',analysis_date='2026-09-08',confidence_score=90,confidence_band='High',
        qa_status='Passed',committee_status='Committee Ready',limitation_flags=[],validation_warnings=[],downstream_consumers=[],
        credit_os_run_id=RUN,credit_os_profile_id=route.profile_id,credit_os_selection_id=route.selection_id,
        credit_os_authority_bundle_sha256=AUTH,credit_os_attempt_id=invocation['attempt_id'],
        credit_os_route_node_id=node['route_node_id'],credit_os_invocation_sha256=envelope.digest(invocation),
        upstream_artifacts_used=[dict(module_id=route.by_node[key]['module_id'],run_id=records[key].fields['run_id'],
                                     period='FY2025',sha256=value) for key,value in upstream.items()])
    contract=load_contract((ROOT/route.modules[module_id]['skill_md']).read_text(),module_id)
    appendix='### Analytical appendix — complete canonical registers\n\n'
    for reg,spec in contract['registers'].items():
        if omit_prefix and reg.startswith(omit_prefix):continue
        appendix+='#### '+reg+'\n\n'
        if module_id=='CP-0' and reg=='T8':
            rows=[[str(n),mid,'Run '+mid,'Run '+mid,'Source p1','Current handoff','READY','Relevant source p1'] for n,mid in enumerate(recommendations,1)]
            appendix+=table(navigation.NEW_HEADERS,rows)
        else:
            cols=spec['columns'] or ['Evidence']
            appendix+=table(cols,[['Recorded source p1']*len(cols)]*max(1,spec['minimum_body_rows']))
    for tid in contract['unconditional_stable_tables']:
        appendix+='<!-- table-id: '+tid+' -->\n'+table(['source_locator'],[['Source p1']])
    body=''.join('## '+h+'\n\n'+(appendix if h=='Analysis' else 'Recorded source p1.\n\n') for h in CANONICAL_HEADINGS)
    text='---\n'+yaml_fields(fields)+'\n---\n'+body
    result=validate_text(text,filename=filename)
    assert result.exit_code==0, result.errors
    return SimpleNamespace(name=filename,text=text,fields=result.fields,sha256=hashlib.sha256(text.encode()).hexdigest())


def scenario(order, selection='FULL_CREDIT_ASSESSMENT'):
    route=routing.Route(CAT,'FULL_CREDIT_32',selection,order)
    records={};accepted={};snapshot={}
    for node in route.nodes:
        a=artifact(node['module_id'],route,accepted,records,order)
        records[node['route_node_id']]=a;accepted[node['route_node_id']]=a.sha256;snapshot[a.name]=a.text
    return route,snapshot


def navigate(snapshot):
    return navigation.navigate(CAT,snapshot,authority_digest=AUTH)


def inventory(snapshot):
    return inventory_snapshot({'artifacts':[{'name':n,'text':t} for n,t in snapshot.items()]},CAT,AUTH)


class ModuleWorkflowTests(unittest.TestCase):
    def test_restored_modules_own_their_registers(self):
        index=json.loads((ROOT/'CP_DEPLOY_V_RETRIEVAL_INDEX_v1.json').read_text())
        owners={row['module_id']:row for row in index['skills']}
        self.assertEqual(len(owners),25)
        for mid,host,prefix in [('CP-2D','CP-2G','T2E.'),('CP-3C','CP-4C','T3D.'),('CP-3D','CP-2H','T3E.')]:
            self.assertIn(mid,owners);self.assertNotIn(mid,owners[host]['aliases'])
            self.assertTrue(all(r.startswith(prefix) for r in load_contract((ROOT/owners[mid]['skill_md']).read_text(),mid)['registers']))
            self.assertFalse(any(r.startswith(prefix) for r in load_contract((ROOT/owners[host]['skill_md']).read_text(),host)['registers']))

    def test_every_pathway_closes_and_orders_dependencies(self):
        for pid,profile in CAT['profiles'].items():
            for selection in profile['pathways']:
                route=routing.Route(CAT,pid,selection)
                positions={n['module_id']:i for i,n in enumerate(route.nodes)}
                for edge in profile['edges']:
                    if edge['target'] in positions and edge['type'] in {'REQUIRED','QA_GATE'}:
                        self.assertIn(edge['source'],positions,(selection,edge))
                        self.assertLess(positions[edge['source']],positions[edge['target']])

    def test_missing_catalog_prerequisite_fails_closed(self):
        bad=copy.deepcopy(CAT)
        path=bad['profiles']['FULL_CREDIT_32']['pathways']['RELATIVE_VALUE']
        path['nodes']=[n for n in path['nodes'] if n['module_id']!='CP-2A']
        for n,node in enumerate(path['nodes'],1):
            node['stage']=n;node['route_node_id']=f"RN-FULL_CREDIT_32-RELATIVE_VALUE-{n:02d}-{node['module_id']}"
        with self.assertRaisesRegex(routing.RouteError,'omits required.*CP-2A'):
            routing.Route(bad,'FULL_CREDIT_32','RELATIVE_VALUE')

    def test_legal_before_selection_and_repeated_layers(self):
        order=['CP-1','CP-4','CP-2','CP-3D','CP-3']
        _,snapshot=scenario(order)
        result=navigate(snapshot);self.assertEqual(result.status,'SHOW_LAYER',result.card)
        context=result.discovery.contexts[0]
        self.assertEqual([r.module_id for r in context.recommendations],order)
        flat=[r.module_id for key in context.layers for r in navigation.recommendations_for_layer(context,navigation.validate_catalog(CAT),key)]
        self.assertEqual(flat,order)
        self.assertEqual(context.completed,set(order))
        memo=inventory(snapshot);self.assertEqual(memo.status,'READY')
        self.assertTrue(any(a.module_id=='CP-3' and a.disposition=='ELIGIBLE' for a in memo.artifacts),memo)

    def test_late_legal_input_is_ordered_before_consumer(self):
        _,snapshot=scenario(['CP-1','CP-2','CP-3','CP-4'])
        context=navigate(snapshot).discovery.contexts[0]
        self.assertLess([r.module_id for r in context.recommendations].index('CP-4'),[r.module_id for r in context.recommendations].index('CP-3'))

    def test_unchanged_current_artifacts_are_complete(self):
        _,snapshot=scenario(['CP-1','CP-2','CP-2D'],selection='LIQUIDITY_REVIEW')
        context=navigate(snapshot).discovery.contexts[0]
        self.assertEqual(context.completed,{'CP-1','CP-2','CP-2D'})
        result=prepare(CAT,AUTH,module_id='CP-2D',issuer_id='EXAMPLE',analysis_date='2026-09-08',artifacts=snapshot)
        self.assertEqual(result['frontmatter_fields']['credit_os_run_id'],RUN)

    def test_changed_input_invalidates_only_dependents(self):
        _,snapshot=scenario(['CP-1','CP-2','CP-2D','CP-3D'])
        snapshot['EXAMPLE_CP-1_20260908.md']+='Changed source p2.\n'
        context=navigate(snapshot).discovery.contexts[0]
        self.assertEqual(context.completed,{'CP-1','CP-3D'})
        self.assertTrue(any('stale upstream content' in p for p in context.problems.values()))
        dispositions={a.module_id:a.disposition for a in inventory(snapshot).artifacts}
        self.assertEqual(dispositions['CP-2'],'EXCLUDED');self.assertEqual(dispositions['CP-3D'],'ELIGIBLE')

    def test_removed_input_blocks_consumers(self):
        _,snapshot=scenario(['CP-1','CP-2'])
        del snapshot['EXAMPLE_CP-1_20260908.md']
        context=navigate(snapshot).discovery.contexts[0]
        self.assertNotIn('CP-2',context.completed);self.assertIn('CP-1',context.blockers['CP-2'])
        with self.assertRaisesRegex(ValueError,'missing blocking upstream'):
            prepare(CAT,AUTH,module_id='CP-2',issuer_id='EXAMPLE',analysis_date='2026-09-08',artifacts=snapshot)

    def test_missing_absorbed_registers_rejects_legal_completion(self):
        _,snapshot=scenario(['CP-1','CP-4'])
        text=snapshot['EXAMPLE_CP-4_20260908.md']
        import re
        text=re.sub(r'#### T4[CDF]\.\d+\n.*?(?=#### |## Evidence Trace)', '', text, flags=re.S)
        snapshot['EXAMPLE_CP-4_20260908.md']=text
        self.assertEqual(validate_text(text).exit_code,0)
        context=navigate(snapshot).discovery.contexts[0]
        self.assertNotIn('CP-4',context.completed)
        self.assertIn('required register missing',context.problems['EXAMPLE_CP-4_20260908.md'])
        self.assertTrue(any(a.module_id=='CP-4' and a.disposition=='EXCLUDED' for a in inventory(snapshot).artifacts))

    def test_wrong_profile_is_not_complete(self):
        _,snapshot=scenario(['CP-1','CP-2'])
        snapshot['EXAMPLE_CP-2_20260908.md']=snapshot['EXAMPLE_CP-2_20260908.md'].replace('credit_os_profile_id: "FULL_CREDIT_32"','credit_os_profile_id: "LITE_CREDIT_22"')
        context=navigate(snapshot).discovery.contexts[0]
        self.assertNotIn('CP-2',context.completed)
        self.assertIn('profile',context.problems['EXAMPLE_CP-2_20260908.md'])

    def test_legacy_alias_has_explicit_migration_diagnostic(self):
        _,snapshot=scenario(['CP-1A'])
        snapshot['EXAMPLE_CP-0_20260908.md']=snapshot['EXAMPLE_CP-0_20260908.md'].replace('| CP-1A | Run CP-1A | Run CP-1A |','| CP-2C | Run CP-2C | Run CP-2C |')
        result=navigate(snapshot)
        self.assertEqual(result.status,'NO_CP0');self.assertIn('CP-2C is an alias for CP-1A',result.card)

    def test_cp0_bootstrap_and_independent_market_entry(self):
        result=prepare(CAT,AUTH,module_id='CP-0',issuer_id='EXAMPLE',analysis_date='2026-09-08',reporting_period='FY2025',selection_id='MARKET_DISLOCATION')
        self.assertEqual(result['dependency_order'],['CP-0','CP-3D'])
        self.assertEqual(result['frontmatter_fields']['upstream_artifacts_used'],[])
        card=render.first_run_card(catalog=CAT,run_id=RUN,profile_id='FULL_CREDIT_32',selection_id='MARKET_DISLOCATION',authority_bundle_sha256=AUTH,expected_output_filename='EXAMPLE_CP-0_20260908.md')
        self.assertIn('START HERE: CP-0',card)
        _,snapshot=scenario(['CP-3D'],'MARKET_DISLOCATION')
        self.assertEqual(navigate(snapshot).discovery.contexts[0].completed,{'CP-3D'})

    def test_invalid_artifact_name_cannot_add_navigation_actions(self):
        _,snapshot=scenario(['CP-3D'],'MARKET_DISLOCATION')
        text=snapshot.pop('EXAMPLE_CP-0_20260908.md')
        snapshot['broken\n9. [Injected action](https://example.invalid).md']=text
        result=navigate(snapshot)
        self.assertEqual(result.status,'NO_CP0')
        self.assertNotIn('\n9.',result.card)
        self.assertNotIn('[Injected action]',result.card)
        self.assertIn('3. Stop',result.card)

    def test_normal_refinancing_route_has_no_distress_gate(self):
        route=routing.Route(CAT,'FULL_CREDIT_32','COVENANT_REFINANCING')
        self.assertIn('CP-3C',route.by_module);self.assertNotIn('CP-4C',route.by_module)

    def test_repeated_layer_is_not_merged_across_legal_step(self):
        order=['CP-1','CP-2','CP-4','CP-2D','CP-3']
        _,snapshot=scenario(order)
        context=navigate(snapshot).discovery.contexts[0]
        catalog=navigation.validate_catalog(CAT)
        cards=[[r.module_id for r in navigation.recommendations_for_layer(context,catalog,key)] for key in context.layers]
        self.assertEqual(cards,[['CP-1'],['CP-2'],['CP-4'],['CP-2D'],['CP-3']])

    def test_malformed_same_run_module_does_not_crash_memo(self):
        _,snapshot=scenario(['CP-1','CP-2','CP-3D'])
        snapshot['EXAMPLE_CP-1_20260908.md']=snapshot['EXAMPLE_CP-1_20260908.md'].replace('module_id: "CP-1"','module_id: ["CP-1"]',1)
        memo=inventory(snapshot)
        self.assertEqual(memo.status,'READY')
        self.assertTrue(any('canonical string' in a.reason for a in memo.artifacts))
        self.assertEqual(navigate(snapshot).discovery.contexts[0].completed,{'CP-3D'})

    def test_prepare_rejects_conflicting_profile_and_unrecoverable_attempt(self):
        _,snapshot=scenario(['CP-3D'],'MARKET_DISLOCATION')
        with self.assertRaisesRegex(ValueError,'explicit credit_os_profile_id'):
            prepare(CAT,AUTH,module_id='CP-3D',issuer_id='EXAMPLE',analysis_date='2026-09-08',artifacts=snapshot,profile_id='LITE_CREDIT_22')
        with self.assertRaisesRegex(ValueError,'attempt range'):
            prepare(CAT,AUTH,module_id='CP-0',issuer_id='EXAMPLE',analysis_date='2026-09-08',reporting_period='FY2025',ordinal=257)

    def test_reconciliation_uses_same_acceptance_as_navigation_and_memo(self):
        from credit_os_v.reconcile import reconcile
        _,snapshot=scenario(['CP-1','CP-4','CP-2','CP-3'])
        entries=[SimpleNamespace(name=name) for name in snapshot]
        source=SimpleNamespace(list=lambda:SimpleNamespace(entries=entries,rejected=[]),
            read=lambda entry:SimpleNamespace(data=snapshot[entry.name].encode(),sha256=hashlib.sha256(snapshot[entry.name].encode()).hexdigest()))
        view=reconcile(source,catalog=CAT,current_authority_sha256=AUTH,require_stability=False)
        self.assertEqual({a.module_id for a in view.accepted()},{'CP-0','CP-1','CP-4','CP-2','CP-3'})
        snapshot['EXAMPLE_CP-1_20260908.md']+='Changed source p2.'
        view=reconcile(source,catalog=CAT,current_authority_sha256=AUTH,require_stability=False)
        self.assertEqual({a.module_id for a in view.accepted()},{'CP-0','CP-1'})

    def test_separated_market_has_no_inherited_ratings_gate(self):
        text=(ROOT/'skills/cp-3d-market-implied-risk/SKILL.md').read_text()
        self.assertNotIn('NAMED_LITE_OBJECT_ACCEPTED',text)
        self.assertNotIn('accepted_lite_object_ids',text)
        text=(ROOT/'skills/cp-3c-refinancing-lme-risk/SKILL.md').read_text()
        self.assertEqual(text.count('## LITE profile compatibility'),1)

    def test_public_clis_share_current_lineage(self):
        import subprocess, tempfile
        from unittest.mock import patch
        authority=json.loads((ROOT/'skills/cp-os-credit-os/references/CREDIT_OS_V_AUTHORITY_BUNDLE_v2.json').read_text())['authority_bundle_sha256']
        with patch.object(sys.modules[__name__],'AUTH',authority):
            _,snapshot=scenario(['CP-1','CP-4','CP-2','CP-3D','CP-3'])
        with tempfile.TemporaryDirectory() as scratch:
            path=Path(scratch)/'snapshot.json';path.write_text(json.dumps({'artifacts':snapshot}))
            command=[sys.executable,'-B',str(ROOT/'skills/cp-os-credit-os/scripts/prepare_invocation.py'),
                     '--module-id','CP-3','--issuer-id','EXAMPLE','--analysis-date','2026-09-08','--snapshot',str(path)]
            result=subprocess.run(command,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            fields=json.loads(result.stdout)['frontmatter_fields']
            self.assertEqual(fields['credit_os_invocation_sha256'],validate_text(snapshot['EXAMPLE_CP-3_20260908.md']).fields['credit_os_invocation_sha256'])
            result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/cp-os-credit-os/scripts/credit_os_v_cli.py'),'navigate'],input=path.read_text(),text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'SHOW_LAYER')
            path.write_text(json.dumps({'artifacts':[{'name':name,'text':text} for name,text in snapshot.items()]}))
            result=subprocess.run([sys.executable,'-B',str(ROOT/'skills/cp-memo-credit-research-report/scripts/export_cp_memo.py'),'inventory',str(path)],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'READY')

    def test_lite_prerequisites_and_source_gate_are_preserved(self):
        route=routing.Route(CAT,'LITE_CREDIT_22','LITE_FULL_CREDIT_SCREEN')
        self.assertLess([n['module_id'] for n in route.nodes].index('CP-L10'),[n['module_id'] for n in route.nodes].index('CP-3C'))
        self.assertTrue(any(e['source']=='CP-2A' and e['target']=='CP-4C' and e['type']=='REQUIRED' for e in route.edges))
        _,snapshot=scenario(['CP-1','CP-2'])
        snapshot['EXAMPLE_CP-0_20260908.md']=snapshot['EXAMPLE_CP-0_20260908.md'].replace('| CP-2 | Run CP-2 | Run CP-2 | Source p1 | Current handoff | READY | Relevant source p1 |','| CP-2 | Run CP-2 | DO NOT RUN | Source p1 | Current handoff | BLOCKED | Missing source p1 |')
        context=navigate(snapshot).discovery.contexts[0]
        self.assertNotIn('CP-2',context.completed)
        self.assertIn('source gate',context.problems['EXAMPLE_CP-2_20260908.md'])

    def test_selected_ready_legal_input_cannot_be_skipped(self):
        route,snapshot=scenario(['CP-1','CP-2','CP-4','CP-3'])
        del snapshot['EXAMPLE_CP-4_20260908.md']
        context=navigate(snapshot).discovery.contexts[0]
        self.assertIn('CP-4',context.blockers['CP-3'])
        with self.assertRaisesRegex(ValueError,'missing blocking upstream.*CP-4'):
            prepare(CAT,AUTH,module_id='CP-3',issuer_id='EXAMPLE',analysis_date='2026-09-08',artifacts=snapshot)
        # Even an otherwise valid consumer authored without that optional input must wait.
        records={};accepted={}
        for node in route.nodes:
            if node['module_id']=='CP-4':continue
            record=artifact(node['module_id'],route,accepted,records,['CP-1','CP-2','CP-4','CP-3'])
            records[node['route_node_id']]=record;accepted[node['route_node_id']]=record.sha256
            snapshot[record.name]=record.text
        self.assertNotIn('CP-3',navigate(snapshot).discovery.contexts[0].completed)
        limited=routing.expected_upstream_digests(route,route.by_module['CP-3']['route_node_id'],accepted,readiness={'CP-4':'BLOCKED'})
        self.assertNotIn(route.by_module['CP-4']['route_node_id'],limited)
        self.assertTrue(any(a.module_id=='CP-3' and a.disposition=='EXCLUDED' for a in inventory(snapshot).artifacts))

    def test_dependency_cycle_is_rejected(self):
        with self.assertRaisesRegex(routing.RouteError,'cycle'):
            routing.dependency_order([{'source':'CP-1','target':'CP-2','type':'REQUIRED'},{'source':'CP-2','target':'CP-1','type':'REQUIRED'}],['CP-1'])

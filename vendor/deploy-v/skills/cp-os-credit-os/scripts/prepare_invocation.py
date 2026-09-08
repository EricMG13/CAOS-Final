#!/usr/bin/env python3
"""Prepare reproducible handoff fields; read-only except for output on stdout."""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from credit_os_v_cli import verified_authority, verified_catalog, verified_limits, _BoundedTextReader, JSON_OVERHEAD_BYTES
from credit_os.authority import AuthorityError
from credit_os.limits import load_limits
from credit_os_v import envelope
from credit_os_v.identity import new_run_id
from credit_os_v.routing import Route, expected_upstream_digests
from credit_os_v.navigation import validate_artifacts, validate_catalog, plan_from_cp0
from credit_os_v.handoffs import accept_snapshot
from credit_os_v.research import validate_brief


def prepare(catalog, authority_digest, *, module_id, issuer_id, analysis_date,
            reporting_period=None, profile_id=None, selection_id=None, run_id=None,
            artifacts=None, ordinal=1, research_brief=None):
    if not isinstance(analysis_date, str) or date.fromisoformat(analysis_date).isoformat() != analysis_date:
        raise ValueError("analysis_date must be YYYY-MM-DD")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or not 1 <= ordinal <= envelope.MAX_ATTEMPT_ORDINAL:
        raise ValueError("ordinal is outside the supported attempt range")
    if research_brief is not None:
        brief = validate_brief(research_brief)
        if module_id != 'CP-DR' or artifacts or profile_id or selection_id:
            raise ValueError('a standalone research brief cannot select an issuer workflow')
        if (issuer_id is not None and issuer_id != brief['scope_key']) or (run_id is not None and run_id != brief['run_id']):
            raise ValueError('explicit identity differs from standalone research brief')
        if not reporting_period:
            raise ValueError('standalone research requires reporting_period')
        fields = dict(module_id='CP-DR',module_name='DeepResearch',run_id=brief['run_id'],
                      analysis_date=analysis_date,reporting_period=reporting_period,upstream_artifacts_used=[],
                      research_mode='standalone',research_question='; '.join(q['question'] for q in brief['questions']),
                      approved_plan_hash='sha256:'+envelope.digest(brief),
                      **{key:brief[key] for key in ('scope_type','scope_key','subject_name','source_mode')})
        return {'filename':f"{brief['scope_key']}_CP-DR_{analysis_date.replace('-', '')}.md",
                'frontmatter_fields':fields,'research_brief':brief,'dependency_order':['CP-DR']}
    if not issuer_id or any(c in issuer_id for c in '/\\\n\r'):
        raise ValueError("issuer_id must be a safe filename component")
    filename = f"{issuer_id}_{module_id}_{analysis_date.replace('-', '')}.md"
    parent_run_id = upgrade_source_sha256 = None
    upstream_records = []
    if module_id == 'CP-0':
        if not reporting_period:
            raise ValueError('CP-0 requires reporting_period')
        profile_id = profile_id or 'FULL_CREDIT_32'
        selection_id = selection_id or ('FULL_CREDIT_ASSESSMENT' if profile_id == 'FULL_CREDIT_32' else 'LITE_FULL_CREDIT_SCREEN')
        run_id = run_id or new_run_id()
        route = Route(catalog, profile_id, selection_id)
        cp0_digest, upstream = envelope.ZERO_SHA256, {}
    else:
        artifacts = artifacts or {}
        limits = load_limits()
        if not isinstance(artifacts, dict) or len(artifacts) > limits['entries_per_run_folder']:
            raise ValueError('snapshot is not an object or exceeds the artifact count limit')
        if any(not isinstance(body, str) for body in artifacts.values()):
            raise ValueError('artifact bodies must be strings')
        sizes = [len(body.encode('utf-8')) for body in artifacts.values()]
        if sum(sizes) > limits['bytes_per_refresh'] or any(size > limits['markdown_or_control_file_bytes'] for size in sizes):
            raise ValueError('snapshot exceeds the artifact byte limit')
        candidates = validate_artifacts(artifacts)
        anchors = [a for a in candidates if a.fields and a.fields.get('module_id') == 'CP-0'
                   and (run_id is None or a.fields.get('credit_os_run_id') == run_id)]
        if len(anchors) != 1:
            raise ValueError('select exactly one CP-0 run in the snapshot')
        cp0 = anchors[0]
        if cp0.fields.get('issuer_id') != issuer_id:
            raise ValueError('issuer_id differs from CP-0')
        for value, field in [(profile_id,'credit_os_profile_id'),(selection_id,'credit_os_selection_id'),(reporting_period,'reporting_period')]:
            if value is not None and value != cp0.fields.get(field):
                raise ValueError(f'explicit {field} differs from CP-0')
        route, recommendations = plan_from_cp0(cp0, validate_catalog(catalog, authority_digest), candidates)
        readiness = {r.module_id:r.readiness for r in recommendations}
        if readiness.get(module_id) not in {'READY','READY_WITH_LIMITATIONS'}:
            raise ValueError('module is not source-ready in the selected CP-0 plan')
        accepted, problems = accept_snapshot(candidates, cp0, route, authority_digest, readiness)
        cp0_digest = accepted.get(route.by_module['CP-0']['route_node_id'])
        if cp0_digest is None:
            raise ValueError(problems.get(cp0.name, 'CP-0 was not accepted'))
        upstream = expected_upstream_digests(route, route.by_module[module_id]['route_node_id'], accepted, readiness=readiness)
        by_hash = {a.sha256:a for a in candidates}
        upstream_records = [{'module_id':route.by_node[node]['module_id'], 'run_id':by_hash[sha].fields['run_id'],
                             'period':by_hash[sha].fields['reporting_period'], 'sha256':sha} for node,sha in upstream.items()]
        run_id = cp0.fields['credit_os_run_id']
        profile_id, selection_id = route.profile_id, route.selection_id
        reporting_period = cp0.fields['reporting_period']
        parent_run_id = cp0.fields.get('credit_os_parent_run_id')
        upgrade_source_sha256 = cp0.fields.get('credit_os_upgrade_source_sha256')
    node = route.by_module[module_id]
    invocation = envelope.build(run_id=run_id, profile_id=profile_id, selection_id=selection_id,
                                module_id=module_id, module_name=node['module_name'], route_node_id=node['route_node_id'],
                                expected_output_filename=filename, authority_bundle_sha256=authority_digest,
                                accepted_cp0_sha256=cp0_digest, required_upstream_digests=upstream,
                                parent_run_id=parent_run_id, upgrade_source_sha256=upgrade_source_sha256, ordinal=ordinal)
    fields = dict(module_id=module_id, module_name=node['module_name'], issuer_id=issuer_id,
                  analysis_date=analysis_date, reporting_period=reporting_period, run_id=run_id,
                  credit_os_run_id=run_id, credit_os_profile_id=profile_id, credit_os_selection_id=selection_id,
                  credit_os_authority_bundle_sha256=authority_digest,
                  credit_os_attempt_id=invocation['attempt_id'], credit_os_route_node_id=node['route_node_id'],
                  credit_os_invocation_sha256=envelope.digest(invocation), upstream_artifacts_used=upstream_records)
    if parent_run_id:
        fields.update(credit_os_parent_run_id=parent_run_id, credit_os_upgrade_source_sha256=upgrade_source_sha256)
    result = {'filename':filename, 'frontmatter_fields':fields, 'dependency_order':[n['module_id'] for n in route.nodes]}
    if route.research_brief:
        brief = route.research_brief
        result['research_brief'] = brief
        if module_id == 'CP-DR':
            fields.update(research_mode='linked',research_question='; '.join(q['question'] for q in brief['questions']),
                          approved_plan_hash='sha256:'+envelope.digest(brief),
                          **{key:brief[key] for key in ('scope_type','scope_key','subject_name','source_mode')})
        else:
            research_input = next((r for r in upstream_records if r['module_id']=='CP-DR'), None)
            if research_input:
                result['research_adoption_rows'] = [dict(question_id=q['question_id'],research_sha256=research_input['sha256'],
                    disposition='REQUIRES_ANALYST_DECISION',reason='REQUIRES_ANALYST_DECISION',analytical_effect='REQUIRES_ANALYST_DECISION')
                    for q in brief['questions'] if q['consumer_module_id']==module_id]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('module-id','analysis-date'):
        parser.add_argument('--'+name, required=True)
    for name in ('issuer-id','reporting-period','profile-id','selection-id','run-id','snapshot','research-brief'):
        parser.add_argument('--'+name)
    parser.add_argument('--ordinal',type=int,default=1)
    args=vars(parser.parse_args())
    try:
        authority=verified_authority()
        brief_path=args.pop('research_brief')
        if brief_path:
            with Path(brief_path).open(encoding='utf-8') as stream:
                args['research_brief']=json.load(_BoundedTextReader(stream, 65536))
        snapshot=args.pop('snapshot')
        if snapshot:
            limits = verified_limits(authority)
            with Path(snapshot).open(encoding='utf-8') as stream:
                args['artifacts']=json.load(_BoundedTextReader(stream, int(limits['bytes_per_refresh']) + JSON_OVERHEAD_BYTES))['artifacts']
        result=prepare(verified_catalog(authority),authority.result['authority_bundle_sha256'],**args)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,AuthorityError,envelope.EnvelopeError) as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc)}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())

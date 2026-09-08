#!/usr/bin/env python3
"""Validate the research registers and, for linked work, current run acceptance."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cp-os-credit-os' / 'scripts'))
from credit_os_v_cli import verified_authority, verified_catalog, verified_limits, _BoundedTextReader, JSON_OVERHEAD_BYTES
from credit_os.authority import AuthorityError
from credit_os_v.research import validate_brief, validate_dossier
from credit_os_v.handoffs import content_errors, accept_snapshot
from credit_os_v.navigation import validate_artifacts, validate_catalog, plan_from_cp0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--brief', required=True)
    parser.add_argument('--handoff', required=True)
    parser.add_argument('--snapshot')
    args = parser.parse_args()
    try:
        authority = verified_authority()
        catalog = verified_catalog(authority)
        with Path(args.brief).open(encoding='utf-8') as stream:
            brief = json.load(_BoundedTextReader(stream, 65536))
        with Path(args.handoff).open(encoding='utf-8') as stream:
            text = _BoundedTextReader(stream, 8 * 1024 * 1024).read()
        candidate = validate_artifacts({Path(args.handoff).name: text})[0]
        module = next(m for m in catalog['modules'] if m['module_id'] == 'CP-DR')
        errors = content_errors(candidate, module)
        if errors:
            raise ValueError('; '.join(errors))
        if not isinstance(brief, dict):
            raise ValueError('research brief must be an object')
        if brief.get('mode') == 'linked':
            if not args.snapshot:
                raise ValueError('linked research validation requires a fresh snapshot')
            limits = verified_limits(authority)
            with Path(args.snapshot).open(encoding='utf-8') as stream:
                snapshot = json.load(_BoundedTextReader(stream, int(limits['bytes_per_refresh']) + JSON_OVERHEAD_BYTES))['artifacts']
            if not isinstance(snapshot, dict) or len(snapshot) > limits['entries_per_run_folder'] or any(not isinstance(t, str) for t in snapshot.values()):
                raise ValueError('snapshot is malformed or exceeds the artifact count limit')
            sizes = [len(t.encode('utf-8')) for t in snapshot.values()]
            if sum(sizes) > limits['bytes_per_refresh'] or any(n > limits['markdown_or_control_file_bytes'] for n in sizes):
                raise ValueError('snapshot exceeds the artifact byte limit')
            if snapshot.get(candidate.name) != candidate.text:
                raise ValueError('fresh snapshot must contain the exact research handoff')
            candidates = validate_artifacts(snapshot)
            anchors = [a for a in candidates if a.fields and a.fields.get('module_id') == 'CP-0' and a.fields.get('credit_os_run_id') == brief.get('run_id')]
            if len(anchors) != 1:
                raise ValueError('research requires one matching CP-0 anchor')
            route, recommendations = plan_from_cp0(anchors[0], validate_catalog(catalog, authority.result['authority_bundle_sha256']), candidates)
            if route.research_brief != brief:
                raise ValueError('brief differs from the current snapshot control')
            accepted, problems = accept_snapshot(candidates, anchors[0], route, authority.result['authority_bundle_sha256'], {r.module_id:r.readiness for r in recommendations})
            if accepted.get(route.by_module['CP-DR']['route_node_id']) != candidate.sha256:
                raise ValueError(problems.get(candidate.name, 'research handoff is not accepted'))
        else:
            validate_dossier(candidate, validate_brief(brief))
        print(json.dumps({'status':'PASS','coverage_score':candidate.fields['coverage_score']}))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AuthorityError) as exc:
        print(json.dumps({'status':'BLOCKED','reason':str(exc)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

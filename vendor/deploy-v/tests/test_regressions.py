"""Regressions for the September 2026 package review; stdlib unless integration is enabled."""
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def module(slug, name):
    sys.path.insert(0, str(ROOT / 'skills' / slug / 'scripts'))
    return importlib.import_module(name)


handoff = module('cp-0-source-readiness', 'validate_handoff')
tables = module('cp-0-source-readiness', 'cp_tables')
complete = module('cp-0-source-readiness', 'completeness_check')
funding = module('cp-4c-restructuring-fulcrum', 'funding_gap')
recovery = module('cp-3-relative-value-security-selection', 'recovery_waterfall')
covenant = module('cp-4-legal-covenant-interpreter', 'covenant_headroom')
bond = module('cp-2h-ratings-migration-trigger', 'bond_analytics')
model_inputs = module('cp-model', 'validate_cp_model_inputs')
memo_markdown = module('cp-memo-credit-research-report', 'cp_memo.markdown')


def markdown(**changes):
    fields = dict(module_id='CP-1', module_name='CanonicalDataFoundation', run_id='run-1',
                  reporting_period='FY2025', analysis_date='2026-09-07', confidence_score=90,
                  confidence_band='High', qa_status='Passed', committee_status='Committee Ready',
                  limitation_flags=[], validation_warnings=[], upstream_artifacts_used=[],
                  downstream_consumers=['CP-MODEL'], issuer_name='Example', issuer_id='EXAMPLE')
    fields.update(changes)
    return ('---\n' + '\n'.join(f'{key}: {json.dumps(value)}' for key, value in fields.items())
            + '\n---\n' + '\n'.join(f'## {heading}\nSupported conclusion.\n' for heading in handoff.CANONICAL_HEADINGS))


class RegressionTests(unittest.TestCase):
    def test_required_handoff_values(self):
        filename = 'EXAMPLE_CP-1_20260907.md'
        self.assertEqual(handoff.validate_text(markdown(), filename=filename).exit_code, 0)
        for field in handoff.REQUIRED_FIELDS + handoff.ISSUER_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(handoff.validate_text(markdown(**{field: None}), filename=filename).exit_code, 2)
        for field in ('confidence_band', 'qa_status', 'committee_status'):
            for value in ([], {}, True, 2):
                with self.subTest(field=field, value=value):
                    self.assertEqual(handoff.validate_text(markdown(**{field: value})).exit_code, 2)

    def test_cp_dr_enum_types(self):
        fields = dict(module_id='CP-DR', scope_key='Sector', subject_name='Sector', research_question='Question',
                      approved_plan_hash='sha256:' + 'a' * 64, scope_type='sector', source_mode='supplied_only',
                      coverage_score=90, research_status='Complete', research_stop_reason='coverage_satisfied')
        self.assertEqual(handoff.validate_text(markdown(**fields)).exit_code, 0)
        for field in ('scope_type', 'source_mode', 'research_status', 'research_stop_reason', 'coverage_score'):
            for value in (None, [], {}):
                with self.subTest(field=field, value=value):
                    self.assertEqual(handoff.validate_text(markdown(**dict(fields, **{field: value}))).exit_code, 2)

    def test_completeness_uses_real_registers(self):
        skill = (ROOT / 'skills/cp-1-canonical-data-foundation/SKILL.md').read_text()
        contract = complete.load_contract(skill, 'CP-1')
        sections = []
        for name, spec in contract['registers'].items():
            sections.append(f'### {name}\n| ' + ' | '.join(spec['columns']) + ' |\n| '
                            + ' | '.join('---' for _ in spec['columns']) + ' |\n'
                            + ('| ' + ' | '.join('present' for _ in spec['columns']) + ' |\n')
                            * max(1, spec['minimum_body_rows']))
        sections.extend(f'<!-- table-id: {name} -->\n| value |\n| --- |\n| present |'
                        for name in contract['unconditional_stable_tables'])
        good = '\n\n'.join(sections)
        self.assertFalse(complete.check(skill, good, 'CP-1')[0])
        width = len(next(iter(contract['registers'].values()))['columns'])
        blank_row = good.replace(sections[0], sections[0] + '|' * (width + 1) + '\n')
        self.assertTrue(complete.check(skill, blank_row, 'CP-1')[0])
        self.assertTrue(complete.check(skill, good.replace('present', '', 1), 'CP-1')[0])
        self.assertTrue(complete.check(skill, '```markdown\n' + good + '\n```', 'CP-1')[0])
        self.assertTrue(complete.check(skill, good.replace('| value |\n| --- |\n| present |', ''), 'CP-1')[0])

    def test_completeness_enforces_bullet_list_columns(self):
        skill = (ROOT / 'skills/cp-3-relative-value-security-selection/SKILL.md').read_text()
        draft = '### T3.7\n| Rank | Evidence ID |\n| --- | --- |\n| 1 | unknown |\n'
        violations, contract, _ = complete.check(skill, draft, 'CP-3')
        spec = contract['registers']['T3.7']
        self.assertIn('Countervailing Evidence', spec['columns'])
        self.assertEqual(spec['columns'], spec['critical_columns'])
        self.assertTrue(any(v.startswith('T3.7: missing column(s)') for v in violations), violations)
        self.assertTrue(any(v.startswith('T3.7 row 1: critical column')
                            and 'disqualifying placeholder' in v for v in violations), violations)

    def test_tagged_table_shapes(self):
        table = '<!-- table-id: example -->\n| A | B |\n| --- | --- |\n| 1 | 2 |\n'
        self.assertEqual(len(tables.parse_tables(table)['example']), 1)
        self.assertFalse(tables.parse_tables('````markdown\n```\n' + table + '\n````'))
        self.assertFalse(tables.parse_tables(table.replace('<!-- table-id: example -->', '`<!-- table-id: example -->`')))
        empty_first = table.replace('| 1 | 2 |', '||2|')
        self.assertEqual(tables.parse_tables(empty_first)['example'].rows, [dict(A='', B='2')])
        self.assertEqual(complete.find_registers('### T1\n' + empty_first)['T1'][1], [dict(A='', B='2')])
        self.assertEqual(tables.parse_tables(table + '|||\n')['example'].rows[-1], dict(A='', B=''))
        for bad in (table + table, table.replace('| 1 | 2 |', '| 1 |'), table.replace('| A | B |', '| A | A |')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tables.parse_tables(bad)

    def test_finite_and_unambiguous_figures(self):
        for bad in (float('nan'), float('inf'), -float('inf'), '1e309', 10**1000, '1,2.3', '1.2.3'):
            with self.subTest(value=str(bad)), self.assertRaises(ValueError):
                tables.parse_figure(bad)
        self.assertEqual(tables.parse_figure('1,234.56'), 1234.56)
        self.assertEqual(tables.parse_figure('1.234,56'), 1234.56)
        self.assertIsNone(tables.parse_figure('n/a'))
        with self.assertRaises(ValueError):
            covenant.headroom({'test_type': 'max-ratio', 'threshold': 5, 'current_ratio': float('nan')})
        with self.assertRaises(ValueError):
            covenant.headroom({'test_type': 'max-ratio', 'threshold': 1e308, 'current_ratio': -1e308})
        with self.assertRaises(ValueError):
            covenant.trigger_headroom({'trigger_direction': 'max-ratio', 'threshold': 1e308,
                                      'cases': [{'period': 'FY26', 'value': -1e308}]})

    def test_funding_currency_across_components(self):
        payload = dict(horizon_years=2, currency='USD', cash=100,
                       instruments=[dict(instrument='Note', amount=100, years_to_maturity=1, currency='EUR')])
        self.assertEqual(funding.compute(payload)['as_of_balance_sheet_date']['gap']['status'], 'Not Calculable')
        payload['instruments'][0]['currency'] = 'USD'
        self.assertEqual(funding.compute(payload)['as_of_balance_sheet_date']['gap']['coverage_ratio'], 1)
        payload.update(forecast_fcf=10, forecast_fcf_currency='EUR')
        self.assertEqual(funding.compute(payload)['as_of_balance_sheet_date']['gap']['status'], 'Not Calculable')
        del payload['currency']
        with self.assertRaises(ValueError):
            funding.compute(payload)

    def test_recovery_boundaries_and_unknowns(self):
        claims = [dict(claim_id='S', amount=100), dict(claim_id='J', amount=100)]
        for ev, state, residual in ((0, 'zero recovery', 0), (100, 'class boundary', 0),
                                    (150, 'partial recovery', 0), (200, 'fully repaid', 0),
                                    (225, 'fully repaid', 25)):
            with self.subTest(ev=ev):
                result = recovery.waterfall(ev, claims)
                self.assertEqual((result['allocation_state'], result['residual_to_equity']), (state, residual))
        summary = recovery.sensitivity(claims, [dict(label='zero', enterprise_value=0)])
        self.assertNotIn('every class is whole', summary['note'])
        self.assertIsNone(summary['fulcrum_stable'])
        claims[0]['amount'] = None
        result = recovery.waterfall(100, claims)
        self.assertIsNone(result['claims'][1]['recovered'])
        self.assertIsNone(result['residual_to_equity'])
        for ev, stack, costs in ((100, [], [dict(amount=-25)]), (100, [dict(claim_id='S', amount=-1)], []), (-1, [], [])):
            with self.subTest(ev=ev, stack=stack, costs=costs), self.assertRaises(ValueError):
                recovery.waterfall(ev, stack, costs)
        for claim_id in (None, '', ' ', 1, []):
            with self.subTest(claim_id=claim_id), self.assertRaises(ValueError):
                recovery.waterfall(50, [dict(claim_id=claim_id, amount=100)])

    def test_sustained_trigger_needs_a_window_within_one_case(self):
        trigger = dict(trigger='L', trigger_direction='max-ratio', threshold=5,
                       cases=[dict(case='Base', period='2026Q4', value=5.5),
                              dict(case='Downside', period='2026Q4', value=6)])
        self.assertIs(covenant.trigger_headroom(trigger)['sustained'], False)
        trigger['cases'][1].update(case='Base', period='2027Q1')
        self.assertIsNone(covenant.trigger_headroom(trigger)['sustained'])
        trigger['sustained_periods'] = ['2026Q4', '2027Q1']
        self.assertEqual(covenant.trigger_headroom(trigger)['sustained_cases'], ['Base'])
        trigger['cases'][1]['value'] = None
        self.assertIsNone(covenant.trigger_headroom(trigger)['sustained'])
        trigger['cases'] = []
        self.assertEqual(covenant.trigger_headroom(trigger)['classification'], 'insufficient information')

    def test_bond_rejects_unsupported_assumptions(self):
        base = dict(price=100, coupon=6, years_to_maturity=5)
        self.assertAlmostEqual(bond.compute(base)['yield_to_maturity'], .06)
        for changes in (dict(years_to_maturity=2.1), dict(years_to_maturity=2.2),
                        dict(convention={'compounding': 'annual'}), dict(accrued_interest=1),
                        dict(call_schedule=[dict(years=1.1, price=100)])):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bond.compute(dict(base, **changes))
        self.assertEqual(bond.compute(dict(base, call_schedule=[dict(years=1, price=None)]))['status'], 'Not Calculable')
        for changes in (dict(recovery_assumption=.99, benchmark_yield=.04, horizon_years=.5),
                        dict(recovery_assumption=.4, benchmark_yield=.04, horizon_years=-1),
                        dict(recovery_assumption=2)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bond.compute(dict(base, **changes))

    def test_current_catalyst_handoff_is_accepted(self):
        text = markdown(module_id='CP-2A', module_name='DownsidePathway')
        self.assertEqual(handoff.validate_text(text, filename='EXAMPLE_CP-2A_20260907.md').exit_code, 0)
        errors = []
        model_inputs._validate_auxiliary_envelope('CP-2A', text, None, errors)
        self.assertFalse(errors)
        self.assertEqual(model_inputs.CP2B_SNAPSHOT_TABLE, 'cp2b.cp_model_catalysts')

    def test_fenced_memo_examples_and_limitations_stay_out(self):
        text = ('## Analysis\n### Credit view\nActual conclusion.\n\n````text\n'
                '```\nExample only: revenue grew 900%.\n~~~\n- Fake finding.\n````\n\n'
                'Actual second conclusion.\n## Gaps & Conflicts\n~~~\n- Fake limitation.\n~~~\n- Actual limitation.')
        passages = memo_markdown.reader_passages(text)
        self.assertEqual([p.text for p in passages], ['Actual conclusion.', 'Actual second conclusion.'])
        self.assertEqual([p.text for p in memo_markdown.limitation_passages(text)], ['Actual limitation.'])

    def test_cli_never_serializes_nonfinite_results(self):
        script = ROOT / 'skills/cp-4c-restructuring-fulcrum/scripts/funding_gap.py'
        payload = dict(horizon_years=1, currency='USD', cash=1e308, forecast_fcf=1e308,
                       instruments=[dict(amount=10, years_to_maturity=1)])
        result = subprocess.run([sys.executable, '-B', str(script)], input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)
        self.assertEqual(json.loads(result.stderr)['status'], 'blocked')

    def test_package_verification_detects_tampering(self):
        import verify_package
        with tempfile.TemporaryDirectory() as scratch:
            package = Path(scratch) / 'package'
            shutil.copytree(ROOT, package)
            with patch.object(verify_package, 'ROOT', package):
                verify_package.sync_copies()
                verify_package.refresh_metadata()
                verify_package.verify_metadata()
                for relative in ('README.md', 'tests/test_regressions.py',
                                 'skills/cp-1-canonical-data-foundation/scripts/validate_handoff.py',
                                 'DEPLOY_V_COPILOT_MEMORY_PROMPT.md'):
                    path = package / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b'\nchanged\n')
                    with self.subTest(path=relative), self.assertRaises(ValueError):
                        verify_package.verify_metadata()
                    path.write_bytes(original)
                for relative in ('unexpected.txt', 'skills/unindexed.txt'):
                    path = package / relative
                    path.write_text('unlisted')
                    with self.subTest(path=relative), self.assertRaises(ValueError):
                        verify_package.verify_metadata()
                    path.unlink()
                verify_package.verify_metadata()
                index = package / verify_package.INDEX
                original = index.read_bytes()
                wrong_route = json.loads(original)
                wrong_route['skills'][0]['aliases'] = []
                index.write_text(json.dumps(wrong_route))
                with self.assertRaises(ValueError):
                    verify_package.refresh_metadata()
                index.write_bytes(original)
                verify_package.verify_metadata()


@unittest.skipUnless(os.environ.get('DEPLOY_V_INTEGRATION') == '1', 'enable integration for native PDF and DOCX dependencies')
class IntegrationTests(unittest.TestCase):
    def test_exporter_binds_current_catalyst_owner(self):
        domain = module('cp-model', 'cp_model_v3.domain')
        self.assertIn('CP-2A', domain.BundlePaths(*(Path('source.md') for _ in range(5))).by_module())
        row = dict(rank='1', event_date_or_window='2026-10-01', event='Refinancing',
                   credit_relevance='Maturity extension', source_id='S1', source_locator='p. 1', as_of='2026-09-07')
        self.assertEqual(domain._parse_catalysts([row])[0].owner, 'CP-2A')
        exporter = ROOT / 'skills/cp-model/scripts/export_cp_model_v3.py'
        with tempfile.TemporaryDirectory() as scratch:
            for option in ('--cp2a', '--cp2b'):
                args = [sys.executable, '-B', str(exporter)]
                for flag in ('--cp1', '--cp1a', '--cp1b', '--cp2', option):
                    args.extend((flag, str(Path(scratch) / 'missing.md')))
                args.extend(('--output-dir', str(Path(scratch) / 'output')))
                result = subprocess.run(args, text=True, capture_output=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                blocked = json.loads(result.stdout)
                self.assertIn('CP-2A', [item['module_id'] for item in blocked['source_artifacts']])
                self.assertFalse((Path(scratch) / 'output').exists())

    def test_real_pdf_page_names_and_containment(self):
        from pypdf import PdfWriter
        builder = module('cp-memo-credit-research-report', 'cp_memo.builder')
        renderer = module('cp-memo-credit-research-report', 'cp_memo.render_pdf')
        raster = shutil.which('pdftoppm')
        self.assertIsNotNone(raster, 'pdftoppm is required for integration checks')
        for count in (9, 10, 100):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as scratch:
                workspace = Path(scratch).resolve()
                render = workspace / 'render'; render.mkdir()
                writer = PdfWriter()
                for _ in range(count):
                    writer.add_blank_page(width=20, height=20)
                writer.write(render / 'draft.pdf')
                subprocess.run([raster, '-png', '-r', '10', str(render / 'draft.pdf'), str(render / 'page')], check=True, capture_output=True)
                pages = sorted(render.glob('page-*.png'), key=renderer._page_number)
                payload = dict(page_count=count, pages=list(map(str, pages)))
                self.assertEqual(builder._validate_session_render(payload, workspace), count)
                pages[0].unlink()
                pages[0].symlink_to(render / 'draft.pdf')
                with self.assertRaises(ValueError):
                    builder._validate_session_render(payload, workspace)


if __name__ == '__main__':
    unittest.main()

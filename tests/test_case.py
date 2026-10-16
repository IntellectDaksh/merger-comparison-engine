import json
from pathlib import Path
import unittest
from engine import ratio
from report import load_report


class RealCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=load_report()
        cls.case=cls.report['case']
        cls.obs={o['id']:o for o in cls.case['observations']}
        cls.metrics={m['id']:m for m in cls.report['analysis']['metrics']}

    def test_source_and_locator_for_every_observation(self):
        sources={s['id']:s for s in self.case['sources']}
        for row in self.obs.values():
            self.assertIn(row['sourceId'],sources)
            self.assertTrue(row['locator'])
            self.assertIs(row['reviewed'],True)
            self.assertEqual(sources[row['sourceId']]['retrievedAt'],'2026-10-16')

    def test_predecessor_subtotals_reconcile(self):
        for metric,total in [('net_advances',651384),('deposits',915159)]:
            values=[self.obs[f'{entity}:2019-03-31:{metric}']['value'] for entity in ['bob','vijaya','dena']]
            self.assertEqual(sum(values),total)
            self.assertEqual(self.obs[f'combined:2019-03-31:{metric}']['value'],total)

    def test_reported_ratios_reconcile_to_source_rounding(self):
        self.assertAlmostEqual(self.metrics['gross_npa_ratio']['baseline'],10.020291649471807)
        self.assertAlmostEqual(self.metrics['gross_npa_ratio']['post'],9.39999674838736)
        for metric in ['gross_npa_ratio','net_npa_ratio','cost_to_income','casa']:
            self.assertLess(abs(self.metrics[metric]['post']-self.metrics[metric]['reported_post']),.0051)
        self.assertLess(abs(self.obs['combined:2020-03-31:gnpa_amount']['value']-self.obs['combined:2020-03-31:gnpa_amount_audited']['value']),.5)

    def test_case_peer_calculation_and_all_waterfalls_reconcile(self):
        metric=self.metrics['gross_npa_ratio']
        self.assertAlmostEqual(metric['sector'],-2.485)
        self.assertAlmostEqual(metric['residual'],1.864705098915553)
        for metric in self.metrics.values():
            if 'reconciliation_error' in metric:
                self.assertAlmostEqual(metric['reconciliation_error'],0)
                self.assertIsNone(metric['accounting'])
                self.assertIsNone(metric['one_off'])

    def test_latest_divergence_does_not_erase_original(self):
        self.assertEqual(self.obs['combined:2019-03-31:gnpa_rbi_assessed']['value'],71972)
        self.assertEqual(self.obs['combined:2019-03-31:gnpa_rbi_assessed_superseded']['value'],75174)
        self.assertEqual(self.obs['combined:2019-03-31:gnpa_divergence']['value'],2048)
        self.assertEqual(self.metrics['gross_npa_ratio']['operands']['baseline']['numerator'],69924)

    def test_missing_global_acquirer_and_unsupported_metrics_not_filled(self):
        self.assertIsNone(self.metrics['casa']['acquirer'])
        for key in ['roe','book_value_per_share','cost_of_funds']:
            self.assertIsNone(self.metrics[key]['post'])
        self.assertTrue(all(m['verdict']=='Too early to tell' for m in self.metrics.values()))

    def test_nim_is_annual_not_quarterly(self):
        self.assertEqual(self.metrics['nim']['baseline'],2.64)
        self.assertEqual(self.metrics['nim']['post'],2.73)
        self.assertNotIn('mechanical',self.metrics['nim'])

    def test_legal_matrix_has_exact_provisions_actions_and_links(self):
        rows=self.report['legal']['rows']
        self.assertGreaterEqual(len(rows),20)
        for row in rows:
            self.assertTrue(row['provision'])
            self.assertTrue(row['effective_date'])
            self.assertTrue(row['required_action'])
            self.assertTrue(row['evidence_urls'])
            self.assertIsInstance(row['legal_review_needed'],bool)


if __name__=='__main__': unittest.main()

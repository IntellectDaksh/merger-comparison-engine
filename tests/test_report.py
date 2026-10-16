import unittest
from report import evaluate_operand, build_report, export_html, validate_case


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(id='n',value=200,unit='INR lakh',period='2020-03-31',basis='standalone',sourceId='s'), dict(id='d',value=100,unit='INR crore',period='2020-03-31',basis='standalone',sourceId='s')]

    def test_unit_normalization_before_ratio(self):
        out = evaluate_operand(dict(numerator=['n'],denominator=['d']), self.rows)
        self.assertEqual(out['value'], 2)
        self.assertEqual(out['sources'], ['s'])

    def test_no_cross_period_or_basis_aggregation(self):
        self.rows[1]['period']='2019-03-31'
        self.assertIsNone(evaluate_operand(dict(numerator=['n'],denominator=['d']),self.rows)['value'])
        self.rows[1]['period']='2020-03-31'
        self.rows[1]['basis']='consolidated'
        self.assertIsNone(evaluate_operand(dict(numerator=['n'],denominator=['d']),self.rows)['value'])

    def test_missing_reference_blocks_ratio(self):
        self.assertIsNone(evaluate_operand(dict(numerator=['missing'],denominator=['d']),self.rows)['value'])

    def test_export_escapes_document_content(self):
        report=build_report(dict(name='<script>alert(1)</script>',observations=[],sources=[],comparisons=[]),dict(rows=[]))
        html=export_html(report)
        self.assertNotIn('<script>',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('Too early to tell',html)

    def test_all_required_metrics_remain_visible_when_missing(self):
        report=build_report(dict(name='Empty case',observations=[],sources=[],comparisons=[]),dict(rows=[]))
        ids={m['id'] for m in report['analysis']['metrics']}
        self.assertTrue({'gross_npa_ratio','net_npa_ratio','nim','roa','roe','cost_to_income','casa','cost_of_funds','capital_adequacy','eps','book_value_per_share','provision_coverage','credit_cost'}.issubset(ids))
        self.assertTrue(all(m['post'] is None for m in report['analysis']['metrics']))

    def test_unreviewed_duplicate_and_unsourced_case_rejected(self):
        case=dict(asOf='2020-12-31',observations=self.rows,sources=[],comparisons=[])
        with self.assertRaises(ValueError): validate_case(case)

    def test_report_filters_publications_after_cutoff(self):
        rows=[dict(id='r',entity='a',period='2020-03-31',metric='gnpa_ratio',value=5,unit='percent',basis='standalone',sourceId='s',locator='p1',reviewed=True)]
        case=dict(asOf='2020-05-01',observations=rows,sources=[dict(id='s',url='https://example.org',publishedDate='2020-06-01')],comparisons=[dict(id='gross_npa_ratio',post=dict(reported=['r']))])
        report=build_report(case,dict(rows=[]))
        self.assertIsNone(report['analysis']['metrics'][0]['post'])

    def test_no_genuine_from_user_flags_without_evidence(self):
        row=dict(entity='a',period='2020-03-31',metric='gnpa_ratio',unit='percent',basis='standalone',sourceId='s',locator='p1',reviewed=True)
        obs=[dict(row,id='pre',value=10),dict(row,id='post',value=5)]
        conf=dict(id='gross_npa_ratio',acquirer=dict(reported=['pre']),baseline=dict(reported=['pre']),post=dict(reported=['post']),post_quarters=4,uncertainty=dict(half_width=.1),evidence_gates=dict(comparable=True,independent_evidence=True,peer_robust=True,persistent=True))
        report=build_report(dict(asOf='2020-12-31',observations=obs,sources=[dict(id='s',url='https://example.org',publishedDate='2020-04-01')],comparisons=[conf]),dict(rows=[]))
        self.assertEqual(report['analysis']['metrics'][0]['verdict'],'Too early to tell')

    def test_reported_money_cannot_be_displayed_as_percentage(self):
        out=evaluate_operand(dict(reported=['n'],expected_unit='%'),self.rows)
        self.assertIsNone(out['value'])

    def test_operating_income_subtracts_interest_expense(self):
        rows=[dict(id=i,value=v,unit='INR crore',period='2020-03-31',basis='standalone',sourceId='s') for i,v in [('cost',20),('interest',100),('other',10),('funding',60)]]
        out=evaluate_operand(dict(numerator=['cost'],denominator=['interest','other'],denominator_subtract=['funding']),rows)
        self.assertEqual(out['value'],40)

    def test_annual_and_quarterly_flows_cannot_be_mixed(self):
        self.rows[0]['period_start']='2019-04-01'
        self.rows[1]['period_start']='2020-01-01'
        self.assertIsNone(evaluate_operand(dict(numerator=['n'],denominator=['d']),self.rows)['value'])


if __name__=='__main__': unittest.main()

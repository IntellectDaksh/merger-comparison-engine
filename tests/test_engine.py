import unittest
from engine import ratio, aggregate_ratio, choose_observation, ratio_bridge, peer_comparison, waterfall, verdict


class CalculationTests(unittest.TestCase):
    def test_fictional_gnpa_reconstructs_amounts_not_average_ratios(self):
        self.assertEqual(aggregate_ratio([(2, 100), (.6, 60)]), 1.625)

    def test_fictional_nim_uses_same_period_interest_earning_assets(self):
        self.assertAlmostEqual(aggregate_ratio([(4.1 / 100 * 120, 120), (3 / 100 * 70, 70)]), 3.694736842105263)

    def test_missing_is_not_zero_and_invalid_denominator_rejected(self):
        self.assertIsNone(ratio(None, 100))
        self.assertIsNone(aggregate_ratio([(2, 100), (None, 60)]))
        for bad in [0, -1, float('nan')]:
            with self.assertRaises(ValueError):
                ratio(2, bad)

    def test_eliminations_are_applied_to_underlying_amounts(self):
        self.assertAlmostEqual(aggregate_ratio([(2, 100), (.6, 60)], eliminate=(.1, 10)), 1.6666666666666667)

    def test_restatement_retains_original_and_respects_publication_cutoff(self):
        obs = [dict(value=10, published='2020-01-01', revision=0), dict(value=12, published='2020-06-01', revision=1)]
        self.assertEqual(choose_observation(obs, '2020-02-01')['value'], 10)
        self.assertEqual(choose_observation(obs, '2020-07-01')['value'], 12)
        self.assertEqual(obs[0]['value'], 10)
        self.assertIsNone(choose_observation(obs, '2019-01-01'))

    def test_ratio_interaction_is_allocated_once(self):
        bridge = ratio_bridge(2, 100, 3, 200)
        self.assertAlmostEqual(bridge['numerator_effect'], .75)
        self.assertAlmostEqual(bridge['denominator_effect'], -1.25)
        self.assertAlmostEqual(bridge['total'], -.5)
        self.assertAlmostEqual(bridge['reconciliation_error'], 0)

    def test_peer_uses_median_changes_and_leave_one_out(self):
        out = peer_comparison([dict(name='a', pre=5, post=4), dict(name='b', pre=7, post=5), dict(name='c', pre=4, post=1)], observed=-.5)
        self.assertEqual(out['median_change'], -2)
        self.assertEqual(out['residual'], 1.5)
        self.assertEqual(len(out['sensitivity']), 3)
        self.assertEqual(out['residual_range'], [1.0, 2.0])

    def test_unpaired_peer_is_excluded(self):
        out = peer_comparison([dict(name='a', pre=None, post=4)], observed=-.5)
        self.assertIsNone(out['median_change'])
        self.assertEqual(out['rows'], [])

    def test_waterfall_reconciles_without_claiming_missing_effects_zero(self):
        out = waterfall(2, 1.625, 1.5, sector=-.1)
        self.assertAlmostEqual(out['mechanical'], -.375)
        self.assertAlmostEqual(out['residual'], -.025)
        self.assertAlmostEqual(out['reconciliation_error'], 0)
        self.assertEqual(out['unquantified'], ['accounting', 'one_off'])

    def test_short_history_and_transition_block_genuine(self):
        self.assertEqual(verdict(direction='lower', observed=-1, residual=-.8, uncertainty=.1, post_quarters=3, comparable=True, independent_evidence=True, peer_robust=True, persistent=True), 'Too early to tell')
        self.assertEqual(verdict(direction='lower', observed=-1, residual=-.8, uncertainty=.1, post_quarters=8, comparable=True, independent_evidence=True, peer_robust=True, persistent=True, transition=True), 'Too early to tell')

    def test_residual_alone_never_proves_genuine(self):
        self.assertEqual(verdict(direction='lower', observed=-1, residual=-.8, uncertainty=.1, post_quarters=8, comparable=True, peer_robust=True, persistent=True), 'Too early to tell')

    def test_verdict_rules_cover_meaningful_cases(self):
        common = dict(direction='lower', uncertainty=.1, post_quarters=8, comparable=True, independent_evidence=True, peer_robust=True, persistent=True)
        self.assertEqual(verdict(observed=-1, residual=-.8, **common), 'Genuine')
        self.assertEqual(verdict(observed=-1, residual=.4, **common), 'Masked deterioration')
        self.assertEqual(verdict(observed=-1, residual=-.01, **common), 'Optical')
        self.assertEqual(verdict(observed=-1, residual=-.3, **common), 'Mixed')


if __name__ == '__main__':
    unittest.main()

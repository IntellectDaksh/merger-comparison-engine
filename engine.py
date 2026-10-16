"""Auditable calculations. Ratios are percentages; changes are percentage points."""
from datetime import date
from math import isfinite
from statistics import median


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError('Expected a finite number')
    return value


def ratio(numerator, denominator, scale=100):
    if numerator is None or denominator is None:
        return None
    if number(denominator) <= 0:
        raise ValueError('Denominator must be positive')
    return number(numerator) / denominator * number(scale)


def aggregate_ratio(pairs, eliminate=(0, 0), scale=100):
    """Caller must align periods, definitions and units before aggregation."""
    if not pairs or any(n is None or d is None for n, d in pairs):
        return None
    for n, d in pairs:
        number(n)
        if number(d) <= 0:
            raise ValueError('Each component denominator must be positive')
    return ratio(sum(n for n, _ in pairs) - number(eliminate[0]),
                 sum(d for _, d in pairs) - number(eliminate[1]), scale)


def choose_observation(observations, as_of):
    cutoff = date.fromisoformat(as_of)
    eligible = [o for o in observations if date.fromisoformat(o['published']) <= cutoff]
    return max(eligible, key=lambda o: (o.get('revision', 0), o['published']), default=None)


def ratio_bridge(n0, d0, n1, d1):
    """Symmetric (Shapley) allocation of numerator/denominator interaction."""
    r00, r10 = ratio(n0, d0), ratio(n1, d0)
    r01, r11 = ratio(n0, d1), ratio(n1, d1)
    if any(v is None for v in (r00, r10, r01, r11)):
        return None
    n_effect = ((r10 - r00) + (r11 - r01)) / 2
    d_effect = ((r01 - r00) + (r11 - r10)) / 2
    return dict(numerator_effect=n_effect, denominator_effect=d_effect,
                total=r11 - r00, reconciliation_error=(r11-r00)-n_effect-d_effect,
                interpretation='Arithmetic allocation, not attribution to merger causation.')


def peer_comparison(peers, observed):
    rows = []
    for peer in peers:
        if peer.get('pre') is not None and peer.get('post') is not None:
            rows.append({**peer, 'change': number(peer['post']) - number(peer['pre'])})
    if not rows:
        return dict(rows=[], method='Median of matched changes', median_change=None,
                    residual=None, sensitivity=[], residual_range=None,
                    pretrend_note='Insufficient paired peer observations.')
    sector = median(p['change'] for p in rows)
    scenarios = []
    if len(rows) > 1:
        for excluded in rows:
            change = median(p['change'] for p in rows if p is not excluded)
            scenarios.append(dict(label='Exclude '+excluded['name'], sector=change,
                                  residual=observed-change))
    residuals = [observed-sector] + [s['residual'] for s in scenarios]
    return dict(rows=rows, method='Equal-weight median of each peer’s period change',
                median_change=sector, residual=observed-sector, sensitivity=scenarios,
                residual_range=[min(residuals), max(residuals)],
                pretrend_note='One matched baseline cannot establish parallel pre-trends; no synthetic peer fitted.')


def waterfall(acquirer, baseline, post, accounting=None, one_off=None, sector=None):
    if any(v is None for v in (acquirer, baseline, post)):
        return None
    for v in (acquirer, baseline, post):
        number(v)
    effects = dict(mechanical=baseline-acquirer, accounting=accounting, one_off=one_off, sector=sector)
    for v in effects.values():
        if v is not None:
            number(v)
    observed = post-acquirer
    residual = observed-sum(v for v in effects.values() if v is not None)
    return dict(**effects, observed_change=observed, residual=residual,
                reconciliation_error=observed-sum(v for v in effects.values() if v is not None)-residual,
                unquantified=[k for k,v in effects.items() if v is None],
                residual_label='Unexplained / unquantified effects; not a causal estimate')


def verdict(*, direction, observed, residual, uncertainty, post_quarters,
            comparable=False, independent_evidence=False, peer_robust=False,
            persistent=False, transition=False):
    if direction not in ('lower', 'higher'):
        return 'Too early to tell'
    if any(v is None for v in (observed, residual, uncertainty)):
        return 'Too early to tell'
    if uncertainty < 0:
        raise ValueError('Uncertainty must be non-negative')
    if post_quarters < 4 or transition or not all((comparable, independent_evidence, peer_robust, persistent)):
        return 'Too early to tell'
    sign = -1 if direction == 'lower' else 1
    improvement, adjusted = sign*observed, sign*residual
    if improvement > uncertainty and adjusted < -uncertainty:
        return 'Masked deterioration'
    if improvement > uncertainty and abs(adjusted) <= uncertainty:
        return 'Optical'
    if adjusted > uncertainty and improvement > 0:
        return 'Genuine' if adjusted/improvement >= .5 else 'Mixed'
    return 'Mixed'

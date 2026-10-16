"""Evidence references, deterministic calculations and a portable report."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
from engine import number, ratio, ratio_bridge, peer_comparison, waterfall, verdict
from ingestion import safe_url

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    ('gross_npa_ratio','Gross NPA','lower'), ('net_npa_ratio','Net NPA','lower'),
    ('slippage_ratio','Slippages','lower'), ('credit_cost','Credit cost','lower'),
    ('provision_coverage','Provision coverage','higher'), ('nim','Net interest margin','higher'),
    ('roa','Return on assets','higher'), ('roe','Return on equity','higher'),
    ('cost_to_income','Cost to income','lower'), ('casa','CASA deposit mix','higher'),
    ('cost_of_funds','Cost of funds','lower'), ('capital_adequacy','Capital adequacy','higher'),
    ('cet1','CET1 capital','higher'), ('eps','Earnings per share','higher'),
    ('book_value_per_share','Book value per share','higher')]
RULES = [
    'Ratios are reconstructed from underlying aligned amounts; never average reported ratios.',
    'Genuine requires at least four post-merger quarters, ended transition relief, comparable definitions, a robust peer result outside uncertainty, persistence, and independent operational evidence.',
    'Only after those evidence gates: Genuine if more than half the positive headline change survives; Mixed if a smaller positive portion survives; Optical if the adjusted signal lies within uncertainty; Masked deterioration if the headline improves while the adjusted signal deteriorates outside uncertainty.',
    'Otherwise Too early to tell means insufficient evidence, including historical cases with incomplete data. An unexplained residual alone never establishes a Genuine verdict.',
    'Unknown accounting and one-off effects stay unquantified inside the residual. The bridge reconciles arithmetic, not causal identification.',
    'No overall Genuine finding unless every material domain is supported and passes the gates. Missing domains keep the overall finding Too early to tell.'
]


def validate_case(case):
    """Reject unsafe evidence, while preserving explicitly unknown publication dates."""
    date.fromisoformat(case.get('asOf','2026-10-16'))
    sources=case.get('sources',[])
    source_ids=[s['id'] for s in sources]
    if len(source_ids)!=len(set(source_ids)):
        raise ValueError('Duplicate source IDs')
    for source in sources:
        if not safe_url(source.get('url','')) and not source.get('uploadedFileSha256'):
            raise ValueError('Missing source location')
        if source.get('publishedDate'): date.fromisoformat(source['publishedDate'])
    seen=set()
    for observation in case.get('observations',[]):
        if observation.get('id') in seen:
            raise ValueError('Duplicate observation ID')
        seen.add(observation.get('id'))
        for key in ('id','entity','period','metric','unit','basis','sourceId','locator'):
            if not observation.get(key): raise ValueError('Observation missing '+key)
        number(observation.get('value'))
        date.fromisoformat(observation['period'])
        if observation.get('reviewed') is not True or observation['sourceId'] not in source_ids:
            raise ValueError('Unreviewed or unsourced observation: '+observation['id'])
    for comparison in case.get('comparisons',[]):
        if any(type(value) is not bool for value in comparison.get('evidence_gates',{}).values()):
            raise ValueError('Evidence flags must be actual booleans')


def evaluate_operand(spec, observations):
    missing = dict(value=None, sources=[], arithmetic='Not available', kind='unavailable', notes=[])
    if not spec:
        return missing
    indexed = {o['id']:o for o in observations}
    ids = spec.get('reported', []) or spec.get('numerator', [])+spec.get('denominator', [])+spec.get('denominator_subtract',[])
    if isinstance(ids, str):
        ids=[ids]
    if not ids or any(i not in indexed for i in ids):
        return dict(missing, notes=['Missing observation reference; calculation blocked.'])
    rows = [indexed[i] for i in ids]
    sources = sorted({r['sourceId'] for r in rows})
    if spec.get('reported'):
        if len(rows)!=1:
            return dict(missing, notes=['Reported ratios cannot be averaged.'])
        expected=spec.get('expected_unit')
        valid_units={'%','percent'} if expected in ('%','percent') else {expected}
        if expected and rows[0]['unit'] not in valid_units:
            return dict(missing,sources=sources,notes=['Reported figure has incompatible units.'])
        return dict(value=rows[0]['value'], sources=sources, arithmetic=f"Reported observation {ids[0]} = {rows[0]['value']}", kind='reported', notes=[spec.get('note','Issuer-reported figure; underlying denominator has not been independently reconstructed.')])
    if len({r['period'] for r in rows})!=1 or len({r.get('period_start') for r in rows})!=1 or len({r['basis'] for r in rows})!=1:
        return dict(missing, sources=sources, notes=['Period, duration or accounting basis mismatch; aggregation blocked.'])
    factors={'INR crore':1, 'INR lakh':.01, 'INR million':.1}
    if any(r['unit'] not in factors for r in rows):
        return dict(missing, sources=sources, notes=['Underlying units not supported for amount reconstruction.'])
    try:
        numerator=sum(indexed[i]['value']*factors[indexed[i]['unit']] for i in spec['numerator'])-spec.get('eliminate_numerator',0)
        denominator=sum(indexed[i]['value']*factors[indexed[i]['unit']] for i in spec['denominator'])-sum(indexed[i]['value']*factors[indexed[i]['unit']] for i in spec.get('denominator_subtract',[]))-spec.get('eliminate_denominator',0)
        value=ratio(numerator,denominator,spec.get('scale',100))
    except (KeyError, TypeError, ValueError):
        return dict(missing, sources=sources, notes=['Invalid numerator or denominator; calculation blocked.'])
    return dict(value=value, numerator=numerator, denominator=denominator, sources=sources,
                arithmetic=f"({numerator:,.6f} / {denominator:,.6f}) × {spec.get('scale',100)} = {value:.8f}; amounts in INR crore. Inputs: {', '.join(ids)}.",
                kind='calculated', notes=[spec['note']] if spec.get('note') else [])


def build_report(case, legal):
    validate_case(case)
    cutoff=case.get('asOf','2026-10-16')
    # Retrieval proves availability by that date, not an earlier publication date.
    eligible_sources={s['id'] for s in case.get('sources',[]) if (s.get('publishedDate') or s.get('retrievedAt')) and (s.get('publishedDate') or s['retrievedAt'])<=cutoff}
    observations=[o for o in case.get('observations',[]) if o['sourceId'] in eligible_sources and o['period']<=cutoff]
    comparisons={c['id']:c for c in case.get('comparisons',[])}
    metrics=[]
    for metric_id,label,direction in REQUIRED:
        config=comparisons.get(metric_id,{})
        unit=config.get('unit','INR/share' if metric_id in ('eps','book_value_per_share') else '%')
        operands={stage:evaluate_operand(dict(config[stage],expected_unit=unit) if config.get(stage) else None,observations) for stage in ('acquirer','baseline','post')}
        values={stage:o['value'] for stage,o in operands.items()}
        supported=all(v is not None for v in values.values()) and all(operands[s]['kind']=='calculated' for s in ('baseline','post'))
        notes=config.get('notes',[])+[n for o in operands.values() for n in o['notes']]
        peer_rows=[]
        for peer in config.get('peers',[]):
            pre=evaluate_operand(dict(peer.get('pre',{}),expected_unit=unit),observations)
            post=evaluate_operand(dict(peer.get('post',{}),expected_unit=unit),observations)
            peer_rows.append(dict(name=peer['name'],pre=pre['value'],post=post['value'],
                                  sources=sorted(set(pre['sources']+post['sources'])),note=peer.get('note','')))
        peer=peer_comparison(peer_rows, values['post']-values['baseline']) if supported else peer_comparison([],0)
        bridge=waterfall(**values,accounting=config.get('accounting'),one_off=config.get('one_off'),sector=peer['median_change']) if supported else {}
        bridge=bridge or {}
        reason=config.get('reason','No validated comparable baseline or denominator is available for this metric.')
        uncertainty=config.get('uncertainty')
        # No automatic causal approval: an analyst's flags cannot supply missing evidence.
        # shortcut: this release lacks an independent-evidence adjudicator; add one before enabling causal verdicts.
        gates=dict(comparable=False,independent_evidence=False,peer_robust=False,persistent=False,
                   transition=config.get('evidence_gates',{}).get('transition',True))
        result=verdict(direction=direction,observed=bridge.get('observed_change'),residual=bridge.get('residual'),
                       uncertainty=(uncertainty or {}).get('half_width'),post_quarters=config.get('post_quarters',0),**gates)
        path=[]
        for point in config.get('path',[]):
            evaluated=evaluate_operand(point.get('operand'),observations)
            path.append(dict(period=point['period'],**evaluated))
        reported_post=evaluate_operand(dict(config.get('reported_post',{}),expected_unit=unit),observations)
        peer.update(config.get('peer_notes',{}))
        metrics.append(dict(id=metric_id,label=label,unit=unit,
                            direction=direction,**values,**bridge,status='supported descriptive bridge' if supported else ('reported or partial comparison' if any(v is not None for v in values.values()) else 'incomplete'),
                            definition=config.get('definition','See data dictionary; comparable amounts unavailable.'),pre_period=config.get('pre_period',case.get('analysisWindow',{}).get('prePeriod')),post_period=config.get('post_period',case.get('analysisWindow',{}).get('postPeriod')),
                            reported_post=reported_post['value'],reported_post_note='Original issuer figure; see source precision and comparability notes.',
                            verdict=result,evidence_strength=config.get('evidence_strength','Weak'),reason=reason,notes=notes,
                            arithmetic=' | '.join(stage.title()+': '+o['arithmetic'] for stage,o in operands.items()),
                            operands=operands,uncertainty=uncertainty,peer=peer,path=path,
                            sources=sorted({s for o in list(operands.values())+[reported_post] for s in o['sources']}),
                            ratio_bridge=ratio_bridge(operands['baseline']['numerator'],operands['baseline']['denominator'],operands['post']['numerator'],operands['post']['denominator']) if all('numerator' in operands[x] for x in ('baseline','post')) else None))
    sources=[]
    for s in case.get('sources',[]):
        sources.append(dict(s,page=s.get('locator',s.get('page','')), publication_date=s.get('publishedDate'),
                            extraction_method=s.get('extractionMethod'),units=s.get('units','See observations')))
    event=case.get('event',{})
    timeline=case.get('timeline',[])
    if not timeline:
        for key,label in [('announcementDate','Announcement'),('approvalDate','Approval'),('effectiveDate','Effective date'),('firstCombinedPeriod','First combined reporting period')]:
            if event.get(key): timeline.append(dict(date=event[key],label=label,description=label))
    normalized=dict(case,title=case.get('name',case.get('title','Merger Comparison Engine')),subtitle=case.get('subtitle','A source-led comparison of reported and comparable performance'),as_of=case.get('asOf','2026-10-16'),sources=sources,timeline=timeline,entities=event.get('entities',case.get('entities',[])))
    legal_rows=[]
    for row in legal.get('rows',[]):
        legal_rows.append(dict(row,entity_transaction_type=str(row.get('entities',''))+' · '+str(row.get('transaction_type','')),url=(row.get('evidence_urls') or [''])[0],action=row.get('required_action','')))
    return dict(case=normalized,analysis=dict(overall=dict(verdict='Too early to tell',evidence_strength='Weak',
                  summary=case.get('executiveFinding','The available evidence does not establish a merger-caused improvement.'),
                  reasons=case.get('limitations',[])),metrics=metrics,
                  challenge=case.get('challenge',dict(counterargument='Sector recovery and classification changes may explain reported improvement.',falsification='A reconciled baseline, stable definitions, credible peer pre-trends and persistent adjusted results would change this finding.',synergies=case.get('managementClaims',[]))),
                  methodology=dict(rules=RULES)),legal=dict(legal,rows=legal_rows))


def load_report(case_path=None):
    case=json.loads(Path(case_path or ROOT/'data/case.json').read_text(encoding='utf-8-sig'))
    legal=json.loads((ROOT/'data/legal.json').read_text(encoding='utf-8-sig'))
    return build_report(case,legal)


def fmt(value):
    if value is None: return 'Not available'
    if isinstance(value,bool): return 'Yes' if value else 'No'
    if isinstance(value,(int,float)): return f'{value:,.4f}'
    if isinstance(value,(list,dict)): return json.dumps(value,ensure_ascii=False)
    return str(value)


def export_html(report):
    e=lambda v:escape(fmt(v),quote=True)
    def table(headers,rows):
        return '<table><thead><tr>'+''.join(f'<th scope="col">{e(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{e(cell)}</td>' for cell in row)+'</tr>' for row in rows)+'</tbody></table>'
    def paragraphs(items):
        return ''.join(f'<p>{e(item)}</p>' for item in items)
    case,analysis=report['case'],report['analysis']
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Merger Comparison Engine — report</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1140px;margin:40px auto;padding:0 24px;color:#172e3a}h1,h2,h3{line-height:1.2}h2{margin-top:40px;border-top:1px solid #adb8b9;padding-top:24px}table{border-collapse:collapse;width:100%;font-size:13px;overflow-wrap:anywhere}th,td{padding:8px;text-align:left;border-bottom:1px solid #c8d0d1;vertical-align:top}th{background:#edf2f1}.tag{color:#365f61}a{color:#14596c}pre{white-space:pre-wrap;font:13px/1.5 ui-monospace,monospace}li{margin:7px 0}@media print{body{margin:0;max-width:none;font-size:11px}h2,h3{break-after:avoid}tr{break-inside:avoid}a{color:inherit}}</style><main>']
    parts += [f'<p class="tag">MERGER COMPARISON ENGINE · Historical research · As of {e(case["as_of"])}</p>',f'<h1>{e(case["title"])}</h1>',f'<h2>{e(analysis["overall"]["verdict"])}</h2>',f'<p>{e(analysis["overall"]["summary"])}</p>','<p>Facts = issuer or official disclosures. Calculations = reproducible estimates. Interpretations = evidence-limited judgments. No investment recommendation.</p>', '<h2>Merger timeline</h2><ul>']
    parts += [f'<li>{e(t.get("date"))}: {e(t.get("label"))} — {e(t.get("description",""))}</li>' for t in case['timeline']]
    parts += ['</ul><h2>Reported and comparable figures</h2><table><thead><tr><th>Metric</th><th>Acquirer</th><th>Combined baseline</th><th>Post merger</th><th>Units</th><th>Verdict / evidence</th></tr></thead><tbody>']
    for m in analysis['metrics']:
        parts.append('<tr>'+''.join(f'<td>{e(x)}</td>' for x in [m['label'],m['acquirer'],m['baseline'],m['post'],m['unit'],m['verdict']+' / '+m['evidence_strength']])+'</tr>')
    parts += ['</tbody></table>']
    for m in analysis['metrics']:
        parts += [f'<h3>{e(m["label"])}</h3>',f'<p><b>Interpretation.</b> {e(m["reason"])}</p>',f'<p><b>Calculation.</b> {e(m["arithmetic"])}</p>']
        if 'residual' in m:
            change_unit='percentage points' if m['unit'] in ('%','percent') else m['unit']
            parts += [f'<table><tr><th>Bridge component</th><th>Change ({e(change_unit)})</th></tr>']
            parts += [f'<tr><td>{e(k)}</td><td>{e(m.get(k))}</td></tr>' for k in ['mechanical','accounting','one_off','sector','residual','observed_change','reconciliation_error']]
            parts += ['</table><p>Unquantified effects remain inside the unexplained residual; unavailable does not mean zero. Additive bridge terms are sequential. The separate numerator/denominator bridge allocates interaction equally and must not be added again.</p>']
        parts += [f'<p><b>Definition.</b> {e(m["definition"])}<br>Before: {e(m["pre_period"])}; after: {e(m["post_period"])}. Original reported after: {e(m["reported_post"])} {e(m["unit"])}.</p>',paragraphs(m['notes'])]
        uncertainty=m['uncertainty'] or {}
        parts.append(f'<p><b>Uncertainty.</b> {e(uncertainty.get("note","No defensible comprehensive uncertainty bound is available."))}</p>')
        if uncertainty.get('low') is not None:
            parts.append(f'<p>Illustrative sensitivity range: {e(uncertainty["low"])} to {e(uncertainty["high"])} percentage points. This is not a statistical confidence interval.</p>')
        if m['peer']['rows']:
            parts += ['<h4>Peer comparison</h4>',table(['Peer','Before','After','Change (pp)'],[[r['name'],r['pre'],r['post'],r['change']] for r in m['peer']['rows']]),f'<p>Median change: {e(m["peer"]["median_change"])} pp.</p>',table(['Peer specification','Sector change (pp)','Unexplained change (pp)'],[[r['label'],r['sector'],r['residual']] for r in m['peer']['sensitivity']]),paragraphs([m['peer'].get('pretrend_note'),m['peer'].get('selection_note'),m['peer'].get('coincident_events')])]
        if m['ratio_bridge']:
            parts += ['<h4>Numerator / denominator explanation</h4>',table(['Component','Change (pp)'],[[key,value] for key,value in m['ratio_bridge'].items() if key!='interpretation'])]
        if m['path']:
            parts += ['<h4>Available reporting history</h4>',table(['Period','Value','Evidence type','Sources'],[[p['period'],p['value'],p['kind'],', '.join(p['sources'])] for p in m['path']])]
        parts.append('<p>Sources: '+', '.join(f'<a href="#source-{e(s)}">{e(s)}</a>' for s in m['sources'])+'</p>')
    parts += ['<h2>Challenge the result</h2>']
    parts += [f'<p><b>{e(k)}:</b> {e(v)}</p>' for k,v in analysis['challenge'].items() if k!='synergies']
    for claim in case.get('managementClaims',[]):
        parts += [f'<h3>{e(claim.get("claim"))}</h3>',f'<p><b>Announced target:</b> {e(claim.get("announcedTarget"))} [<a href="#source-{e(claim.get("sourceId"))}">{e(claim.get("sourceId"))}</a>]</p>',f'<p><b>Observed outcome:</b> {e(claim.get("outcome"))} {e(claim.get("outcomeLocator"))} [<a href="#source-{e(claim.get("outcomeSourceId"))}">{e(claim.get("outcomeSourceId"))}</a>]</p>',f'<p><b>Attribution limit:</b> {e(claim.get("caution"))}</p>']
    parts += ['<h2>Reconstruction and comparability</h2>',paragraphs(case.get('reconstruction',{}).get('unresolved',[]))]
    parts += [f'<p><b>{e(note.get("category"))}:</b> {e(note.get("note"))}</p>' for note in case.get('comparability',[])]
    parts += ['<h2>Methodology and limits</h2><ul>']+[f'<li>{e(x)}</li>' for x in RULES+case.get('limitations',[])]+['</ul><h2>Source trail</h2>']
    for source in case['sources']:
        try: url=safe_url(source.get('url',''))
        except ValueError: url=''
        parts.append(f'<p id="source-{e(source["id"])}"><b>{e(source["id"])}</b> · <a href="{e(url)}">{e(source.get("title"))}</a><br>Published: {e(source.get("publication_date") or "Unknown")}; date status: {e(source.get("publicationDateStatus"))}; period: {e(source.get("period"))}; locator: {e(source.get("page"))}; extraction: {e(source.get("extraction_method"))}; retrieved: {e(source.get("retrievedAt"))}.</p>')
    parts += ['<h2>Underlying observations (reported facts)</h2><table><tr><th>ID / entity</th><th>Period / basis</th><th>Metric</th><th>Amount / unit</th><th>Source / location</th></tr>']
    for o in case.get('observations',[]):
        parts.append('<tr>'+''.join(f'<td>{e(x)}</td>' for x in [o.get('id','')+' / '+o.get('entity',''),o.get('period','')+' / '+o.get('basis',''),o.get('metric'),str(o.get('value'))+' '+o.get('unit',''),o.get('sourceId','')+' / '+o.get('locator','')])+'</tr>')
    parts += ['</table><h2>Legal applicability matrix</h2><p>Research checklist, not clearance to publish or sell. Qualified legal review remains required. Effective dates and applicability differ by entity and transaction.</p><table><tr><th>Rule / scope</th><th>Provision / effective date</th><th>Required action</th><th>Official evidence</th></tr>']
    for row in report['legal'].get('rows',[]):
        links=[]
        for url in row.get('evidence_urls',[]):
            try: url=safe_url(url)
            except ValueError: continue
            links.append(f'<a href="{e(url)}">{e(url)}</a>')
        parts.append(f'<tr><td>{e(row.get("rule"))}<br>{e(row.get("entity_transaction_type"))}</td><td>{e(row.get("provision"))}<br>{e(row.get("effective_date"))}</td><td>{e(row.get("action"))}<br>Legal review: {e(row.get("legal_review_needed"))}</td><td>{"<br>".join(links)}</td></tr>')
    parts += ['</table></main></html>']
    return '\n'.join(parts)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Generate a portable, source-linked report')
    parser.add_argument('--case',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'real-case-report.html')
    args=parser.parse_args()
    args.output.write_text(export_html(load_report(args.case)),encoding='utf-8')
    print(args.output)

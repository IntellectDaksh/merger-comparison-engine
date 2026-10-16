# Methodology and assumptions

## The question and evidence hierarchy

The report distinguishes (1) reported facts, (2) reproducible calculations, and (3) interpretations. It does not infer causation from a before/after ratio or from a regression residual. Primary transaction schemes establish transaction type, transfer perimeter and dates. Audited issuer results outrank unaudited presentations when they conflict; presentations can supply explicitly identified combined historical amounts. Rounded presentation amounts are reconciled to audited figures within their publication precision.

The initial case is a statutory public-sector bank amalgamation. The application does not assume an NBFC loan-book purchase, capital raise or demerger is a bank merger. Keyword discovery produces candidates requiring entity and transaction review. No unrestricted internet scraping is implemented; licensing and permitted retrieval are unresolved for bulk exchange feeds.

## Pro forma and restatements

Normalize units, reporting period, accounting basis, geography, segment scope and numerator/denominator conventions. Sum amounts; subtract disclosed intercompany amounts; divide only after aggregation. Preserve original reported observations when revised figures arrive. Prefer reconciled issuer restatements only after examining their perimeter and adjustments. A simple issuer sum is not described as a fully reconciled restatement. Missing eliminations are unresolved, not proved zero.

`choose_observation` selects eligible versions by publication cutoff and revision without overwriting history. The delivered report uses explicitly named observation IDs to prevent a new revision silently changing past results. Corrections must update references after human review. A latest-known historical study contains hindsight and is not a contemporaneous trading backtest.

## Reconciled waterfall

For a ratio measured in percent:

`Post − acquirer = (combined baseline − acquirer) + quantified accounting + quantified one-offs + peer median change + unexplained/unquantified remainder`.

The mechanical term is a change of reporting perimeter; it is not a claim about acquisition economics. Unknown accounting and one-off contributions remain null and are carried in the residual. Arithmetic reconciliation does not make unknown effects known. Effects require disjoint support; do not add a baseline stress or numerator/denominator explanation again to the same waterfall.

The separate two-factor bridge uses the symmetric average of both ordering paths. With R(N,D)=100N/D, the numerator effect is half of `[R(N1,D0)−R(N0,D0)] + [R(N1,D1)−R(N0,D1)]`; denominator effect is the remaining symmetric term. This allocates the interaction exactly once. It explains the ratio arithmetic, not merger synergies.

## Counterfactual and uncertainty

Use the median of each eligible peer's matched period change, not the difference between cross-sectional median levels. Show leave-one-peer-out sensitivity. Peers require similar ownership/business, compatible definitions and no in-window merger. Older integrations, PCA exits, capital injections, recoveries, rate cycles and COVID-era forbearance remain confounders. Sparse pre-period observations cannot validate parallel trends or support a synthetic-control model; no synthetic weights or statistical confidence interval are fabricated.

Accounting stress scenarios change only the identified input and are labelled sensitivity assumptions. They are not a statistical uncertainty interval. The absence of a quantified uncertainty bound blocks a Genuine verdict. A directionally favourable four-quarter ratio path is not sufficient persistence evidence: the comparable, peer-adjusted effect must persist under alternative specifications and after transition relief.

## Published verdict rules

First require complete comparable inputs, at least four post-merger quarters, ended transition relief, independent operating evidence, robust plausible peers, meaningful persistence and an uncertainty band. If those are unavailable, **Too early to tell** means insufficient evidence, even for an old merger.

After these gates, test changes in the direction favourable to the metric:

- **Genuine:** positive adjusted improvement outside uncertainty, at least half of headline improvement, supported by independent evidence.
- **Mixed:** a smaller supported adjusted improvement survives, or supported effects conflict.
- **Optical:** headline improves but adjusted signal lies inside uncertainty.
- **Masked deterioration:** headline improves while the adjusted signal deteriorates outside uncertainty.
- **Too early to tell:** any required identification gate fails.

These numerical cutoffs are transparent research conventions, not economic laws. Unsupported domains prevent an overall Genuine conclusion. The delivered version deliberately reports the overall case as Too early to tell; no automatic weighted overall score is offered until all material domains are supported. The unexplained residual is never itself the independent evidence required by these rules.

The low-level rule function is tested against all five categories. The report layer currently blocks automatic causal approval for every case: independent-evidence adjudication is not implemented, and configuration booleans cannot replace it. This deliberately conservative restriction is part of this release, not a claim that every future merger is inconclusive.

## Evidence strength

Strong requires independently cross-checked source amounts, reconciled definitions and perimeter, credible peer fit, uncertainty and persistence. Moderate can support a descriptive historical calculation when primary source arithmetic reconciles but causal identification is incomplete. Weak applies to causal verdicts with incomplete comparable history, uncertain adjustments or poor peers. The case can have moderate descriptive arithmetic and weak causal evidence simultaneously.

## Uploads and review

The local review endpoint accepts at most 8 MB JSON / 5 MB document, and text PDFs at most 100 pages and 500,000 extracted characters. PDFs require optional pypdf. No macros, scripts, embedded attachments or PDF JavaScript are executed. Extracted number tokens include dates and unrelated numbers: a human must map them to metrics. Review unit, period, subtotal and source reconciliation before import. Source URLs are references only and are never automatically fetched. Nothing uploaded is stored or logged. The app is for a trusted local user; resource-isolated parsing, authentication, retention controls and operational incident handling require production engineering before public deployment.

# Verification record — 16 October 2026

## Executed

| Check | Result |
|---|---|
| `python -m unittest discover -s tests` | **42 tests passed**, no failures or skips in the supplied environment |
| `node --check public/app.js` | Passed |
| `node public/app.js --self-test` | Passed: waterfall arithmetic, unknown effects, URL validation, escaping |
| `python report.py` | Generated the standalone source-linked HTML report |
| Live local HTTP report and export endpoints | Returned 200; tests verify JSON, HTML, security headers and rejected paths |
| Browser metric selection | Cost/income selection updated values, formula, waterfall and peer limitations |
| Browser document-review submission | Returned an amalgamation candidate and numeric tokens; all review checks stayed false and the verified case was unchanged |
| Browser HTML-like text test | Script markup appeared as text; no script execution or dialog |
| Browser keyboard check | Tab reached a disclosure control with a visible solid focus outline |
| Browser narrow layout at 390 px | Page width stayed inside viewport; table regions support horizontal inspection; viewport restored |
| Optional PDF parser | Valid one-page PDF parsed; review remained mandatory |
| Vercel production site | Live report rendered from the same 114-observation snapshot; document review is hidden |

Environment: Windows, Python **3.12.14**, optional **pypdf 6.10.0**, bundled Node.js. Python standard library is sufficient except PDF extraction. No new runtime dependency was installed.

## Numerical evidence

- Fictional fixture, tests only: GNPA **1.625%** and NIM **3.6947368421%**.
- Real case: **114 observations**, **13 evidence records**, **26 legal applicability rows**.
- Verified predecessor net-advance sum: **468,819 + 130,606 + 51,959 = 651,384 crore**.
- Verified predecessor deposit sum: **638,690 + 175,817 + 100,652 = 915,159 crore**.
- GNPA combined baseline: **69,924 / 697,824 × 100 = 10.02029165%**.
- GNPA post: **69,381 / 738,096 × 100 = 9.39999675%**. Presentation GNPA reconciles to audited **69,381.43 crore** within its rounding precision.
- Combined baseline-to-post change: **−0.62029490 pp**. Selected peer median change: **−2.485 pp**. Unexplained relative movement: **+1.86470510 pp**, adverse for NPA, with substantial identification limits.
- Every supported descriptive waterfall reconciles to numerical precision. Accounting and one-off terms remain null, never silently reported as measured zero.
- Latest disclosed historical GNPA divergence **2,048 crore** is a separate stress scenario; the superseded **5,250 crore** version is retained and not used as a current adjustment.
- Annual global NIM **2.64% → 2.73%** is displayed as reported-only. Quarterly **2.67%** is not substituted for annual NIM.

## Independent review and fixes

A separate reviewer found import validation, unsupported favourable verdicts, percentage-versus-currency handling, publication cutoff and export-unit issues. The implementation now rejects unreviewed/unsourced/duplicate observations, checks reported units, respects source availability cutoffs, uses correct export change units, and blocks automatic causal approval. Regression tests cover the consequential cases. An additional annual-versus-quarterly duration test failed before the shared operand check was corrected and then passed.

## What remains unsupported or unverified

- The transaction and selected factual cells are verified; the **full predecessor-by-predecessor GNPA reconstruction is not complete**. It uses disclosed issuer-aggregated amounts with unresolved eliminations. This does not satisfy a claim of a fully reconciled three-bank historical panel.
- GNPA history comprises three combined pre-merger dates and four post-merger quarters, not 8–12 quarters on each side. Four quarterly levels are not four persistent adjusted merger effects.
- Some publication dates remain unknown; retrieval establishes availability by the research date only. Inferred exchange filing dates are labelled. Blocked documents remain indexed/manual-review evidence, not claimed as fully inspected PDFs.
- ROE, book value per share, full cost of funds and several reconstructed denominators remain unavailable. Capital, EPS, NIM and other reported-only figures are not fully decomposed.
- No synthetic control, exhaustive exchange-wide discovery, licensed scheduled ingestion, OCR or fully automated financial table extraction. Local keyword discovery and reviewed data configuration are implemented.
- The rule function exercises all five verdict categories, but **automatic report-level causal adjudication remains disabled**. A positive residual or analyst-supplied flags cannot independently establish Genuine improvement.
- No full screen-reader audit, cross-browser suite, load test, adversarial PDF resource-exhaustion test or penetration test. PDF parsing is local and size-limited, but not OS-sandboxed; use trusted/permitted documents.
- The public site is a read-only historical research demonstration, not commercial/legal clearance. CCI exemption currency, data licences, regulatory report-publishing obligations and transaction-specific approvals still require qualified review.

The visible verdict is **Too early to tell** with **Weak causal evidence**, while selected descriptive arithmetic has Moderate evidence. The output makes these limits visible instead of substituting estimates for missing facts.

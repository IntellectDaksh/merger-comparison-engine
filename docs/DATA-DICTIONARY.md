# Data dictionary

All dates are ISO calendar dates. Financial periods are historical; `asOf` is the research cutoff. INR crore = 10 million rupees; INR lakh = 0.01 crore; INR million = 0.1 crore. Percentages are stored as percentage values, not decimal fractions. Their changes are **percentage points**, not percentage growth. Missing values remain null/unavailable.

## Evidence and identifiers

| Field | Meaning |
|---|---|
| `sources[].id` | Stable local evidence key; every material observation refers to it |
| `url`, `title` | Primary issuer, exchange, regulator or government source |
| `publishedDate` | Publication date; unknown dates must remain explicitly unknown and block unattended import |
| `retrievedAt` | Research retrieval date, not the reporting date |
| `period`, `locator` | Financial period and page/table/section; observation locator overrides broad source locator |
| `extractionMethod` | Manual/web/PDF extraction and its verification limitations |
| `observations[].id` | Unique immutable reference for a reported number |
| `entity`, `metric`, `period` | Reporting entity, measure and financial period end |
| `period_start` | Start date for flow observations; mismatched quarterly and annual durations block aggregation |
| `value`, `unit`, `basis` | Amount, scale and standalone/consolidated/perimeter definition |
| `sourceId`, `locator` | Audit trail to the original number |
| `status`, revision fields | Reported, issuer-aggregated, superseded, disputed or other explicitly described evidence state |
| `comparisons[].id` | One of the supported metric IDs |
| `acquirer`, `baseline`, `post` | Operand specification with raw amount IDs or one reported observation ID |
| `numerator`, `denominator` | Arrays of amounts; sums occur before division |
| `eliminate_numerator`, `eliminate_denominator` | Disclosed eliminations in INR crore; never a guessed offset |
| `peers`, `path` | Independent observation references for counterfactuals and historical trajectories |
| `evidence_gates` | Explicit comparability, independent evidence, peer robustness, persistence and transition conditions |

## Metric definitions and applicability

| Metric | Required definition / denominator | Important comparability boundary |
|---|---|---|
| Gross NPA | Gross non-performing advances / gross advances × 100 | Match geography, classification rules, write-off treatment and date. No loan-balance inference from rounded reported ratios. |
| Net NPA | Net non-performing advances / net advances × 100 | Net amounts use regulatory deductions; do not substitute gross denominator. |
| Slippage | Fresh NPA additions / issuer-specified opening or average standard advances | Numerator period and annualization differ between issuers; require exact convention. |
| Credit cost | Credit provisions / issuer-defined average advances, annualized if quarterly | Exclude or separately identify investment provisions and non-credit items. |
| Provision coverage | Eligible provisions / relevant GNPA | Including/excluding technical write-offs are different ratios; GNPA minus NNPA is not a universally valid numerator. |
| NIM | Net interest income / average interest-earning assets, annualized | Daily/period average denominators and domestic/global scope must match. The fictional fixture assumes aligned annual rates and average earning-asset weights. |
| ROA | Profit after tax / average total assets | Quarter annualization versus annual actual; one-off/tax adjustments need underlying evidence. |
| ROE | Profit after tax / average relevant equity | Do not use closing equity as average; identify capital injections and dilution. |
| Cost to income | Operating expenses / (net interest income + other operating income) | Expenses and income must span the same quarter/year; distinguish before/after exceptional items. |
| CASA mix | Current plus savings deposits / total deposits | Domestic CASA must use domestic deposits. Not applicable to ordinary non-deposit-taking NBFCs. |
| Cost of funds | Interest expense / average interest-bearing funding, annualized | Total deposits alone are not a universal denominator. |
| Capital adequacy | Eligible regulatory capital / risk-weighted assets | Capital deductions, tier composition and RWA calculations must be harmonised; do not sum capital ratios. |
| CET1 | Eligible common equity tier 1 / relevant RWA | Bank Basel measure must not be automatically assigned to NBFCs. |
| EPS | Earnings attributable to ordinary shares / weighted-average ordinary shares | Apply documented swap/restatement rules and distinguish basic/diluted EPS. |
| BVPS | Relevant ordinary shareholders’ equity / period-end ordinary shares | Adjust share count for exchange terms and new issuance; never add predecessor BVPS. |

The current generic ratio operand accepts monetary numerator and denominator amounts in supported INR units. EPS/BVPS and capital measures can be displayed as source-reported figures; reconstruction needs separately reviewed weighted share/RWA inputs and is not silently approximated. An issuer aggregate is distinguished from a reconciled pro forma. Reported figures may be visible even where the comparable bridge is unsupported.

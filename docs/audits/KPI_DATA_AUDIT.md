# Qareena KPI & Data Audit

**Audit date:** 2026-08-31  
**Decision:** Define which numbers can anchor the next Qareena interface before Figma.  
**Overall assessment:** **Needs revision** for derived scores and confidence claims; **usable with caveats** for official observed indicators.

## Executive decision

Qareena can safely build the new interface around three observed metric families once the duplicate-grain issue is fixed:

1. published average rental value, rolled up with contract-count weighting;
2. documented rental contract count at the selected geography, property type, and period;
3. official sale indicators only where city, district, property type, and period match explicitly.

Growth can be retained after enforcing consecutive periods and adequate volume in both periods. Opportunity Score, Property Score, confidence badges, risk labels, and forecast outputs should not be primary claims in the new interface until their cohorts, calibration, and validation are redesigned.

## Evidence snapshot

| Check | Observed result | Decision impact |
|---|---:|---|
| Rental snapshot | 45,198 rows; 2019 Q1–2026 Q1 | Broad historical coverage, but not transaction-level data |
| Duplicate business-grain rows | 1,486 rows / 743 groups / 3.29% | Blocks trusted contract totals until deduplicated |
| Duplicate groups spanning datasets | 739 of 743 groups | Strong evidence of overlapping published sources |
| Duplicate groups with identical rent and deal measures | 740 of 743 groups | Likely repeated indicators rather than distinct market observations |
| Potential deal overcount | 0.71% overall; **6.46% in 2026 Q1** | Material for demand, liquidity, confidence, and scores |
| Missing district | 24.49% of rental rows | City-level analysis remains usable; neighborhood claims need explicit coverage |
| Weighted vs simple latest rent | 24,819 vs 22,293 SAR; +11.33% | Weighting materially changes the headline; method must be visible |
| Non-consecutive growth comparisons | 4,564 / 28,085 = **16.25%** | “Quarterly growth” is not always quarter-over-quarter |
| Maximum growth gap | 14 quarters | Some changes compare non-adjacent market states |
| Opportunity Score scope sensitivity, apartments | median score shift 4.44 points; median rank shift 39; max 332 | Score is relative to the active cohort, not an absolute 0–100 measure |
| Riyadh Property Score eligibility | 26 rows have prior deals below the 10-deal threshold; 4 use non-consecutive periods | Current score can promote unstable growth |
| Sale snapshot | 44 rows; one city; three districts; one property-type grouping | Suitable only for narrow matched comparables |
| Forecast | 12 periods; 2026 Q1 → 2027 Q1; “high” heuristic confidence | Scenario only; no backtest or accuracy evidence |

## Metric registry and classification

`Raw` below means a published source aggregate, not a row-level rental contract or sale deed.

| Metric | Canonical definition | Class | Current readiness | Required label / action |
|---|---|---|---|---|
| Published average rental value | Source-provided average rental value for a stated geography, unit type, and period, after the source's outlier treatment | **Raw** | Ready with source caveat | “متوسط قيمة الإيجار المنشور” |
| Rolled-up average rent | `Σ(source average rent × contract count) / Σ(contract count)` across mutually exclusive source rows | **Calculated** | Ready after deduplication | Show scope, period, weighting, and included property types |
| Rental contracts / deals | Sum of source-provided rental transaction counts in the exact selected grain | **Raw** | Blocked until deduplication | Use “عقود/صفقات إيجار موثقة”; never imply sale liquidity |
| Sale deed count | Source-provided count of sale transactions | **Raw** | Ready only in matched sale coverage | Keep separate from rental contract count |
| Average sale price per sqm | Source-provided sale price-per-sqm indicator after source processing | **Raw** | Ready only for explicit city/district/type match | Show source period independently from rental period |
| Estimated sale value | `area × matched average sale price per sqm` | **Estimated** | Conditional | “قيمة بيع تقديرية”; never “fair value” without wider comparables |
| Rental growth | `(current weighted rent − prior weighted rent) / prior weighted rent` for the same entity and cohort | **Calculated** | Needs revision | Require adjacent periods and minimum volume in both |
| Deal-count growth | Same formula on rental contract counts | **Calculated** | Needs revision | State actual comparison period; protect against source backfill |
| Market comparison / rent gap | Difference from a same-type, same-period benchmark | **Calculated** | Directionally usable | Benchmark must be same property type and geography scope |
| Opportunity Score | Percentile blend of liquidity 40%, growth 35%, and lower rent 25% | **Inference** | Not ready as headline | Rename “ترتيب نسبي للفرصة”; lock and disclose cohort |
| Riyadh Property Score | Percentile blend of growth 35%, demand 30%, affordability 20%, and heuristic risk 15% | **Inference** | Not ready | Remove calibrated-looking `/100` until validated |
| Investor strategy scores | Alternate percentile blends for balanced, yield, or growth strategies | **Inference** | Not ready | Treat as sortable presets, not independent KPIs |
| Deal Score | Weighted underwriting score from yield, price gap, cash flow/DSCR, break-even occupancy, and demand | **Estimated** | Usable only as scenario output | Show assumptions and components; do not call it market truth |
| Risk score / label | Demand percentile blended with capped absolute rent-growth volatility | **Inference** | Not ready | Rename or redesign using actual downside/risk measures |
| Coverage confidence | Threshold label based on deal count, locations, and property types | **Inference** | Needs revision | Rename “كفاية البيانات”; calculate per displayed entity |
| Underwriting confidence | Threshold label from market sample size and number of positive stress scenarios | **Inference** | Needs revision | Keep separate from data quality and model accuracy |
| Forecast confidence | Threshold label from history length and recent deal volume | **Inference** | Not validated | Rename “كفاية تاريخ التوقع”; no accuracy claim |
| Rental and demand projection | Recency-weighted, shrunk historical growth compounded into three scenarios | **Forecast** | Scenario only | Display pessimistic/base/optimistic bands and backtest status |
| Latest period | Maximum period index in the selected source or comparable panel | **Calculated** | Ready with scope | Show rental and sale “as of” dates separately |
| Source readiness / trust score | Hard-coded coverage thresholds or source scores | **Inference** | Not ready for customer UI | Keep internal until governance and calibration exist |

## High-priority findings

### 1. Rental totals are exposed to overlapping source rows — High

The snapshot has 743 duplicate groups at the intended market grain. Of those, 739 span more than one dataset and 740 repeat the exact same rent and deal measures. Summing these rows can inflate the latest displayed rental contract count by an estimated 6.46%. Average rent may remain numerically similar when the duplicate measures are identical, but demand, liquidity, confidence, and every score that consumes contract count are affected.

**Required fix:** establish a canonical observation key and source precedence rule in the snapshot builder, deduplicate before aggregation, and add uniqueness tests.

### 2. “Growth” does not consistently mean quarter-over-quarter — High

The implementation shifts to the previous available observation, not necessarily the previous quarter. Across the panel, 16.25% of computed growth comparisons are non-consecutive. One live Riyadh momentum signal compares 2026 Q1 with 2025 Q2, where the prior sample has only two deals, yet states that momentum may continue.

**Required fix:** require `current_period_index - previous_period_index == 1`, require the volume threshold in both periods, preserve missing growth as missing, and show the actual comparison label.

### 3. Scores are cohort-relative but look absolute — High

The score inputs use percentile ranks. Changing the active filter changes the population and therefore the score, even when the underlying market row is unchanged. For apartments, recalculating within the same property type changes the median rank by 39 places and as much as 332 places.

The current affordability rank also compares raw rents across different property types in some score paths. A lower-rent unit type can appear “more affordable” even though the comparison is not like-for-like.

**Required fix:** define a stable cohort: same property type, same geography tier, same period, and sufficient observations. Present the result as a relative rank or percentile and store the cohort ID with the score.

### 4. “Confidence” has three incompatible meanings — High

The product uses confidence for aggregate coverage, stress-scenario resilience, and forecast history sufficiency. None is a statistical confidence interval or calibrated probability. Using the same high/medium/low visual language implies equivalence that the methods do not support.

**Required fix:** split into:

- **Data sufficiency**: completeness, volume, recency, period continuity, and duplicate status;
- **Scenario resilience**: number of stress scenarios that pass explicit financial thresholds;
- **Forecast validation**: backtest error and prediction interval coverage.

### 5. Sale coverage cannot support broad valuation claims — High

The sale snapshot contains 44 rows, covers Riyadh only, includes three districts, and exposes one property-type grouping. It is useful as a narrow official reference when all dimensions match. It cannot support a general Saudi valuation experience or fill unmatched districts by analogy.

**Required fix:** gate sale-backed valuation by exact coverage and show “no matched sale comparable” when absent.

### 6. The product snapshot and official platform use different cadences — Medium

The local rental snapshot is quarterly through 2026 Q1. The current official REGA indicators surface describes rental metrics updated monthly and shows later 2026 coverage. The official growth indicator also describes a year-over-year, 12-month weighted-moving-average method, while Qareena currently calculates change from the previous available quarterly observation. These are different metrics and must not share the same name.

**Required fix:** name Qareena's calculation “change from prior comparable quarter” and reserve “official rental growth indicator” for the source's documented methodology.

### 7. Forecast confidence is not forecast accuracy — Medium

The forecast is a transparent deterministic scenario model, which is useful. Its “high” label is based only on at least ten periods and 200 recent deals. There is no rolling-origin backtest, MAE/MAPE, coverage test, or segment-level error report.

**Required fix:** keep forecasts behind a “Scenario” label until backtesting exists. Confidence should derive from out-of-sample error and interval coverage, not only sample volume.

## Canonical KPI contract for the new interface

Every customer-facing KPI should carry these fields:

| Field | Requirement |
|---|---|
| `metric_id` | Stable machine name |
| `display_name_ar` | Unambiguous Arabic label |
| `classification` | Raw / Calculated / Estimated / Forecast / Inference |
| `unit` | SAR, SAR/m², contracts, percentage, percentile |
| `grain` | Geography × property type × period |
| `population` | Included rental contracts or sale deeds |
| `formula` | Exact formula for non-Raw values |
| `source` | Official source or Qareena calculation |
| `as_of_period` | Exact source period |
| `comparison_period` | Exact prior period when a delta is shown |
| `cohort_id` | Stable comparison population for relative scores |
| `data_sufficiency` | Separate structured checks, not a generic confidence badge |
| `limitations` | The one caveat that changes the decision |

## Recommended KPI set for Qareena VNext

### Primary observed KPIs

1. **Weighted rental value** — after deduplication, scoped to one property type by default.
2. **Verified rental contract count** — same scope and period as the rental value.
3. **Matched official sale price per sqm** — only when exact sale coverage exists.

### Drivers

1. **Consecutive-quarter rental change** — requires adequate volume in both quarters.
2. **Contract-count change** — same continuity rule.
3. **Relative rent position** — within same property type and geography tier.

### Guardrails

1. **Data sufficiency state** — duplicate-free, consecutive, recent, and above minimum volume.
2. **Coverage state** — exact geography/type match versus fallback or unavailable.

### Secondary decision aids

- Relative opportunity percentile, clearly labeled as an inference and tied to a stable cohort.
- Underwriting scenario outputs with visible user assumptions.
- Forecast scenarios only after showing backtest status.

## Implementation order before Figma

1. Add business-grain deduplication and source precedence to the rental snapshot pipeline.
2. Add automated tests for uniqueness, period continuity, volume thresholds, and score cohort stability.
3. Create a single metric registry implementing the KPI contract above.
4. Replace generic confidence with separate data-sufficiency, resilience, and forecast-validation states.
5. Rewrite growth and signal logic to forbid non-consecutive or low-volume comparisons.
6. Rebuild Opportunity/Property Score as a stable within-cohort percentile and validate rank stability.
7. Add rolling backtests before promoting forecasts.
8. Only then map the approved KPI hierarchy into the new Qareena information architecture and Figma components.

## Sources and reproducibility

- Local rental snapshot: `data/processed/rental_market.csv.gz`
- Local sale snapshot: `data/processed/sale_market.csv.gz`
- Reproducible audit runner: `scripts/kpi_data_audit.py`
- Executed notebook: `docs/audits/kpi_data_audit.ipynb`
- Reviewed JSON output: `outputs/kpi_data_audit.json`
- Official REGA open-data page: <https://rega.gov.sa/البيانات-المفتوحة/>
- Official REGA indicator definitions: <https://rei.rega.gov.sa/ar>
- Official rental-market service: <https://rei.rega.gov.sa/ar/advanced-search/rental-market>

This audit validates the current repository snapshot and implementation. It does not certify transaction-level completeness because Qareena currently consumes published aggregate indicators rather than rental-contract or sale-deed microdata.

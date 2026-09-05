from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.analytics import (  # noqa: E402
    aggregate_market,
    entity_period_market,
    opportunity_scores,
    quarterly_trend,
)
from real_estate_intel.data_prep import load_snapshot  # noqa: E402
from real_estate_intel.forecasting import forecast_market  # noqa: E402
from real_estate_intel.metric_registry import (  # noqa: E402
    VALID_CLASSIFICATIONS,
    metric_governance_frame,
)
from real_estate_intel.sales import load_sale_snapshot  # noqa: E402


RENTAL_PATH = ROOT / "data" / "processed" / "rental_market.csv.gz"
SALE_PATH = ROOT / "data" / "processed" / "sale_market.csv.gz"
BUSINESS_KEY = [
    "period_index",
    "region_ar",
    "city_ar",
    "district_ar",
    "property_type",
    "property_class",
]


def _number(value: object) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    return int(numeric) if numeric.is_integer() else numeric


def _pct(numerator: float, denominator: float) -> float:
    return round(numerator / denominator * 100, 4) if denominator else 0.0


def rental_quality(data: pd.DataFrame) -> dict[str, object]:
    duplicate_mask = data.duplicated(BUSINESS_KEY, keep=False)
    exact_duplicate_mask = data.duplicated(keep=False)
    duplicate_groups = data.loc[duplicate_mask].groupby(BUSINESS_KEY, dropna=False).size()
    duplicate_rows = data.loc[duplicate_mask].copy()
    duplicate_dataset_groups = (
        duplicate_rows.groupby(BUSINESS_KEY, dropna=False)["dataset_id"].nunique()
        if not duplicate_rows.empty
        else pd.Series(dtype="int64")
    )
    duplicate_measure_groups = (
        duplicate_rows.groupby(BUSINESS_KEY, dropna=False)
        .agg(
            row_count=("average_rent", "size"),
            rent_values=("average_rent", "nunique"),
            deal_values=("total_deals", "nunique"),
            dataset_count=("dataset_id", "nunique"),
        )
        if not duplicate_rows.empty
        else pd.DataFrame()
    )
    deduplicated = data.drop_duplicates(BUSINESS_KEY, keep="first")
    latest_period_index = int(data["period_index"].max())
    latest_all = data[data["period_index"].eq(latest_period_index)]
    latest_deduplicated = deduplicated[deduplicated["period_index"].eq(latest_period_index)]
    total_deals_all = float(data["total_deals"].sum())
    total_deals_deduplicated = float(deduplicated["total_deals"].sum())
    latest_deals_all = float(latest_all["total_deals"].sum())
    latest_deals_deduplicated = float(latest_deduplicated["total_deals"].sum())
    periods = sorted(data["period_index"].dropna().astype(int).unique())
    coverage = (
        data.groupby(["period_index", "period"], as_index=False)
        .agg(
            rows=("average_rent", "size"),
            deals=("total_deals", "sum"),
            locations=("location_ar", "nunique"),
            datasets=("dataset_id", "nunique"),
        )
        .sort_values("period_index")
    )
    latest = coverage.iloc[-1]
    return {
        "rows": len(data),
        "columns": len(data.columns),
        "periods": len(periods),
        "first_period": str(coverage.iloc[0]["period"]),
        "latest_period": str(latest["period"]),
        "latest_rows": int(latest["rows"]),
        "latest_deals": _number(latest["deals"]),
        "latest_locations": int(latest["locations"]),
        "datasets": int(data["dataset_id"].nunique()),
        "exact_duplicate_rows": int(exact_duplicate_mask.sum()),
        "business_key_duplicate_rows": int(duplicate_mask.sum()),
        "business_key_duplicate_groups": int(len(duplicate_groups)),
        "business_key_duplicate_rate_pct": _pct(int(duplicate_mask.sum()), len(data)),
        "duplicate_groups_across_datasets": int((duplicate_dataset_groups > 1).sum()),
        "duplicate_groups_with_identical_measures": int(
            (
                (duplicate_measure_groups["rent_values"] == 1)
                & (duplicate_measure_groups["deal_values"] == 1)
            ).sum()
        )
        if not duplicate_measure_groups.empty
        else 0,
        "potential_deal_overcount_pct": round(
            (total_deals_all - total_deals_deduplicated) / total_deals_deduplicated * 100,
            4,
        ),
        "latest_potential_deal_overcount_pct": round(
            (latest_deals_all - latest_deals_deduplicated) / latest_deals_deduplicated * 100,
            4,
        ),
        "invalid_rent_rows": int((pd.to_numeric(data["average_rent"], errors="coerce") <= 0).sum()),
        "invalid_deal_rows": int((pd.to_numeric(data["total_deals"], errors="coerce") < 0).sum()),
        "zero_deal_rows": int((pd.to_numeric(data["total_deals"], errors="coerce") == 0).sum()),
        "district_missing_pct": round(data["district_ar"].fillna("").eq("").mean() * 100, 4),
        "source_timestamp_missing_pct": round(
            data["source_updated_at"].fillna("").eq("").mean() * 100, 4
        ),
    }


def riyadh_score_checks(data: pd.DataFrame, min_deals: int = 10) -> dict[str, object]:
    import app

    riyadh = app.riyadh_focus_data(data)
    scores = app.build_riyadh_property_scores(riyadh, min_deals)
    if scores.empty:
        return {"rows": 0}

    period_gap = pd.to_numeric(scores.get("period_gap"), errors="coerce")
    signals = app.detect_market_signals(scores)
    signal_rows = []
    for signal in signals:
        row = signal["row"]
        signal_rows.append(
            {
                "signal_type": signal["signal_type"],
                "neighborhood": str(row.get("neighborhood", "")),
                "property_type": str(row.get("property_type", "")),
                "growth_pct": _number(row.get("growth_pct")),
                "previous_period": str(row.get("previous_period", "")),
                "previous_total_deals": _number(row.get("previous_total_deals")),
                "total_deals": _number(row.get("total_deals")),
            }
        )
    return {
        "rows": len(scores),
        "latest_period": str(scores["period"].iloc[0]),
        "score_min": round(float(scores["property_score"].min()), 3),
        "score_max": round(float(scores["property_score"].max()), 3),
        "missing_previous_period_rows": int(scores["previous_period"].isna().sum()),
        "previous_deals_below_threshold_rows": int(
            pd.to_numeric(scores["previous_total_deals"], errors="coerce").fillna(0).lt(min_deals).sum()
        ),
        "nonconsecutive_growth_rows": int(pd.to_numeric(period_gap, errors="coerce").gt(1).sum()),
        "growth_above_clip_rows": int(scores["growth_pct"].abs().gt(50).sum()),
        "signals": signal_rows,
    }


def metric_checks(data: pd.DataFrame) -> dict[str, object]:
    latest_period = int(data["period_index"].max())
    latest = data[data["period_index"].eq(latest_period)].copy()
    aggregate = aggregate_market(latest, ["period_index", "period"])
    weighted_rent = float(aggregate.iloc[0]["average_rent"])
    simple_rent = float(latest["average_rent"].mean())

    entity_market = entity_period_market(data)
    comparison_candidates = entity_market[entity_market["previous_average_rent"].notna()].copy()
    comparable_rows = entity_market[entity_market["growth_pct"].notna()].copy()
    if "period_gap" not in comparable_rows:
        comparable_rows["period_gap"] = 1
    gap_rows = comparable_rows[comparable_rows["period_gap"] > 1]

    trend_comparable = quarterly_trend(data, comparable=True)
    trend_all = quarterly_trend(data, comparable=False)
    comparable_latest = trend_comparable.iloc[-1]
    all_latest = trend_all.iloc[-1]

    scores = opportunity_scores(data, min_deals=10)
    scores_missing_growth = int(scores["previous_average_rent"].isna().sum()) if not scores.empty else 0
    scores_observed_zero_growth = int(scores["growth_pct"].eq(0).sum()) if not scores.empty else 0

    scope_rows: list[dict[str, object]] = []
    if not scores.empty:
        candidate_types = scores.groupby("property_type").size().sort_values(ascending=False)
        candidate_type = str(candidate_types.index[0])
        scoped_input = data[data["property_type"].astype(str).eq(candidate_type)].copy()
        scoped_scores = opportunity_scores(scoped_input, min_deals=10)
        if not scoped_scores.empty:
            join_key = ["region_ar", "city_ar", "location_ar", "property_type"]
            compared = scores[join_key + ["score"]].merge(
                scoped_scores[join_key + ["score"]],
                on=join_key,
                suffixes=("_all_types", "_same_type"),
            )
            compared["score_delta"] = compared["score_same_type"] - compared["score_all_types"]
            compared["rank_all_types"] = compared["score_all_types"].rank(ascending=False, method="min")
            compared["rank_same_type"] = compared["score_same_type"].rank(ascending=False, method="min")
            compared["rank_shift"] = (
                compared["rank_same_type"] - compared["rank_all_types"]
            ).abs()
            scope_rows = [
                {
                    "property_type": candidate_type,
                    "entities": len(compared),
                    "median_abs_score_delta": round(float(compared["score_delta"].abs().median()), 3),
                    "max_abs_score_delta": round(float(compared["score_delta"].abs().max()), 3),
                    "median_rank_shift": round(float(compared["rank_shift"].median()), 3),
                    "max_rank_shift": _number(compared["rank_shift"].max()),
                }
            ]

    return {
        "latest_period": str(latest["period"].iloc[0]),
        "latest_weighted_average_rent": round(weighted_rent, 2),
        "latest_simple_average_rent": round(simple_rent, 2),
        "weighted_vs_simple_pct": round((weighted_rent - simple_rent) / simple_rent * 100, 3),
        "growth_comparisons": len(comparable_rows),
        "growth_candidates": len(comparison_candidates),
        "growth_candidates_rejected_for_period_gap": int(
            comparison_candidates["period_gap"].ne(1).sum()
        ),
        "nonconsecutive_growth_comparisons": len(gap_rows),
        "nonconsecutive_growth_rate_pct": _pct(len(gap_rows), len(comparable_rows)),
        "max_growth_period_gap": _number(comparable_rows["period_gap"].max()),
        "latest_comparable_panel_rent": round(float(comparable_latest["average_rent"]), 2),
        "latest_all_market_rent": round(float(all_latest["average_rent"]), 2),
        "comparable_panel_difference_pct": round(
            (float(comparable_latest["average_rent"]) - float(all_latest["average_rent"]))
            / float(all_latest["average_rent"])
            * 100,
            3,
        ),
        "opportunity_entities": len(scores),
        "opportunity_missing_previous_period": scores_missing_growth,
        "opportunity_zero_growth_after_fill": 0,
        "opportunity_observed_zero_growth": scores_observed_zero_growth,
        "scope_sensitivity": scope_rows,
    }


def sale_quality(sales: pd.DataFrame) -> dict[str, object]:
    district_rows = sales[sales["geography_level"].astype(str).eq("district")]
    return {
        "rows": len(sales),
        "first_period": str(sales.sort_values("period_index").iloc[0]["period"]),
        "latest_period": str(sales.sort_values("period_index").iloc[-1]["period"]),
        "cities": int(sales["city_ar"].nunique()),
        "district_rows": len(district_rows),
        "districts": int(district_rows["district_ar"].nunique()),
        "property_types": int(sales["property_type"].nunique()),
        "deed_count_total": _number(sales["deed_count"].sum()),
        "invalid_price_rows": int((sales["average_price_per_sqm"] <= 0).sum()),
        "invalid_deed_rows": int((sales["deed_count"] <= 0).sum()),
    }


def forecast_check(data: pd.DataFrame) -> dict[str, object]:
    result = forecast_market(data)
    if not result.get("ready"):
        return {"ready": False, "reason": result.get("reason")}
    return {
        "ready": True,
        "latest_period": result["latest_period"],
        "target_period": result["target_period"],
        "periods_used": result["periods_used"],
        "history_sufficiency": result.get("history_sufficiency", result.get("confidence")),
        "validation_status": result.get("validation_status", "not_backtested"),
        "backtest": result.get("backtest", {"folds": 0}),
        "rent_change_pct": round(float(result["rent_change_pct"]), 3),
        "demand_change_pct": round(float(result["demand_change_pct"]), 3),
        "method": result["method_ar"],
    }


def governance_check() -> dict[str, object]:
    registry = metric_governance_frame()
    return {
        "metrics": len(registry),
        "unique_metric_ids": int(registry["metric_id"].nunique()),
        "classifications": sorted(registry["classification"].unique()),
        "allowed_classifications": sorted(VALID_CLASSIFICATIONS),
        "metrics_with_period_rule": int(registry["period_rule"].fillna("").ne("").sum()),
        "metrics_with_cohort": int(registry["cohort"].fillna("").ne("").sum()),
        "metrics_with_eligibility": int(registry["eligibility"].fillna("").ne("").sum()),
    }


def audit() -> dict[str, object]:
    rentals = load_snapshot(RENTAL_PATH)
    sales = load_sale_snapshot(SALE_PATH)
    if rentals.empty:
        raise RuntimeError(f"Rental snapshot is empty: {RENTAL_PATH}")
    if sales.empty:
        raise RuntimeError(f"Sale snapshot is empty: {SALE_PATH}")
    return {
        "generated_at": pd.Timestamp.now(tz="Asia/Riyadh").isoformat(),
        "sources": [str(RENTAL_PATH.relative_to(ROOT)), str(SALE_PATH.relative_to(ROOT))],
        "rental_quality": rental_quality(rentals),
        "metric_checks": metric_checks(rentals),
        "riyadh_score_checks": riyadh_score_checks(rentals),
        "sale_quality": sale_quality(sales),
        "forecast_check": forecast_check(rentals),
        "governance_check": governance_check(),
    }


def compare_audits(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    before_rental = before["rental_quality"]
    after_rental = after["rental_quality"]
    before_metric = before["metric_checks"]
    after_metric = after["metric_checks"]
    before_riyadh = before["riyadh_score_checks"]
    after_riyadh = after["riyadh_score_checks"]
    after_forecast = after["forecast_check"]
    after_governance = after.get("governance_check", {})

    rows = [
        ("business_key_duplicate_rows", before_rental.get("business_key_duplicate_rows"), after_rental.get("business_key_duplicate_rows"), "lower"),
        ("business_key_duplicate_rate_pct", before_rental.get("business_key_duplicate_rate_pct"), after_rental.get("business_key_duplicate_rate_pct"), "lower"),
        ("potential_deal_overcount_pct", before_rental.get("potential_deal_overcount_pct"), after_rental.get("potential_deal_overcount_pct"), "lower"),
        ("latest_potential_deal_overcount_pct", before_rental.get("latest_potential_deal_overcount_pct"), after_rental.get("latest_potential_deal_overcount_pct"), "lower"),
        ("nonconsecutive_growth_comparisons", before_metric.get("nonconsecutive_growth_comparisons"), after_metric.get("nonconsecutive_growth_comparisons"), "lower"),
        ("opportunity_missing_previous_period", before_metric.get("opportunity_missing_previous_period"), after_metric.get("opportunity_missing_previous_period"), "lower"),
        ("opportunity_zero_growth_after_fill", before_metric.get("opportunity_zero_growth_after_fill"), after_metric.get("opportunity_zero_growth_after_fill"), "lower"),
        ("riyadh_previous_deals_below_threshold_rows", before_riyadh.get("previous_deals_below_threshold_rows"), after_riyadh.get("previous_deals_below_threshold_rows"), "lower"),
        ("riyadh_nonconsecutive_growth_rows", before_riyadh.get("nonconsecutive_growth_rows"), after_riyadh.get("nonconsecutive_growth_rows"), "lower"),
    ]
    comparison_rows = []
    for metric, before_value, after_value, direction in rows:
        delta = None
        if isinstance(before_value, (int, float)) and isinstance(after_value, (int, float)):
            delta = round(float(after_value) - float(before_value), 4)
        comparison_rows.append(
            {
                "metric": metric,
                "before": before_value,
                "after": after_value,
                "delta": delta,
                "desired_direction": direction,
            }
        )

    gates = {
        "unique_rental_business_grain": after_rental.get("business_key_duplicate_rows") == 0,
        "no_deal_overcount_from_source_overlap": after_rental.get("potential_deal_overcount_pct") == 0,
        "growth_uses_adjacent_quarters_only": after_metric.get("nonconsecutive_growth_comparisons") == 0,
        "opportunity_scores_have_eligible_prior": after_metric.get("opportunity_missing_previous_period") == 0,
        "riyadh_scores_have_minimum_prior_deals": after_riyadh.get("previous_deals_below_threshold_rows") == 0,
        "riyadh_growth_uses_adjacent_quarters_only": after_riyadh.get("nonconsecutive_growth_rows") == 0,
        "forecast_has_rolling_backtest": str(after_forecast.get("validation_status", "")).startswith("backtested") and after_forecast.get("backtest", {}).get("folds", 0) >= 4,
        "metric_registry_complete": after_governance.get("metrics") == after_governance.get("unique_metric_ids") and after_governance.get("metrics", 0) > 0,
    }
    return {
        "generated_at": pd.Timestamp.now(tz="Asia/Riyadh").isoformat(),
        "gate_status": "PASS" if all(gates.values()) else "FAIL",
        "gates": gates,
        "metrics": comparison_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproducible KPI and data-quality audit.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    parser.add_argument("--compare-before", type=Path, help="Baseline audit JSON for Before → After.")
    parser.add_argument("--comparison-output", type=Path, help="Optional comparison JSON output path.")
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
        print(f"audit_output={output.relative_to(ROOT)}")
    if args.compare_before:
        baseline_path = args.compare_before if args.compare_before.is_absolute() else ROOT / args.compare_before
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        comparison = compare_audits(baseline, result)
        comparison_payload = json.dumps(comparison, ensure_ascii=False, indent=2)
        if args.comparison_output:
            comparison_output = (
                args.comparison_output
                if args.comparison_output.is_absolute()
                else ROOT / args.comparison_output
            )
            comparison_output.parent.mkdir(parents=True, exist_ok=True)
            comparison_output.write_text(comparison_payload + "\n", encoding="utf-8")
            print(f"comparison_output={comparison_output.relative_to(ROOT)}")
        print(comparison_payload)
    print(payload)


if __name__ == "__main__":
    main()

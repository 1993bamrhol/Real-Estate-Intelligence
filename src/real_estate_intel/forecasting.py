from __future__ import annotations

import math

import pandas as pd

from real_estate_intel.analytics import aggregate_market


SCENARIO_LABELS = {
    "pessimistic": "متشائم",
    "base": "محايد",
    "optimistic": "متفائل",
}


def forecast_market(frame: pd.DataFrame, horizons: int = 4) -> dict[str, object]:
    """Produce a conservative quarterly rent and demand projection from observed history."""
    trend = aggregate_market(frame, ["period_index", "period"]).sort_values("period_index")
    trend = trend.dropna(subset=["average_rent", "total_deals"]).tail(12).copy()
    if len(trend) < 4:
        return {"ready": False, "reason": "يلزم توفر أربعة أرباع تاريخية على الأقل."}

    rent_growth = _growth_series(trend["average_rent"], -0.12, 0.12)
    demand_growth = _growth_series(trend["total_deals"], -0.30, 0.30)
    rent_rate = _weighted_rate(rent_growth, limit=0.06)
    demand_rate = _weighted_rate(demand_growth, limit=0.12)
    rent_spread = _uncertainty_spread(rent_growth, minimum=0.025, maximum=0.08)
    demand_spread = _uncertainty_spread(demand_growth, minimum=0.06, maximum=0.18)

    latest = trend.iloc[-1]
    last_period = int(latest["period_index"])
    rows: list[dict[str, object]] = []
    for scenario, direction in (("pessimistic", -1), ("base", 0), ("optimistic", 1)):
        scenario_rent_rate = _clamp(rent_rate + direction * rent_spread, -0.15, 0.15)
        scenario_demand_rate = _clamp(demand_rate + direction * demand_spread, -0.35, 0.35)
        for step in range(1, horizons + 1):
            period_index = last_period + step
            rows.append(
                {
                    "scenario": scenario,
                    "scenario_ar": SCENARIO_LABELS[scenario],
                    "period_index": period_index,
                    "period": _period_label(period_index),
                    "average_rent": float(latest["average_rent"]) * (1 + scenario_rent_rate) ** step,
                    "total_deals": max(float(latest["total_deals"]) * (1 + scenario_demand_rate) ** step, 0.0),
                    "rent_quarterly_rate_pct": scenario_rent_rate * 100,
                    "demand_quarterly_rate_pct": scenario_demand_rate * 100,
                }
            )

    forecast = pd.DataFrame(rows)
    horizon_rows = forecast[forecast["period_index"].eq(last_period + horizons)].set_index("scenario")
    base_horizon = horizon_rows.loc["base"]
    confidence = _confidence(len(trend), float(trend.tail(4)["total_deals"].sum()))
    return {
        "ready": True,
        "history": trend,
        "forecast": forecast,
        "latest_period": str(latest["period"]),
        "target_period": str(base_horizon["period"]),
        "current_rent": float(latest["average_rent"]),
        "current_demand": float(latest["total_deals"]),
        "forecast_rent": float(base_horizon["average_rent"]),
        "forecast_demand": float(base_horizon["total_deals"]),
        "rent_change_pct": _pct(float(base_horizon["average_rent"]), float(latest["average_rent"])),
        "demand_change_pct": _pct(float(base_horizon["total_deals"]), float(latest["total_deals"])),
        "confidence": confidence,
        "periods_used": len(trend),
        "method_ar": "اتجاه ربعي حديث مخفّض الأثر مع نطاق عدم يقين مشتق من تذبذب التاريخ.",
    }


def _growth_series(values: pd.Series, lower: float, upper: float) -> pd.Series:
    growth = pd.to_numeric(values, errors="coerce").pct_change(fill_method=None)
    return growth.replace([math.inf, -math.inf], pd.NA).dropna().clip(lower=lower, upper=upper)


def _weighted_rate(growth: pd.Series, limit: float) -> float:
    if growth.empty:
        return 0.0
    recent = growth.tail(8)
    weights = pd.Series(range(1, len(recent) + 1), index=recent.index, dtype="float64")
    observed = float((recent * weights).sum() / weights.sum())
    # Shrink noisy historical movement toward zero to avoid false precision.
    reliability = min(len(recent) / 8, 1.0) * 0.55
    return _clamp(observed * reliability, -limit, limit)


def _uncertainty_spread(growth: pd.Series, minimum: float, maximum: float) -> float:
    if growth.empty:
        return minimum
    median = float(growth.median())
    mad = float((growth - median).abs().median())
    return _clamp(mad * 1.5, minimum, maximum)


def _confidence(periods: int, recent_deals: float) -> str:
    if periods >= 10 and recent_deals >= 200:
        return "high"
    if periods >= 6 and recent_deals >= 60:
        return "medium"
    return "low"


def _period_label(period_index: int) -> str:
    year = (period_index - 1) // 4
    quarter = period_index - year * 4
    return f"{year} Q{quarter}"


def _pct(current: float, previous: float) -> float:
    return (current - previous) / previous * 100 if previous > 0 else 0.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)

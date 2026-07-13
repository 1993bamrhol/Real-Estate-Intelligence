from __future__ import annotations

import pandas as pd


def rank_alternatives(
    scores: pd.DataFrame,
    *,
    selected_neighborhood: str,
    property_type: str,
    purchase_price: float,
    top_n: int = 3,
) -> pd.DataFrame:
    if scores.empty or purchase_price <= 0:
        return pd.DataFrame()

    scoped = scores[scores["property_type"].astype(str).eq(str(property_type))].copy()
    if scoped.empty:
        return scoped
    selected_key = _normalized(selected_neighborhood)
    selected = scoped[scoped["neighborhood"].map(_normalized).eq(selected_key)]
    selected_yield = (
        float(selected.iloc[0]["average_rent"]) / purchase_price * 100 if not selected.empty else 0.0
    )
    selected_risk = float(selected.iloc[0].get("risk_score", 0)) if not selected.empty else 0.0

    candidates = scoped[~scoped["neighborhood"].map(_normalized).eq(selected_key)].copy()
    if candidates.empty:
        return candidates
    candidates["gross_yield_pct"] = candidates["average_rent"] / purchase_price * 100
    if "risk_score" not in candidates:
        candidates["risk_score"] = candidates.get("demand_rank", 0) * 100
    candidates["yield_rank"] = candidates["gross_yield_pct"].rank(pct=True)
    candidates["safety_rank"] = candidates["risk_score"].rank(pct=True)
    candidates["demand_rank_local"] = candidates["total_deals"].rank(pct=True)
    candidates["alternative_score"] = (
        candidates["yield_rank"] * 45
        + candidates["safety_rank"] * 30
        + candidates["demand_rank_local"] * 25
    )
    candidates["yield_advantage_pct"] = candidates["gross_yield_pct"] - selected_yield
    candidates["safety_advantage"] = candidates["risk_score"] - selected_risk
    candidates["why_ar"] = candidates.apply(_alternative_reason, axis=1)
    columns = [
        "neighborhood",
        "property_type",
        "average_rent",
        "total_deals",
        "gross_yield_pct",
        "risk_score",
        "yield_advantage_pct",
        "safety_advantage",
        "alternative_score",
        "why_ar",
    ]
    return candidates.sort_values("alternative_score", ascending=False).head(top_n)[columns].reset_index(drop=True)


def _alternative_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if float(row.get("yield_advantage_pct", 0)) > 0.1:
        reasons.append("عائد أعلى")
    if float(row.get("safety_advantage", 0)) > 3:
        reasons.append("مخاطرة أقل")
    if float(row.get("demand_rank_local", 0)) >= 0.7:
        reasons.append("طلب أقوى")
    return "، ".join(reasons) or "توازن أفضل بين العائد والسيولة"


def _normalized(value: object) -> str:
    return str(value or "").strip().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")

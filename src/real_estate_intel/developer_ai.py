from __future__ import annotations

from dataclasses import dataclass, replace
import math
import re

import pandas as pd

from real_estate_intel.analytics import aggregate_market


@dataclass(frozen=True)
class DevelopmentAssumptions:
    land_area_sqm: float
    land_cost: float
    floor_area_ratio: float
    saleable_efficiency_pct: float
    average_unit_area_sqm: float
    construction_cost_per_sqm: float
    sale_price_per_sqm: float
    annual_rent_per_unit: float
    occupancy_pct: float = 90.0
    soft_cost_pct: float = 12.0
    contingency_pct: float = 7.0
    marketing_pct: float = 3.0
    finance_pct: float = 8.0
    development_years: float = 2.0
    target_margin_pct: float = 20.0
    demand_rank: float = 0.5
    market_sample_size: int = 0


def analyze_development(assumptions: DevelopmentAssumptions) -> dict[str, float | str | list[str]]:
    metrics = _development_metrics(assumptions)
    score = _development_score(metrics, assumptions)
    decision = "proceed" if score >= 72 else "redesign" if score >= 52 else "reject"

    warnings: list[str] = []
    if metrics["profit"] <= 0:
        warnings.append("إيراد البيع المتوقع لا يغطي التكلفة الكلية.")
    if metrics["margin_pct"] < assumptions.target_margin_pct:
        warnings.append("هامش المشروع أقل من الهامش المستهدف.")
    if metrics["units"] < 1:
        warnings.append("مساحة المشروع لا تنتج وحدة كاملة وفق الافتراضات الحالية.")
    if assumptions.market_sample_size < 30:
        warnings.append("مرجعية السوق محدودة؛ تحقق ميدانيًا من الأسعار والطلب.")
    if assumptions.sale_price_per_sqm <= metrics["break_even_sale_price_per_sqm"] * 1.05:
        warnings.append("هامش الأمان السعري ضعيف أمام ارتفاع التكلفة أو انخفاض سعر البيع.")

    return {
        **metrics,
        "development_score": score,
        "decision": decision,
        "confidence": _confidence(assumptions.market_sample_size),
        "warnings": warnings,
    }


def stress_test_development(assumptions: DevelopmentAssumptions) -> dict[str, object]:
    scenarios = (
        ("downside", "متحفظ", -12.0, 12.0, 6.0),
        ("base", "أساسي", 0.0, 0.0, 0.0),
        ("upside", "متفائل", 8.0, -3.0, -4.0),
    )
    rows: list[dict[str, float | str]] = []
    for code, label, price_change, cost_change, occupancy_change in scenarios:
        scenario = replace(
            assumptions,
            sale_price_per_sqm=max(assumptions.sale_price_per_sqm * (1 + price_change / 100), 0.0),
            construction_cost_per_sqm=max(
                assumptions.construction_cost_per_sqm * (1 + cost_change / 100), 0.0
            ),
            occupancy_pct=_clamp(assumptions.occupancy_pct + occupancy_change, 40.0, 100.0),
        )
        result = analyze_development(scenario)
        rows.append(
            {
                "scenario": code,
                "label": label,
                "revenue": float(result["sale_revenue"]),
                "total_cost": float(result["total_cost"]),
                "profit": float(result["profit"]),
                "margin_pct": float(result["margin_pct"]),
                "roi_pct": float(result["roi_pct"]),
                "development_score": float(result["development_score"]),
                "decision": str(result["decision"]),
            }
        )

    profitable = sum(float(row["profit"]) > 0 for row in rows)
    downside = rows[0]
    return {
        "scenarios": rows,
        "resilience_pct": profitable / len(rows) * 100,
        "downside_profit": float(downside["profit"]),
        "downside_margin_pct": float(downside["margin_pct"]),
        "survives_downside": float(downside["profit"]) > 0,
    }


def recommend_product_mix(
    frame: pd.DataFrame,
    *,
    total_units: int,
    top_n: int = 4,
) -> pd.DataFrame:
    columns = [
        "property_type",
        "allocation_pct",
        "recommended_units",
        "average_rent",
        "total_deals",
        "growth_pct",
        "market_score",
        "reason",
    ]
    if frame.empty or total_units <= 0:
        return pd.DataFrame(columns=columns)

    market = aggregate_market(frame, ["period_index", "period", "property_type"])
    if market.empty:
        return pd.DataFrame(columns=columns)
    market = market.sort_values(["property_type", "period_index"]).copy()
    market["previous_rent"] = market.groupby("property_type")["average_rent"].shift(1)
    market["growth_pct"] = (
        (market["average_rent"] - market["previous_rent"]) / market["previous_rent"] * 100
    )
    latest = market[market["period_index"].eq(market["period_index"].max())].copy()
    latest = latest.dropna(subset=["average_rent", "total_deals"])
    if latest.empty:
        return pd.DataFrame(columns=columns)

    latest["demand_rank"] = latest["total_deals"].rank(pct=True)
    latest["growth_rank"] = latest["growth_pct"].fillna(0).clip(-50, 50).rank(pct=True)
    latest["rent_rank"] = latest["average_rent"].rank(pct=True)
    latest["market_score"] = (
        latest["demand_rank"] * 50 + latest["growth_rank"] * 30 + latest["rent_rank"] * 20
    )
    latest = latest.sort_values("market_score", ascending=False).head(max(top_n, 1)).copy()
    score_total = float(latest["market_score"].sum())
    if score_total <= 0:
        latest["allocation_pct"] = 100 / len(latest)
    else:
        latest["allocation_pct"] = latest["market_score"] / score_total * 100

    raw_units = latest["allocation_pct"] / 100 * int(total_units)
    latest["recommended_units"] = raw_units.map(math.floor).astype(int)
    remaining = int(total_units) - int(latest["recommended_units"].sum())
    if remaining > 0:
        fractions = (raw_units - latest["recommended_units"]).sort_values(ascending=False)
        for index in fractions.index[:remaining]:
            latest.loc[index, "recommended_units"] += 1
    latest["allocation_pct"] = latest["recommended_units"] / int(total_units) * 100
    latest["reason"] = latest.apply(_mix_reason, axis=1)
    return latest[columns].reset_index(drop=True)


def build_developer_brief(
    result: dict[str, object],
    stress: dict[str, object],
    mix: pd.DataFrame,
) -> str:
    decision_labels = {
        "proceed": "انتقل إلى دراسة تفصيلية مشروطة",
        "redesign": "أعد تصميم الافتراضات قبل الالتزام",
        "reject": "لا تلتزم بالمشروع بهذه الافتراضات",
    }
    decision = decision_labels.get(str(result.get("decision")), "راجع الافتراضات")
    top_mix = "، ".join(
        f"{row['property_type']} ({int(row['recommended_units'])} وحدة)"
        for _, row in mix.head(3).iterrows()
    ) or "لا توجد بيانات كافية لاقتراح المزيج"
    downside_text = (
        "يبقى مربحًا في السيناريو المتحفظ"
        if bool(stress.get("survives_downside"))
        else "يتحول إلى خسارة في السيناريو المتحفظ"
    )
    warnings = list(result.get("warnings", []))
    warning_text = " ".join(f"- {item}" for item in warnings) or "- لا توجد إشارة حرجة ضمن الافتراضات المدخلة."
    return (
        "### توصية قرينة AI للمطور\n\n"
        f"**القرار:** {decision}. درجة التطوير {float(result['development_score']):.1f}/100 "
        f"بثقة {result['confidence']}.\n\n"
        f"**الاقتصاديات:** تكلفة كلية {float(result['total_cost']):,.0f} ر.س، قيمة تطويرية "
        f"{float(result['sale_revenue']):,.0f} ر.س، وربح متوقع {float(result['profit']):,.0f} ر.س "
        f"بهامش {float(result['margin_pct']):.1f}%. سعر التعادل {float(result['break_even_sale_price_per_sqm']):,.0f} "
        f"ر.س/م²، والحد الأعلى المقترح للأرض {float(result['max_land_bid']):,.0f} ر.س.\n\n"
        f"**الضغط:** المشروع {downside_text}؛ هامش السيناريو المتحفظ "
        f"{float(stress['downside_margin_pct']):.1f}%.\n\n"
        f"**المزيج الأولي:** {top_mix}.\n\n"
        "**تنبيهات قبل القرار:**\n"
        f"{warning_text}\n\n"
        "هذه توصية فرز أولي قابلة للتفسير، وليست دراسة هندسية أو تقييمًا معتمدًا أو التزامًا تمويليًا."
    )


def optimize_for_target_margin(
    assumptions: DevelopmentAssumptions,
    target_margin_pct: float,
) -> dict[str, float | list[dict[str, float | str]]]:
    """Calculate transparent commercial levers needed to reach a target margin."""
    target_margin_pct = _clamp(float(target_margin_pct), 1.0, 70.0)
    target = replace(assumptions, target_margin_pct=target_margin_pct)
    current = analyze_development(assumptions)
    target_view = analyze_development(target)

    saleable_area = float(current["saleable_area_sqm"])
    marketing_ratio = max(assumptions.marketing_pct, 0.0) / 100
    target_ratio = target_margin_pct / 100
    fixed_cost = float(current["total_cost"]) - float(current["sale_revenue"]) * marketing_ratio
    denominator = 1 - marketing_ratio - target_ratio
    required_revenue = fixed_cost / denominator if denominator > 0 else math.inf
    required_sale_price = required_revenue / saleable_area if saleable_area > 0 else math.inf

    max_land_cost = float(target_view["max_land_bid"])
    land_reduction = max(assumptions.land_cost - max_land_cost, 0.0)
    sale_price_increase = max(required_sale_price - assumptions.sale_price_per_sqm, 0.0)

    max_construction_cost = _max_construction_cost_for_margin(target, target_margin_pct)
    construction_reduction = max(
        assumptions.construction_cost_per_sqm - max_construction_cost,
        0.0,
    )

    levers: list[dict[str, float | str]] = [
        {
            "lever": "سعر الأرض",
            "current": float(assumptions.land_cost),
            "required": max_land_cost,
            "change": -land_reduction,
            "unit": "ر.س",
            "action": f"لا تتجاوز {max_land_cost:,.0f} ر.س للأرض",
        },
        {
            "lever": "سعر البيع للمتر",
            "current": float(assumptions.sale_price_per_sqm),
            "required": required_sale_price,
            "change": sale_price_increase,
            "unit": "ر.س/م²",
            "action": f"استهدف {required_sale_price:,.0f} ر.س/م² على الأقل",
        },
        {
            "lever": "تكلفة البناء للمتر",
            "current": float(assumptions.construction_cost_per_sqm),
            "required": max_construction_cost,
            "change": -construction_reduction,
            "unit": "ر.س/م²",
            "action": f"اخفض تكلفة البناء إلى {max_construction_cost:,.0f} ر.س/م² أو أقل",
        },
    ]
    for lever in levers:
        current_value = abs(float(lever["current"]))
        lever["change_pct"] = (
            float(lever["change"]) / current_value * 100 if current_value > 0 else 0.0
        )
        lever["gap"] = abs(float(lever["change"]))
    levers.sort(key=lambda item: abs(float(item["change_pct"])))
    return {
        "current_margin_pct": float(current["margin_pct"]),
        "target_margin_pct": target_margin_pct,
        "required_profit": required_revenue * target_ratio if math.isfinite(required_revenue) else math.inf,
        "required_sale_price_per_sqm": required_sale_price,
        "max_land_cost": max_land_cost,
        "max_construction_cost_per_sqm": max_construction_cost,
        "levers": levers,
    }


def answer_developer_question(
    question: str,
    assumptions: DevelopmentAssumptions,
    result: dict[str, object],
    stress: dict[str, object],
    mix: pd.DataFrame,
) -> str:
    """Answer common developer questions from deterministic project evidence."""
    text = str(question or "").strip()
    normalized = text.replace("٪", "%")
    requested_pct = _requested_percentage(normalized)
    target_margin = requested_pct or assumptions.target_margin_pct
    optimization = optimize_for_target_margin(assumptions, target_margin)

    if any(token in normalized for token in ("هامش", "ربح", "أصل", "اوصل", "أوصل")):
        levers = list(optimization["levers"])
        best = levers[0]
        return (
            f"للوصول إلى هامش {target_margin:.1f}% بدل {float(result['margin_pct']):.1f}%، "
            f"أقرب رافعة منفردة حسب نسبة التغيير هي: **{best['action']}**. "
            f"البدائل: أرض بحد أقصى {float(optimization['max_land_cost']):,.0f} ر.س، "
            f"أو سعر البيع عند {float(optimization['required_sale_price_per_sqm']):,.0f} ر.س/م²، "
            f"أو تكلفة بناء لا تتجاوز {float(optimization['max_construction_cost_per_sqm']):,.0f} ر.س/م². "
            "اختبر قدرة السوق والمقاول قبل اعتماد أي رافعة منفردة."
        )
    if any(token in normalized for token in ("أرض", "الارض", "سعر الشراء", "عرض")):
        return (
            f"الحد الأعلى المحسوب للأرض عند هامش مستهدف {target_margin:.1f}% هو "
            f"**{float(optimization['max_land_cost']):,.0f} ر.س**، أي "
            f"{float(optimization['max_land_cost']) / max(assumptions.land_area_sqm, 1):,.0f} ر.س/م² أرض. "
            f"السعر المدخل حاليًا {assumptions.land_cost:,.0f} ر.س."
        )
    if any(token in normalized for token in ("بيع", "المتر", "التسعير", "سعر")):
        return (
            f"سعر البيع المطلوب لتحقيق هامش {target_margin:.1f}% هو **"
            f"{float(optimization['required_sale_price_per_sqm']):,.0f} ر.س/م²**. "
            f"الافتراض الحالي {assumptions.sale_price_per_sqm:,.0f} ر.س/م²، "
            f"وسعر التعادل {float(result['break_even_sale_price_per_sqm']):,.0f} ر.س/م²."
        )
    if any(token in normalized for token in ("تكلفة", "مقاول", "بناء")):
        return (
            f"لتحقيق هامش {target_margin:.1f}% مع ثبات بقية الافتراضات، يجب ألا تتجاوز تكلفة البناء "
            f"**{float(optimization['max_construction_cost_per_sqm']):,.0f} ر.س/م²** مقابل "
            f"{assumptions.construction_cost_per_sqm:,.0f} ر.س/م² حاليًا."
        )
    if any(token in normalized for token in ("مزيج", "وحدات", "منتج", "شقق")):
        if mix.empty:
            return "لا توجد بيانات سوق كافية لتكوين مزيج وحدات موثوق في النطاق الحالي."
        items = "، ".join(
            f"{row['property_type']}: {int(row['recommended_units'])} وحدة ({float(row['allocation_pct']):.0f}%)"
            for _, row in mix.head(4).iterrows()
        )
        return f"المزيج الأولي المقترح هو: **{items}**. راجعه هندسيًا وفق المساحات والاشتراطات ومواقف السيارات."
    if any(token in normalized for token in ("مخاطر", "ضغط", "متحفظ", "أسوأ")):
        status = "يبقى مربحًا" if bool(stress.get("survives_downside")) else "يتحول إلى خسارة"
        return (
            f"في السيناريو المتحفظ، المشروع **{status}** بربح "
            f"{float(stress['downside_profit']):,.0f} ر.س وهامش {float(stress['downside_margin_pct']):.1f}%. "
            "السيناريو يفترض هبوط سعر البيع 12% وارتفاع تكلفة البناء 12%."
        )
    return (
        f"درجة المشروع {float(result['development_score']):.1f}/100 وهامشه "
        f"{float(result['margin_pct']):.1f}%. اسألني عن الهامش المستهدف، سعر الأرض، "
        "سعر البيع، تكلفة البناء، المزيج، أو سيناريو الضغط لأعطيك إجابة رقمية."
    )


def project_snapshot(
    name: str,
    assumptions: DevelopmentAssumptions,
    result: dict[str, object],
    stress: dict[str, object],
) -> dict[str, float | str]:
    return {
        "project": str(name).strip() or "مشروع بدون اسم",
        "land_area_sqm": float(assumptions.land_area_sqm),
        "land_cost": float(assumptions.land_cost),
        "units": float(result["units"]),
        "sale_revenue": float(result["sale_revenue"]),
        "total_cost": float(result["total_cost"]),
        "profit": float(result["profit"]),
        "margin_pct": float(result["margin_pct"]),
        "roi_pct": float(result["roi_pct"]),
        "annualized_return_pct": float(result["annualized_return_pct"]),
        "development_score": float(result["development_score"]),
        "decision": str(result["decision"]),
        "downside_profit": float(stress["downside_profit"]),
        "max_land_bid": float(result["max_land_bid"]),
    }


def _development_metrics(assumptions: DevelopmentAssumptions) -> dict[str, float]:
    land_area = max(float(assumptions.land_area_sqm), 0.0)
    far = max(float(assumptions.floor_area_ratio), 0.0)
    efficiency = _clamp(assumptions.saleable_efficiency_pct / 100, 0.1, 1.0)
    gross_floor_area = land_area * far
    saleable_area = gross_floor_area * efficiency
    average_unit_area = max(float(assumptions.average_unit_area_sqm), 1.0)
    units = max(math.floor(saleable_area / average_unit_area), 0)

    land_cost = max(float(assumptions.land_cost), 0.0)
    hard_cost = gross_floor_area * max(float(assumptions.construction_cost_per_sqm), 0.0)
    soft_cost = hard_cost * max(assumptions.soft_cost_pct, 0.0) / 100
    contingency = hard_cost * max(assumptions.contingency_pct, 0.0) / 100
    pre_marketing_cost = land_cost + hard_cost + soft_cost + contingency
    marketing_cost = saleable_area * max(assumptions.sale_price_per_sqm, 0.0) * max(
        assumptions.marketing_pct, 0.0
    ) / 100
    finance_ratio = max(assumptions.finance_pct, 0.0) / 100
    finance_cost = pre_marketing_cost * finance_ratio
    total_cost = pre_marketing_cost + marketing_cost + finance_cost

    sale_revenue = saleable_area * max(float(assumptions.sale_price_per_sqm), 0.0)
    effective_annual_rent = (
        units
        * max(float(assumptions.annual_rent_per_unit), 0.0)
        * _clamp(assumptions.occupancy_pct / 100, 0.0, 1.0)
    )
    profit = sale_revenue - total_cost
    margin_pct = profit / sale_revenue * 100 if sale_revenue > 0 else -100.0
    roi_pct = profit / total_cost * 100 if total_cost > 0 else 0.0
    equity_multiple = sale_revenue / total_cost if total_cost > 0 else 0.0
    annualized_return_pct = (
        (equity_multiple ** (1 / max(assumptions.development_years, 0.25)) - 1) * 100
        if equity_multiple > 0
        else -100.0
    )
    yield_on_cost_pct = effective_annual_rent / total_cost * 100 if total_cost > 0 else 0.0
    break_even_sale_price = total_cost / saleable_area if saleable_area > 0 else 0.0

    target_margin = _clamp(assumptions.target_margin_pct / 100, 0.0, 0.8)
    allowable_total_cost = sale_revenue * (1 - target_margin)
    non_land_pre_finance = hard_cost + soft_cost + contingency
    non_land_cost = non_land_pre_finance * (1 + finance_ratio) + marketing_cost
    max_land_bid = max((allowable_total_cost - non_land_cost) / (1 + finance_ratio), 0.0)
    land_cost_per_sqm = land_cost / land_area if land_area > 0 else 0.0

    return {
        "gross_floor_area_sqm": gross_floor_area,
        "saleable_area_sqm": saleable_area,
        "units": float(units),
        "land_cost": land_cost,
        "land_cost_per_sqm": land_cost_per_sqm,
        "hard_cost": hard_cost,
        "soft_cost": soft_cost,
        "contingency": contingency,
        "marketing_cost": marketing_cost,
        "finance_cost": finance_cost,
        "total_cost": total_cost,
        "sale_revenue": sale_revenue,
        "effective_annual_rent": effective_annual_rent,
        "profit": profit,
        "margin_pct": margin_pct,
        "roi_pct": roi_pct,
        "annualized_return_pct": annualized_return_pct,
        "yield_on_cost_pct": yield_on_cost_pct,
        "break_even_sale_price_per_sqm": break_even_sale_price,
        "max_land_bid": max_land_bid,
    }


def _development_score(metrics: dict[str, float], assumptions: DevelopmentAssumptions) -> float:
    margin_target = max(assumptions.target_margin_pct, 1.0)
    margin_score = _clamp(metrics["margin_pct"] / margin_target, 0, 1.25) / 1.25 * 35
    roi_score = _clamp(metrics["roi_pct"] / max(margin_target * 1.25, 1.0), 0, 1.25) / 1.25 * 20
    yield_score = _clamp(metrics["yield_on_cost_pct"] / 7.0, 0, 1.0) * 10
    demand_score = _clamp(assumptions.demand_rank, 0, 1) * 20
    safety_gap = (
        assumptions.sale_price_per_sqm / metrics["break_even_sale_price_per_sqm"] - 1
        if metrics["break_even_sale_price_per_sqm"] > 0
        else -1
    )
    safety_score = _clamp(safety_gap / 0.25, 0, 1) * 10
    confidence_score = {"مرتفعة": 5.0, "متوسطة": 3.0, "منخفضة": 1.0}[
        _confidence(assumptions.market_sample_size)
    ]
    return round(_clamp(margin_score + roi_score + yield_score + demand_score + safety_score + confidence_score, 0, 100), 1)


def _max_construction_cost_for_margin(
    assumptions: DevelopmentAssumptions,
    target_margin_pct: float,
) -> float:
    low = 0.0
    high = max(assumptions.construction_cost_per_sqm * 3, 1.0)
    for _ in range(55):
        candidate = (low + high) / 2
        metrics = _development_metrics(
            replace(assumptions, construction_cost_per_sqm=candidate)
        )
        if metrics["margin_pct"] >= target_margin_pct:
            low = candidate
        else:
            high = candidate
    return round(low, 2)


def _requested_percentage(text: str) -> float | None:
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*%?", text)
    if not matches:
        return None
    for match in matches:
        value = float(match.replace(",", "."))
        if 1 <= value <= 70:
            return value
    return None


def _mix_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if float(row.get("demand_rank", 0)) >= 0.7:
        reasons.append("طلب مرتفع")
    if float(row.get("growth_rank", 0)) >= 0.7:
        reasons.append("اتجاه إيجار قوي")
    if float(row.get("rent_rank", 0)) >= 0.7:
        reasons.append("قيمة إيجارية مرتفعة")
    return "، ".join(reasons) or "توازن نسبي بين الطلب والإيجار"


def _confidence(sample_size: int) -> str:
    if sample_size >= 150:
        return "مرتفعة"
    if sample_size >= 40:
        return "متوسطة"
    return "منخفضة"


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)

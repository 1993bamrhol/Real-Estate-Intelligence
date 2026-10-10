from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd

from real_estate_intel.analytics import opportunity_scores, quarterly_trend
from real_estate_intel.metric_registry import metric_governance_frame
from real_estate_intel.ui.contracts import presentation_term_ar


@dataclass(frozen=True)
class HomeMetric:
    metric_id: str
    label_ar: str
    value_ar: str
    evidence_ar: str
    context_ar: str


@dataclass(frozen=True)
class HomeOpportunity:
    segment_ar: str
    property_type_ar: str
    period_ar: str
    average_rent_ar: str
    total_deals_ar: str
    growth_ar: str
    growth_period_ar: str
    rent_evidence_ar: str
    deals_evidence_ar: str
    growth_evidence_ar: str
    score_ar: str
    evidence_ar: str
    cohort_ar: str
    rank_context_ar: str


@dataclass(frozen=True)
class HomeViewModel:
    available: bool
    city_ar: str
    property_type_ar: str
    period_ar: str
    scope_ar: str
    metrics: tuple[HomeMetric, ...]
    opportunities: tuple[HomeOpportunity, ...]
    source_ar: str
    limitation_ar: str
    data_message_ar: str = ""


def arabic_period_label(period: object) -> str:
    value = str(period or "").strip()
    parts = value.split()
    if len(parts) != 2 or not parts[0].isdigit():
        return value
    quarter_names = {
        "Q1": "الربع الأول",
        "Q2": "الربع الثاني",
        "Q3": "الربع الثالث",
        "Q4": "الربع الرابع",
    }
    quarter = quarter_names.get(parts[1])
    return f"{quarter} {parts[0]}" if quarter else value


def _format_number(value: object) -> str:
    return f"{float(value):,.0f}"


def _format_growth(value: object) -> str:
    if value is None or pd.isna(value):
        return "غير متاح"
    numeric = float(value)
    return f"{numeric:+.1f}%"


def _segment_label(location: object, city: str) -> str:
    value = str(location or "").strip()
    prefix = f"{city} - "
    return value[len(prefix) :] if value.startswith(prefix) else value


def _empty_home(city: str, property_type: str) -> HomeViewModel:
    return HomeViewModel(
        available=False,
        city_ar=city,
        property_type_ar=property_type,
        period_ar="",
        scope_ar=f"{city} · كل الأحياء · {property_type}",
        metrics=(),
        opportunities=(),
        source_ar="الهيئة العامة للعقار — بيانات الإيجار المفتوحة",
        limitation_ar="لا تُعرض مؤشرات قبل توفر نطاق وفترة صالحين.",
        data_message_ar="لا توجد بيانات كافية لبناء موجز الرئيسية لهذا النطاق.",
    )


def build_home_view_model(
    data: pd.DataFrame,
    *,
    city: str = "الرياض",
    property_type: str = "استديو",
    min_deals: int = 10,
) -> HomeViewModel:
    if data.empty:
        return _empty_home(city, property_type)

    scope = data[data["city_ar"].eq(city) & data["property_type"].eq(property_type)].copy()
    trend = quarterly_trend(scope, comparable=True)
    if trend.empty:
        return _empty_home(city, property_type)

    current = trend.iloc[-1]
    current_period_index = int(current["period_index"])
    current_period = str(current["period"])
    prior = trend.iloc[-2] if len(trend) > 1 else None
    growth: float | None = None
    growth_period_ar = "لا توجد فترة سابقة متصلة"
    if prior is not None and current_period_index - int(prior["period_index"]) == 1:
        prior_rent = float(prior["average_rent"])
        if prior_rent > 0 and not math.isnan(prior_rent):
            growth = (float(current["average_rent"]) / prior_rent - 1) * 100
            growth_period_ar = (
                f"من {arabic_period_label(prior['period'])} إلى {arabic_period_label(current_period)}"
            )

    registry = metric_governance_frame().set_index("metric_id")
    metrics = (
        HomeMetric(
            metric_id="weighted_average_rent",
            label_ar="متوسط الإيجار المجمّع",
            value_ar=f"{_format_number(current['average_rent'])} ر.س",
            evidence_ar=presentation_term_ar(str(registry.loc["weighted_average_rent", "classification"])),
            context_ar="مرجّح بعدد العقود في آخر فترة",
        ),
        HomeMetric(
            metric_id="rental_deals",
            label_ar="عقود الإيجار",
            value_ar=_format_number(current["total_deals"]),
            evidence_ar=presentation_term_ar(str(registry.loc["rental_deals", "classification"])),
            context_ar="مجموع العقود المنشورة في آخر فترة",
        ),
        HomeMetric(
            metric_id="quarterly_rent_growth",
            label_ar="التغير الربعي",
            value_ar=_format_growth(growth),
            evidence_ar=presentation_term_ar(str(registry.loc["quarterly_rent_growth", "classification"])),
            context_ar=growth_period_ar,
        ),
    )

    scored = opportunity_scores(scope, min_deals=min_deals)
    scored = scored[scored["period_index"].eq(current_period_index)].head(2)
    opportunities: list[HomeOpportunity] = []
    for rank, (_, row) in enumerate(scored.iterrows(), start=1):
        entity_rows = scope[
            scope["period_index"].eq(current_period_index)
            & scope["location_ar"].eq(row.get("location_ar"))
        ]
        rent_classification = "Raw" if len(entity_rows) == 1 else "Calculated"
        previous_period = arabic_period_label(row.get("previous_period"))
        score_period = arabic_period_label(row.get("period"))
        opportunities.append(
            HomeOpportunity(
                segment_ar=_segment_label(row.get("location_ar"), city),
                property_type_ar=str(row.get("property_type") or property_type),
                period_ar=score_period,
                average_rent_ar=f"{_format_number(row['average_rent'])} ر.س",
                total_deals_ar=_format_number(row["total_deals"]),
                growth_ar=_format_growth(row.get("growth_pct")),
                growth_period_ar=f"من {previous_period} إلى {score_period}",
                rent_evidence_ar=presentation_term_ar(rent_classification),
                deals_evidence_ar=presentation_term_ar(
                    str(registry.loc["rental_deals", "classification"])
                ),
                growth_evidence_ar=presentation_term_ar(
                    str(registry.loc["quarterly_rent_growth", "classification"])
                ),
                score_ar=f"{float(row['score']):.1f}/100",
                evidence_ar=presentation_term_ar(str(row.get("score_classification") or "Inference")),
                cohort_ar=f"داخل مجموعة أحياء {city} لنوع {property_type} في {score_period}",
                rank_context_ar=(
                    "الأعلى ضمن المقارنة الحالية"
                    if rank == 1
                    else "ضمن أعلى النتائج في المقارنة الحالية"
                ),
            )
        )

    source_ar = str(registry.loc["rental_deals", "source_ar"])
    limitation_ar = (
        "المتوسط مرجّح بعدد العقود المنشور، ومؤشر الفرصة ترتيب نسبي داخل مجموعة المقارنة "
        "وليس تقييمًا رسميًا أو توصية شراء."
    )
    period_ar = arabic_period_label(current_period)
    return HomeViewModel(
        available=True,
        city_ar=city,
        property_type_ar=property_type,
        period_ar=period_ar,
        scope_ar=f"{city} · كل الأحياء · {property_type} · {period_ar}",
        metrics=metrics,
        opportunities=tuple(opportunities),
        source_ar=source_ar,
        limitation_ar=limitation_ar,
    )

from __future__ import annotations

from html import escape
import re
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.analytics import (
    aggregate_market,
    opportunity_scores,
    period_coverage,
    period_label,
    quarterly_trend,
    top_growth_markets,
    weighted_average,
)
from real_estate_intel.catalog import REGA_OPEN_DATA_PAGE
from real_estate_intel.data_prep import load_rental_data, location_label


st.set_page_config(page_title="Real Estate Intelligence", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --page: #f4f7f5;
        --panel: #ffffff;
        --panel-soft: #f8fbf9;
        --ink: #17211f;
        --muted: #66736e;
        --line: #dbe7e1;
        --teal: #0b6b53;
        --teal-soft: #e5f2ee;
        --amber: #b87918;
        --blue: #1c5d99;
        --rose: #a73f54;
    }
    html, body, [class*="css"] {
        direction: rtl;
        text-align: right;
        font-family: "Segoe UI", Tahoma, Arial, sans-serif;
        color: var(--ink);
    }
    .stApp { background: var(--page); }
    .block-container { padding-top: 1.1rem; max-width: 1540px; }
    div[data-testid="stMetricValue"] { direction: ltr; text-align: right; }
    div[data-testid="stMetricDelta"] { direction: ltr; text-align: right; }
    div[data-testid="stMetricLabel"] { text-align: right; }
    div[data-testid="metric-container"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem 1.05rem;
        box-shadow: 0 10px 26px rgba(23, 33, 31, 0.06);
    }
    .stPlotlyChart { direction: ltr; }
    section[data-testid="stSidebar"] {
        direction: rtl;
        background: #eef4f1;
        border-left: 1px solid var(--line);
    }
    .digital-header {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 30px rgba(23, 33, 31, 0.07);
    }
    .digital-header h1 {
        margin: 0;
        font-size: clamp(1.9rem, 3vw, 3rem);
        line-height: 1.08;
        letter-spacing: 0;
    }
    .digital-header p {
        margin: .45rem 0 0;
        color: var(--muted);
        font-size: 1rem;
    }
    .status-strip {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: .9rem;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: .35rem;
        border: 1px solid var(--line);
        background: var(--panel-soft);
        border-radius: 999px;
        padding: .35rem .7rem;
        color: var(--ink);
        font-size: .86rem;
        white-space: nowrap;
    }
    .ai-briefing {
        display: grid;
        grid-template-columns: minmax(0, 1.45fr) minmax(280px, .75fr);
        gap: 1rem;
        margin: .35rem 0 1rem;
    }
    .brief-panel,
    .signal-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 12px 28px rgba(23, 33, 31, 0.06);
    }
    .brief-panel {
        border-right: 4px solid var(--teal);
    }
    .panel-label {
        color: var(--teal);
        font-weight: 700;
        font-size: .82rem;
        margin-bottom: .35rem;
    }
    .brief-panel h2 {
        margin: 0 0 .55rem;
        font-size: clamp(1.3rem, 2.2vw, 2rem);
        letter-spacing: 0;
    }
    .brief-panel p,
    .signal-panel p {
        color: var(--muted);
        margin: .2rem 0 .65rem;
        line-height: 1.7;
    }
    .insight-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin-top: .8rem;
    }
    .insight-item {
        border-top: 1px solid var(--line);
        padding: .75rem 0 0;
        min-height: 76px;
    }
    .insight-item strong {
        display: block;
        color: var(--ink);
        margin-bottom: .25rem;
        font-size: .95rem;
    }
    .insight-item span {
        color: var(--muted);
        line-height: 1.55;
        font-size: .88rem;
    }
    .signal-value {
        direction: ltr;
        text-align: right;
        font-size: 2rem;
        font-weight: 800;
        color: var(--teal);
        line-height: 1.1;
    }
    .signal-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: .6rem;
        margin-top: .85rem;
    }
    .signal-mini {
        border-top: 1px solid var(--line);
        padding-top: .65rem;
    }
    .signal-mini b {
        display: block;
        font-size: .82rem;
        color: var(--muted);
        font-weight: 600;
    }
    .signal-mini span {
        display: block;
        direction: ltr;
        text-align: right;
        font-size: 1.05rem;
        font-weight: 750;
        color: var(--ink);
        margin-top: .15rem;
    }
    .confidence-high { color: var(--teal); }
    .confidence-medium { color: var(--amber); }
    .confidence-low { color: var(--rose); }
    .assistant-shell {
        background: #101917;
        color: #f5fbf8;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin: .35rem 0 1rem;
        box-shadow: 0 16px 34px rgba(16, 25, 23, 0.16);
    }
    .assistant-shell h2 {
        margin: 0;
        font-size: 1.35rem;
        letter-spacing: 0;
    }
    .assistant-shell p {
        margin: .35rem 0 0;
        color: #c7d9d2;
        line-height: 1.7;
    }
    .assistant-answer {
        background: var(--panel);
        border: 1px solid var(--line);
        border-right: 4px solid var(--blue);
        border-radius: 8px;
        padding: 1rem;
        margin: .35rem 0 1rem;
        box-shadow: 0 12px 28px rgba(23, 33, 31, 0.06);
    }
    .assistant-answer h3 {
        margin: 0 0 .45rem;
        font-size: 1.2rem;
        letter-spacing: 0;
    }
    .assistant-answer p {
        color: var(--muted);
        line-height: 1.7;
        margin: .25rem 0;
    }
    .assistant-facts {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: .6rem;
        margin-top: .8rem;
    }
    .assistant-fact {
        border-top: 1px solid var(--line);
        padding-top: .65rem;
    }
    .assistant-fact b {
        display: block;
        color: var(--muted);
        font-size: .82rem;
        font-weight: 600;
    }
    .assistant-fact span {
        display: block;
        direction: ltr;
        text-align: right;
        color: var(--ink);
        font-weight: 800;
        margin-top: .16rem;
    }
    .coverage-panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1rem;
        margin: .35rem 0 1rem;
        box-shadow: 0 12px 28px rgba(23, 33, 31, 0.06);
    }
    .coverage-panel h2 {
        margin: 0 0 .45rem;
        font-size: 1.25rem;
        letter-spacing: 0;
    }
    .coverage-panel p {
        color: var(--muted);
        line-height: 1.7;
        margin: .25rem 0 .7rem;
    }
    .coverage-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: .6rem;
    }
    .coverage-item {
        border-top: 1px solid var(--line);
        padding-top: .65rem;
    }
    .coverage-item b {
        display: block;
        color: var(--muted);
        font-size: .82rem;
        font-weight: 600;
    }
    .coverage-item span {
        display: block;
        color: var(--ink);
        font-weight: 800;
        margin-top: .18rem;
    }
    @media (max-width: 900px) {
        .ai-briefing,
        .insight-row,
        .assistant-facts,
        .coverage-grid {
            grid-template-columns: 1fr;
        }
        .status-chip { white-space: normal; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_data(data_version: tuple[tuple[str, int, int], ...]) -> pd.DataFrame:
    return ensure_app_columns(load_rental_data())


def raw_data_version() -> tuple[tuple[str, int, int], ...]:
    raw_dir = ROOT / "data" / "raw"
    if not raw_dir.exists():
        return ()
    return tuple(
        (path.name, path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(raw_dir.glob("*.csv"))
    )


def ensure_app_columns(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if "district_ar" not in data.columns:
        data["district_ar"] = ""
    if "property_class" not in data.columns:
        data["property_class"] = ""
    if "location_ar" not in data.columns:
        data["location_ar"] = data.apply(location_label, axis=1)
    if "period_index" not in data.columns and {"year", "quarter"}.issubset(data.columns):
        data["period_index"] = data["year"].astype("int64") * 4 + data["quarter"].astype("int64")
    if "period" not in data.columns and {"year", "quarter"}.issubset(data.columns):
        data["period"] = data["year"].astype(str) + " Q" + data["quarter"].astype(str)
    return data


def render_digital_header(data: pd.DataFrame) -> None:
    latest_text = period_label(data) if not data.empty else "-"
    records = f"{len(data):,.0f}"
    deals = f"{data['total_deals'].sum():,.0f}" if "total_deals" in data else "0"
    cities = f"{data['city_ar'].nunique():,.0f}" if "city_ar" in data else "0"
    sources = f"{data['dataset_id'].nunique():,.0f}" if "dataset_id" in data else "0"

    st.markdown(
        f"""
        <section class="digital-header">
            <h1>Real Estate Intelligence</h1>
            <p>رؤية السوق العقاري السعودي حسب الفلتر الحالي، مع قراءة قرار مبنية على البيانات المفتوحة.</p>
            <div class="status-strip">
                <span class="status-chip">آخر فترة: {escape(latest_text)}</span>
                <span class="status-chip">السجلات: {records}</span>
                <span class="status-chip">العقود: {deals}</span>
                <span class="status-chip">المدن: {cities}</span>
                <span class="status-chip">مصادر البيانات: {sources}</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def build_market_snapshot(data: pd.DataFrame, settings: dict[str, object]) -> dict[str, object]:
    min_deals = int(settings["min_deals"])
    trend = quarterly_trend(data, comparable=bool(settings["trend_comparable"]))
    scores = opportunity_scores(data, min_deals=min_deals)
    growth = top_growth_markets(data, min_deals=min_deals)

    latest = trend.tail(1)
    previous = trend.tail(2).head(1) if len(trend) >= 2 else pd.DataFrame()
    avg_rent = weighted_average(data, "average_rent", "total_deals")
    latest_avg = float(latest["average_rent"].iloc[0]) if not latest.empty else float("nan")
    latest_deals = float(latest["total_deals"].iloc[0]) if not latest.empty else 0
    prev_avg = float(previous["average_rent"].iloc[0]) if not previous.empty else float("nan")
    prev_deals = float(previous["total_deals"].iloc[0]) if not previous.empty else 0

    latest_period = data["period_index"].max()
    latest_data = data[data["period_index"] == latest_period].copy()
    confidence_label, confidence_class, confidence_note = confidence_status(latest_data, min_deals)

    return {
        "trend": trend,
        "scores": scores,
        "growth": growth,
        "avg_rent": avg_rent,
        "latest_avg": latest_avg,
        "latest_deals": latest_deals,
        "avg_delta": pct_delta(latest_avg, prev_avg),
        "deals_delta": pct_delta(latest_deals, prev_deals),
        "confidence_label": confidence_label,
        "confidence_class": confidence_class,
        "confidence_note": confidence_note,
    }


def confidence_status(latest_data: pd.DataFrame, min_deals: int) -> tuple[str, str, str]:
    if latest_data.empty:
        return "منخفضة", "confidence-low", "لا توجد بيانات في آخر فترة ضمن الفلتر."

    locations = latest_data["location_ar"].nunique()
    deals = latest_data["total_deals"].sum()
    property_types = latest_data["property_type"].nunique()
    if deals >= min_deals * 80 and locations >= 30 and property_types >= 5:
        return "عالية", "confidence-high", "تغطية واسعة ومؤشرات كافية للمقارنة."
    if deals >= min_deals * 25 and locations >= 10:
        return "متوسطة", "confidence-medium", "التغطية جيدة، لكن بعض الشرائح تحتاج عقودا أكثر."
    return "تحتاج تدعيم", "confidence-low", "الفلتر ضيق أو عدد العقود محدود في آخر فترة."


def render_ai_briefing(
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object],
) -> None:
    scores = snapshot["scores"]
    growth = snapshot["growth"]
    avg_delta = snapshot["avg_delta"]
    deals_delta = snapshot["deals_delta"]
    confidence_label = str(snapshot["confidence_label"])
    confidence_class = str(snapshot["confidence_class"])
    confidence_note = str(snapshot["confidence_note"])

    trend_title, trend_text = trend_narrative(avg_delta, deals_delta)
    best_title, best_text, best_score = opportunity_narrative(scores)
    growth_title, growth_text = growth_narrative(growth)
    filter_scope = scope_narrative(data)

    st.markdown(
        f"""
        <section class="ai-briefing">
            <div class="brief-panel">
                <div class="panel-label">موجز الذكاء التحليلي</div>
                <h2>{escape(trend_title)}</h2>
                <p>{escape(trend_text)}</p>
                <div class="insight-row">
                    <div class="insight-item">
                        <strong>{escape(best_title)}</strong>
                        <span>{escape(best_text)}</span>
                    </div>
                    <div class="insight-item">
                        <strong>{escape(growth_title)}</strong>
                        <span>{escape(growth_text)}</span>
                    </div>
                    <div class="insight-item">
                        <strong>نطاق القراءة</strong>
                        <span>{escape(filter_scope)}</span>
                    </div>
                </div>
            </div>
            <aside class="signal-panel">
                <div class="panel-label">درجة الفرصة</div>
                <div class="signal-value">{escape(best_score)}</div>
                <p>الدرجة تجمع الطلب، النمو، وجاذبية السعر داخل الفلتر الحالي.</p>
                <div class="signal-grid">
                    <div class="signal-mini">
                        <b>ثقة القراءة</b>
                        <span class="{escape(confidence_class)}">{escape(confidence_label)}</span>
                    </div>
                    <div class="signal-mini">
                        <b>حد العقود</b>
                        <span>{int(settings["min_deals"]):,.0f}</span>
                    </div>
                </div>
                <p>{escape(confidence_note)}</p>
            </aside>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_decision_assistant(
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object],
) -> None:
    st.subheader("مساعد القرار العقاري")
    st.caption("اسأل عن أفضل الفرص، أعلى نمو، قوة الطلب، أو المدن والأحياء المناسبة لنوع عقار محدد.")

    examples = [
        "ما أفضل الفرص العقارية الآن؟",
        "أفضل أحياء الرياض للشقق السكنية",
        "قارن الرياض وجدة للشقق السكنية",
        "أين الطلب قوي والسعر أقل؟",
        "ما مخاطر أفضل فرصة؟",
        "ما أعلى المواقع نموا؟",
    ]
    left, right = st.columns([1, 2.3])
    with left:
        selected_question = st.selectbox("سؤال سريع", examples)
    with right:
        question = st.text_input(
            "اكتب سؤالك",
            value=selected_question,
            placeholder="مثال: أفضل فرص جدة للفلل السكنية",
        )

    answer = answer_decision_question(question, data, settings, snapshot)
    render_assistant_answer(answer)


def answer_decision_question(
    question: str,
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object],
) -> dict[str, object]:
    scoped, filters = apply_question_scope(data, question)
    min_deals = int(settings["min_deals"])
    mode = detect_question_mode(question)
    limit = requested_result_limit(question)

    if mode == "compare":
        return answer_comparison_question(question, data, scoped, filters, min_deals, limit)

    if mode == "growth":
        ranking = top_growth_markets(scoped, min_deals=min_deals).copy()
        if not ranking.empty and "growth_pct" in ranking:
            ranking["score"] = ranking["growth_pct"].clip(lower=-50, upper=50).rank(pct=True) * 100
        answer_title = "أعلى نمو داخل نطاق السؤال"
        method = "تم ترتيب النتائج حسب نمو متوسط الإيجار مع اشتراط حد أدنى للعقود في فترتين."
    elif mode == "risk":
        ranking = opportunity_scores(scoped, min_deals=min_deals).copy()
        answer_title = "قراءة المخاطر للفرص الأعلى"
        method = "تم اختيار أعلى الفرص ثم فحص حجم العقود، النمو، وثقة المقارنة قبل صياغة التنبيهات."
    elif mode == "demand":
        latest = scoped[scoped["period_index"] == scoped["period_index"].max()].copy()
        ranking = aggregate_market(latest, ["region_ar", "city_ar", "location_ar", "property_type"])
        ranking = ranking[ranking["total_deals"] >= min_deals].copy()
        ranking["growth_pct"] = pd.NA
        ranking["previous_period"] = ""
        ranking["score"] = ranking["total_deals"].rank(pct=True) * 100
        ranking = ranking.sort_values(["total_deals", "average_rent"], ascending=[False, True])
        answer_title = "أقوى طلب داخل نطاق السؤال"
        method = "تم ترتيب النتائج حسب عدد العقود في آخر فترة، مع تفضيل السعر الأقل عند تقارب الطلب."
    elif mode == "affordable":
        ranking = opportunity_scores(scoped, min_deals=min_deals).copy()
        if not ranking.empty and "affordability_rank" in ranking:
            ranking = ranking.sort_values(["affordability_rank", "demand_rank", "growth_rank"], ascending=False)
        answer_title = "طلب جيد مع سعر أكثر جاذبية"
        method = "تم تفضيل الشرائح الأقل سعرا نسبيا مع الحفاظ على الطلب والنمو داخل الفلتر."
    else:
        ranking = (
            opportunity_scores(scoped, min_deals=min_deals).copy()
            if scoped is not data
            else snapshot["scores"].copy()
        )
        answer_title = "أفضل الفرص العقارية المحسوبة"
        method = "درجة الفرصة تجمع الطلب، النمو، وجاذبية السعر مقارنة ببقية النتائج داخل النطاق."

    if ranking.empty:
        filter_text = "، ".join(filters) if filters else "حسب الفلاتر الحالية"
        return {
            "title": "لا توجد نتيجة كافية الثقة",
            "summary": f"لم أجد نتائج كافية ضمن: {filter_text}. جرّب مدينة أوسع أو خفف حد العقود من الفلاتر.",
            "method": "لم تظهر نتائج تتجاوز حد العقود الحالي.",
            "filters": filters,
            "table": ranking,
            "facts": {},
            "reasons": [],
            "warnings": ["وسّع نطاق السؤال أو خفّض حد العقود للحصول على قراءة أوضح."],
            "followups": default_followups(),
            "limit": limit,
        }

    ranking = ranking.dropna(subset=["average_rent", "total_deals"]).head(limit).copy()
    if ranking.empty:
        filter_text = "، ".join(filters) if filters else "حسب الفلاتر الحالية"
        return {
            "title": "لا توجد نتيجة كافية الثقة",
            "summary": f"ظهرت نتائج أولية ضمن: {filter_text}، لكنها لا تحتوي متوسط إيجار وحجم عقود كافيين للعرض.",
            "method": method,
            "filters": filters,
            "table": ranking,
            "facts": {},
            "reasons": [],
            "warnings": ["البيانات المتاحة لا تكفي لإصدار توصية عملية داخل هذا النطاق."],
            "followups": default_followups(),
            "limit": limit,
        }
    best = ranking.iloc[0]
    location = str(best.get("location_ar", "-"))
    property_type = str(best.get("property_type", "-"))
    score = float(best.get("score", 0))
    rent = float(best.get("average_rent", 0))
    deals = float(best.get("total_deals", 0))
    growth = best.get("growth_pct", pd.NA)
    growth_text = "-" if pd.isna(growth) else format_pct_text(float(growth))
    filter_text = "، ".join(filters) if filters else "حسب الفلاتر الحالية"

    return {
        "title": answer_title,
        "decision": assistant_decision(best, ranking, mode, min_deals),
        "summary": (
            f"أفضل نتيجة هي {location} لنوع {property_type}. "
            f"متوسط الإيجار {format_sar(rent)}، وحجم العقود {deals:,.0f}، والنمو {growth_text}. "
            f"نطاق الإجابة: {filter_text}."
        ),
        "method": method,
        "filters": filters,
        "table": ranking,
        "reasons": assistant_reasons(best, ranking, mode),
        "warnings": assistant_warnings(best, ranking, min_deals),
        "followups": suggested_followups(location, property_type, mode),
        "limit": limit,
        "facts": {
            "درجة": f"{score:,.1f}",
            "الإيجار": format_sar(rent),
            "العقود": f"{deals:,.0f}",
            "النمو": growth_text,
        },
    }


def answer_comparison_question(
    question: str,
    data: pd.DataFrame,
    scoped: pd.DataFrame,
    filters: list[str],
    min_deals: int,
    limit: int,
) -> dict[str, object]:
    group_col, group_label, requested_values = comparison_group(data, question)
    source = scoped.copy()
    if requested_values:
        source = source[source[group_col].isin(requested_values)].copy()

    comparison = comparison_ranking(source, group_col, min_deals).head(limit)
    filter_text = "، ".join(filters) if filters else "حسب الفلاتر الحالية"

    if comparison.empty:
        return {
            "title": "المقارنة غير كافية البيانات",
            "summary": f"لم أجد بيانات كافية للمقارنة ضمن: {filter_text}. جرّب مقارنة مدن أوسع أو خفف حد العقود.",
            "method": "المقارنة تحتاج نتائج تتجاوز حد العقود في آخر فترة متاحة.",
            "filters": filters,
            "table": comparison,
            "facts": {},
            "reasons": [],
            "warnings": ["لا توجد عينة كافية لإظهار خيار متفوق بثقة."],
            "followups": default_followups(),
            "limit": limit,
        }

    best = comparison.iloc[0]
    second = comparison.iloc[1] if len(comparison) > 1 else None
    best_name = str(best.get(group_col, "-"))
    score = float(best.get("score", 0))
    rent = float(best.get("average_rent", 0))
    deals = float(best.get("total_deals", 0))
    growth = best.get("growth_pct", pd.NA)
    growth_text = "-" if pd.isna(growth) else format_pct_text(float(growth))
    second_text = ""
    if second is not None:
        second_name = str(second.get(group_col, "-"))
        second_score = float(second.get("score", 0))
        second_text = f" أقرب بديل في المقارنة هو {second_name} بدرجة {second_score:,.1f}."

    return {
        "title": f"مقارنة حسب {group_label}",
        "decision": f"الخيار الأقوى في هذه المقارنة: {best_name}.",
        "summary": (
            f"{best_name} يتصدر المقارنة بدرجة {score:,.1f}. "
            f"متوسط الإيجار {format_sar(rent)}، العقود {deals:,.0f}، والنمو {growth_text}."
            f"{second_text} نطاق الإجابة: {filter_text}."
        ),
        "method": "تمت المقارنة بدمج الطلب، النمو، وجاذبية السعر في آخر فترة قابلة للمقارنة.",
        "filters": filters,
        "table": comparison,
        "reasons": assistant_reasons(best, comparison, "compare"),
        "warnings": assistant_warnings(best, comparison, min_deals),
        "followups": suggested_followups(best_name, "العقار المطلوب", "compare"),
        "limit": limit,
        "facts": {
            "الأقوى": best_name,
            "درجة": f"{score:,.1f}",
            "الإيجار": format_sar(rent),
            "العقود": f"{deals:,.0f}",
        },
    }


def comparison_group(data: pd.DataFrame, question: str) -> tuple[str, str, list[str]]:
    normalized = normalize_search_text(question)
    city_matches = matching_values(data["city_ar"].dropna().unique(), normalized)
    region_matches = matching_values(
        data["region_ar"].dropna().unique(),
        normalized,
        allow_token_match=True,
    )
    location_matches = matching_values(data["location_ar"].dropna().unique(), normalized)
    property_matches = matching_property_types(data["property_type"].dropna().unique(), normalized)

    if len(city_matches) >= 2:
        return "city_ar", "المدينة", city_matches
    if len(region_matches) >= 2:
        return "region_ar", "المنطقة", region_matches
    if len(location_matches) >= 2:
        return "location_ar", "الموقع", location_matches
    if len(property_matches) >= 2:
        return "property_type", "نوع العقار", property_matches
    if city_matches:
        return "location_ar", "الموقع", []
    return "city_ar", "المدينة", []


def comparison_ranking(frame: pd.DataFrame, group_col: str, min_deals: int) -> pd.DataFrame:
    if frame.empty or group_col not in frame.columns:
        return pd.DataFrame()

    trend = aggregate_market(frame, ["period_index", "period", group_col]).sort_values(
        [group_col, "period_index"]
    )
    if trend.empty:
        return trend

    grouped = trend.groupby(group_col, dropna=False)
    trend["previous_period"] = grouped["period"].shift(1)
    trend["previous_average_rent"] = grouped["average_rent"].shift(1)
    trend["previous_total_deals"] = grouped["total_deals"].shift(1)
    trend["growth_pct"] = (
        (trend["average_rent"] - trend["previous_average_rent"])
        / trend["previous_average_rent"]
        * 100
    )
    trend.loc[trend["previous_average_rent"].le(0), "growth_pct"] = pd.NA

    latest_period = int(trend["period_index"].max())
    latest = trend[trend["period_index"] == latest_period].dropna(subset=["average_rent", "total_deals"]).copy()
    latest = latest[latest["total_deals"] >= min_deals].copy()
    if latest.empty:
        return latest

    if len(latest) == 1:
        latest["demand_rank"] = 1.0
        latest["growth_rank"] = 0.5
        latest["affordability_rank"] = 0.5
    else:
        latest["demand_rank"] = latest["total_deals"].rank(pct=True)
        latest["growth_rank"] = latest["growth_pct"].fillna(0).clip(lower=-50, upper=50).rank(pct=True)
        latest["affordability_rank"] = 1 - latest["average_rent"].rank(pct=True)

    latest["score"] = (
        latest["demand_rank"] * 40
        + latest["growth_rank"] * 35
        + latest["affordability_rank"] * 25
    )
    return latest.sort_values("score", ascending=False)


def requested_result_limit(question: str) -> int:
    normalized = normalize_search_text(question)
    match = re.search(r"\b(\d{1,2})\b", normalized)
    if not match:
        return 8
    value = int(match.group(1))
    return max(3, min(value, 15))


def safe_float(value: object, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def assistant_decision(row: pd.Series, ranking: pd.DataFrame, mode: str, min_deals: int) -> str:
    score = safe_float(row.get("score", 0))
    deals = safe_float(row.get("total_deals", 0))
    growth = row.get("growth_pct", pd.NA)

    if mode == "risk":
        if deals < min_deals * 2:
            return "القرار: لا تعتمد عليها وحدها؛ حجم العقود قريب من الحد الأدنى."
        if not pd.isna(growth) and abs(float(growth)) >= 35:
            return "القرار: فرصة تحتاج تحقق ميداني؛ النمو حاد وقد يكون استثنائيا."
        return "القرار: المخاطر مقبولة مبدئيا مع ضرورة التحقق من تفاصيل الحي والعقار."

    if score >= 75 and deals >= min_deals * 3:
        return "القرار: فرصة قابلة للدراسة الآن ضمن البيانات المتاحة."
    if score >= 55:
        return "القرار: فرصة واعدة، لكن تحتاج مقارنة بديلين قبل التحرك."
    return "القرار: راقبها ولا تعتبرها أولوية إلا إذا كان لديك سبب محلي إضافي."


def assistant_reasons(row: pd.Series, ranking: pd.DataFrame, mode: str) -> list[str]:
    reasons: list[str] = []
    rent = safe_float(row.get("average_rent", 0))
    deals = safe_float(row.get("total_deals", 0))
    score = safe_float(row.get("score", 0))
    growth = row.get("growth_pct", pd.NA)

    median_deals = float(ranking["total_deals"].median()) if "total_deals" in ranking and not ranking.empty else 0
    median_rent = float(ranking["average_rent"].median()) if "average_rent" in ranking and not ranking.empty else 0

    if score:
        reasons.append(f"درجة الفرصة {score:,.1f} لأنها تجمع الطلب والنمو وجاذبية السعر.")
    if median_deals and deals >= median_deals:
        reasons.append(f"الطلب أعلى من وسيط النتائج المعروضة: {deals:,.0f} عقد.")
    elif deals:
        reasons.append(f"الطلب متاح لكنه ليس الأعلى بين البدائل: {deals:,.0f} عقد.")
    if median_rent and rent <= median_rent:
        reasons.append(f"متوسط الإيجار أقل من وسيط النتائج، ما يعزز جاذبية الدخول: {format_sar(rent)}.")
    elif rent:
        reasons.append(f"متوسط الإيجار أعلى نسبيا، لذلك يحتاج تبريرا من الموقع أو جودة الأصل: {format_sar(rent)}.")
    if not pd.isna(growth):
        growth_text = format_pct_text(float(growth))
        if mode == "growth" or float(growth) > 0:
            reasons.append(f"النمو المسجل {growth_text} مقارنة بالفترة السابقة المتاحة.")
        else:
            reasons.append(f"النمو الحالي {growth_text}، لذلك القرار يعتمد أكثر على الطلب والسعر.")
    return reasons[:4]


def assistant_warnings(row: pd.Series, ranking: pd.DataFrame, min_deals: int) -> list[str]:
    warnings: list[str] = []
    deals = safe_float(row.get("total_deals", 0))
    growth = row.get("growth_pct", pd.NA)

    if deals < min_deals * 2:
        warnings.append("حجم العقود قريب من الحد الأدنى؛ ارفع الثقة بتوسيع الفترة أو خفض تفصيل الحي.")
    if pd.isna(growth):
        warnings.append("لا توجد مقارنة نمو كافية لهذا الكيان في فترتين موثوقتين.")
    elif abs(float(growth)) >= 35:
        warnings.append("النمو مرتفع أو منخفض بشكل حاد؛ قد يكون بسبب تغير عينة العقود لا تغير السوق فقط.")
    if len(ranking) < 3:
        warnings.append("عدد البدائل قليل داخل السؤال؛ المقارنة قد تكون ضيقة.")
    return warnings[:3]


def suggested_followups(location: str, property_type: str, mode: str) -> list[str]:
    if mode == "compare":
        return [
            f"ما أفضل الأحياء داخل {location}؟",
            "أين السعر أقل مع طلب قوي؟",
            "ما أعلى نمو في نفس النطاق؟",
        ]
    return [
        f"قارن {location} مع أقرب بديل",
        f"أين الطلب أقوى لنوع {property_type}؟",
        f"ما مخاطر {location}؟",
    ]


def default_followups() -> list[str]:
    return [
        "ما أفضل الفرص العقارية الآن؟",
        "قارن الرياض وجدة للشقق السكنية",
        "أين الطلب قوي والسعر أقل؟",
    ]


def render_assistant_answer(answer: dict[str, object]) -> None:
    facts = answer.get("facts", {})
    with st.container(border=True):
        st.subheader(str(answer["title"]))
        decision = answer.get("decision")
        if decision:
            st.success(str(decision))
        st.write(str(answer["summary"]))
        st.caption(str(answer["method"]))

        if isinstance(facts, dict) and facts:
            columns = st.columns(min(len(facts), 4))
            for index, (label, value) in enumerate(facts.items()):
                columns[index % len(columns)].metric(str(label), str(value))

        reasons = answer.get("reasons", [])
        if isinstance(reasons, list) and reasons:
            st.markdown("**لماذا؟**")
            for reason in reasons:
                st.write(f"- {reason}")

        warnings = answer.get("warnings", [])
        if isinstance(warnings, list) and warnings:
            st.markdown("**تنبيهات القرار**")
            for warning in warnings:
                st.warning(str(warning))

        followups = answer.get("followups", [])
        if isinstance(followups, list) and followups:
            st.markdown("**أسئلة متابعة مقترحة**")
            cols = st.columns(min(len(followups), 3))
            for index, followup in enumerate(followups[:3]):
                cols[index % len(cols)].caption(str(followup))

    table = answer.get("table")
    if isinstance(table, pd.DataFrame) and not table.empty:
        render_assistant_table(table, int(answer.get("limit", 8)))


def render_assistant_table(table: pd.DataFrame, limit: int = 8) -> None:
    columns = [
        "region_ar",
        "city_ar",
        "location_ar",
        "property_type",
        "average_rent",
        "total_deals",
        "growth_pct",
        "score",
    ]
    available = [column for column in columns if column in table.columns]
    view = table[available].head(limit).rename(
        columns={
            "region_ar": "المنطقة",
            "city_ar": "المدينة",
            "location_ar": "الموقع",
            "property_type": "نوع العقار",
            "average_rent": "متوسط الإيجار",
            "total_deals": "العقود",
            "growth_pct": "النمو %",
            "score": "الدرجة",
        }
    )
    formatters = {
        "متوسط الإيجار": "{:,.0f}",
        "العقود": "{:,.0f}",
        "النمو %": "{:,.1f}",
        "الدرجة": "{:,.1f}",
    }
    st.dataframe(
        view.style.format({key: value for key, value in formatters.items() if key in view.columns}),
        width="stretch",
        hide_index=True,
    )


def render_market_coverage(data: pd.DataFrame, filtered: pd.DataFrame) -> None:
    available, missing = major_market_coverage(data)
    latest_text = period_label(data)
    filtered_regions = filtered["region_ar"].nunique()
    filtered_locations = filtered["location_ar"].nunique()

    st.markdown(
        f"""
        <section class="coverage-panel">
            <h2>تغطية السوق والبيانات</h2>
            <p>هذه القراءة توضّح ما يغطيه مصدر البيانات الموحد الآن، حتى تكون إجابات المساعد مرتبطة بنطاق فعلي لا بانطباع عام عن السوق.</p>
            <div class="coverage-grid">
                <div class="coverage-item">
                    <b>مناطق الإيجار المتاحة</b>
                    <span>{data["region_ar"].nunique():,.0f}</span>
                </div>
                <div class="coverage-item">
                    <b>مدن ومواقع متاحة</b>
                    <span>{data["location_ar"].nunique():,.0f}</span>
                </div>
                <div class="coverage-item">
                    <b>آخر فترة</b>
                    <span>{escape(latest_text)}</span>
                </div>
                <div class="coverage-item">
                    <b>نطاق الفلتر الحالي</b>
                    <span>{filtered_regions:,.0f} مناطق / {filtered_locations:,.0f} مواقع</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if missing:
        st.warning(
            "أسواق كبرى لم تظهر بعد في بيانات الإيجار المحملة: "
            + "، ".join(missing)
            + ". سيعرض المساعد رسالة تنبيه عند السؤال عنها بدلا من خلطها بنتائج أخرى."
        )
    else:
        st.success("الأسواق الكبرى الأساسية في قائمة التحقق موجودة داخل بيانات الإيجار الحالية.")

    with st.expander("تفاصيل التغطية حسب المنطقة", expanded=False):
        region_table = region_coverage_table(data)
        st.dataframe(
            region_table.style.format({"السجلات": "{:,.0f}", "المواقع": "{:,.0f}", "العقود": "{:,.0f}"}),
            width="stretch",
            hide_index=True,
        )
        if available:
            st.caption("أسواق كبرى متاحة: " + "، ".join(available))


def region_coverage_table(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region, group in data.groupby("region_ar", dropna=False):
        rows.append(
            {
                "المنطقة": region,
                "السجلات": len(group),
                "المدن": group["city_ar"].nunique(),
                "المواقع": group["location_ar"].nunique(),
                "العقود": group["total_deals"].sum(),
                "آخر فترة": period_label(group),
            }
        )
    return pd.DataFrame(rows).sort_values("السجلات", ascending=False)


def major_market_coverage(data: pd.DataFrame) -> tuple[list[str], list[str]]:
    markets = {
        "الرياض": ["الرياض"],
        "جدة": ["جدة", "جده"],
        "مكة المكرمة": ["مكة المكرمة", "مكه المكرمه"],
        "المدينة المنورة": ["المدينة المنورة", "المدينه المنوره"],
        "الدمام": ["الدمام"],
        "الخبر": ["الخبر"],
        "المنطقة الشرقية": ["المنطقة الشرقية", "الشرقية", "الشرقيه"],
        "عسير": ["عسير"],
        "القصيم": ["القصيم"],
    }
    values = set()
    for column in ["region_ar", "city_ar", "location_ar"]:
        values.update(normalize_search_text(value) for value in data[column].dropna().unique())

    available: list[str] = []
    missing: list[str] = []
    for market, aliases in markets.items():
        if any(market_alias_available(alias, values) for alias in aliases):
            available.append(market)
        else:
            missing.append(market)
    return available, missing


def market_alias_available(alias: str, values: set[str]) -> bool:
    normalized_alias = normalize_search_text(alias)
    return any(
        normalized_alias == value
        or (normalized_alias in value and normalized_alias in {"الشرقيه", "مكه المكرمه", "المدينه المنوره"})
        for value in values
    )


def apply_question_scope(data: pd.DataFrame, question: str) -> tuple[pd.DataFrame, list[str]]:
    normalized = normalize_search_text(question)
    scoped = data
    filters: list[str] = []
    matched_primary_place = False
    primary_norms: set[str] = set()

    region_matches = matching_values(
        data["region_ar"].dropna().unique(),
        normalized,
        allow_token_match=True,
    )
    city_matches = matching_values(data["city_ar"].dropna().unique(), normalized)
    if region_matches or city_matches:
        primary_mask = pd.Series(False, index=data.index)
        if region_matches:
            primary_mask = primary_mask | data["region_ar"].isin(region_matches)
            filters.append(f"المنطقة: {', '.join(region_matches[:3])}")
            primary_norms.update(normalize_search_text(match) for match in region_matches)
        if city_matches:
            primary_mask = primary_mask | data["city_ar"].isin(city_matches)
            filters.append(f"المدينة: {', '.join(city_matches[:3])}")
            primary_norms.update(normalize_search_text(match) for match in city_matches)
        scoped = data[primary_mask].copy()
        matched_primary_place = True

    missing_places = missing_requested_places(data, normalized)
    if missing_places and not matched_primary_place:
        return data.iloc[0:0].copy(), [f"غير متوفر في البيانات الحالية: {', '.join(missing_places[:3])}"]

    district_matches = matching_values(data["district_ar"].dropna().unique(), normalized)
    district_matches = [
        match for match in district_matches if normalize_search_text(match) not in primary_norms
    ]
    if district_matches:
        scoped = scoped[scoped["district_ar"].isin(district_matches)]
        filters.append(f"الحي: {', '.join(district_matches[:3])}")

    property_matches = matching_property_types(data["property_type"].dropna().unique(), normalized)
    if property_matches:
        scoped = scoped[scoped["property_type"].isin(property_matches)]
        filters.append(f"نوع العقار: {', '.join(property_matches[:3])}")

    return scoped, filters


def matching_values(
    values: object,
    normalized_question: str,
    allow_token_match: bool = False,
) -> list[str]:
    matches: list[str] = []
    question_tokens = set(normalized_question.split())
    for value in values:
        text = str(value).strip()
        normalized_value = normalize_search_text(text)
        tokens = [token for token in normalized_value.split() if len(token) >= 3 and token != "المنطقه"]
        if len(normalized_value) >= 3 and (
            normalized_value in normalized_question
            or (allow_token_match and any(token in question_tokens for token in tokens))
        ):
            matches.append(text)
    return matches[:12]


def matching_property_types(values: object, normalized_question: str) -> list[str]:
    specific_groups = [
        ["شقة", "شقق"],
        ["فيلا", "فلل"],
        ["استديو", "استوديو"],
        ["دور", "ادوار"],
        ["محل", "محلات"],
        ["مكتب", "مكاتب"],
        ["معرض", "معارض"],
    ]
    broad_groups = [
        ["سكني"],
        ["تجاري"],
    ]
    requested_groups = [
        group
        for group in specific_groups
        if any(normalize_search_text(keyword) in normalized_question for keyword in group)
    ]
    if not requested_groups:
        requested_groups = [
            group
            for group in broad_groups
            if any(normalize_search_text(keyword) in normalized_question for keyword in group)
        ]
    if not requested_groups:
        return []

    matches: list[str] = []
    for value in values:
        text = str(value).strip()
        normalized_value = normalize_search_text(text)
        if any(
            normalize_search_text(keyword) in normalized_value
            for group in requested_groups
            for keyword in group
        ):
            matches.append(text)
    return matches[:20]


def missing_requested_places(data: pd.DataFrame, normalized_question: str) -> list[str]:
    common_places = [
        "الرياض",
        "جدة",
        "جده",
        "مكة",
        "مكه",
        "المدينة",
        "المدينه",
        "الدمام",
        "الخبر",
        "الظهران",
        "الطائف",
        "أبها",
        "ابها",
        "حائل",
        "بريدة",
        "بريده",
        "عنيزة",
        "عنيزه",
        "القصيم",
        "عسير",
        "الشرقية",
        "الشرقيه",
    ]
    available = set()
    for column in ["region_ar", "city_ar"]:
        available.update(normalize_search_text(value) for value in data[column].dropna().unique())

    missing: list[str] = []
    for place in common_places:
        normalized_place = normalize_search_text(place)
        place_available = any(
            normalized_place in value or value in normalized_place
            for value in available
            if len(value) >= 3
        )
        if normalized_place in normalized_question and not place_available:
            missing.append(place)
    return missing


def detect_question_mode(question: str) -> str:
    normalized = normalize_search_text(question)
    if any(word in normalized for word in ["قارن", "مقارنه", "مقارنة", "ايهما", "افضل بين", "الفرق بين", "بين"]):
        return "compare"
    if any(word in normalized for word in ["مخاطر", "خطر", "ثقه", "ثقة", "امن", "آمن", "مضمون"]):
        return "risk"
    if any(word in normalized for word in ["نمو", "صعود", "ارتفاع", "زخم"]):
        return "growth"
    if any(word in normalized for word in ["رخيص", "اقل", "أقل", "منخفض", "سعر مناسب", "جذاب"]):
        return "affordable"
    if any(word in normalized for word in ["طلب", "عقود", "نشاط", "حركة"]):
        return "demand"
    return "opportunity"


def normalize_search_text(value: object) -> str:
    text = str(value).strip().lower()
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه").replace("ـ", "")
    text = re.sub(r"[\u064b-\u065f]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06ff]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def trend_narrative(avg_delta: float | None, deals_delta: float | None) -> tuple[str, str]:
    avg_text = format_pct_text(avg_delta)
    deals_text = format_pct_text(deals_delta)
    if avg_delta is None:
        return (
            "السوق يحتاج فترة مقارنة إضافية",
            "لا توجد فترة سابقة كافية داخل الفلتر الحالي، لذلك القراءة تركز على آخر مستوى متاح وحجم العقود.",
        )
    if avg_delta >= 3:
        title = "إشارة صعود في متوسط الإيجار"
    elif avg_delta <= -3:
        title = "إشارة هدوء في متوسط الإيجار"
    else:
        title = "استقرار نسبي في متوسط الإيجار"
    return (
        title,
        f"متوسط آخر فترة تغير {avg_text} مقارنة بالفترة السابقة، وحجم العقود تغير {deals_text}.",
    )


def opportunity_narrative(scores: pd.DataFrame) -> tuple[str, str, str]:
    if scores.empty:
        return (
            "لا توجد فرصة كافية الثقة",
            "ارفع نطاق الفلتر أو خفف حد العقود للحصول على ترتيب أوضح للفرص.",
            "-",
        )
    row = scores.iloc[0]
    location = str(row.get("location_ar", "-"))
    property_type = str(row.get("property_type", "-"))
    score = float(row.get("score", 0))
    deals = float(row.get("total_deals", 0))
    growth = format_pct_text(float(row.get("growth_pct", 0)))
    return (
        f"{location} | {property_type}",
        f"أعلى فرصة محسوبة بدرجة {score:,.1f}، مع {deals:,.0f} عقد ونمو {growth}.",
        f"{score:,.1f}",
    )


def growth_narrative(growth: pd.DataFrame) -> tuple[str, str]:
    if growth.empty:
        return (
            "النمو غير كاف للمقارنة",
            "لا توجد كيانات لديها عقود كافية في فترتين متتاليتين ضمن الفلتر الحالي.",
        )
    row = growth.iloc[0]
    location = str(row.get("location_ar", "-"))
    property_type = str(row.get("property_type", "-"))
    growth_pct = format_pct_text(float(row.get("growth_pct", 0)))
    return (
        "أقوى زخم",
        f"{location} | {property_type} سجل {growth_pct} مقابل آخر فترة متاحة لنفس الكيان.",
    )


def scope_narrative(data: pd.DataFrame) -> str:
    latest_text = period_label(data)
    locations = data["location_ar"].nunique()
    property_types = data["property_type"].nunique()
    return f"آخر فترة {latest_text}، مع {locations:,.0f} موقع و{property_types:,.0f} نوع عقار داخل الفلتر."


def main() -> None:
    data = ensure_app_columns(get_data(raw_data_version()))
    render_digital_header(data)

    if data.empty:
        render_empty_state()
        return

    filtered, settings = render_filters(data)
    if filtered.empty:
        st.warning("لا توجد بيانات مطابقة للفلاتر الحالية.")
        return

    snapshot = build_market_snapshot(filtered, settings)
    render_riyadh_first_page(data, settings)
    render_ai_briefing(filtered, settings, snapshot)
    render_decision_assistant(filtered, settings, snapshot)
    render_market_coverage(data, filtered)
    render_data_quality(filtered)
    render_kpis(filtered, settings, snapshot)
    render_charts(filtered, settings, snapshot)
    render_opportunities(filtered, settings, snapshot)
    render_data_table(filtered)


def render_empty_state() -> None:
    st.warning("لم يتم العثور على ملفات CSV قابلة للتحليل في data/raw.")
    st.code("python scripts/fetch_rega_data.py --seed-only", language="powershell")
    st.link_button("مصدر البيانات", REGA_OPEN_DATA_PAGE)


def render_filters(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    st.sidebar.header("الفلاتر")

    regions = st.sidebar.multiselect("المنطقة", sorted(data["region_ar"].dropna().unique()))
    cities_source = data[data["region_ar"].isin(regions)] if regions else data
    city_options = sorted(cities_source["city_ar"].dropna().unique())
    default_cities = ["الرياض"] if "الرياض" in city_options else []
    cities = st.sidebar.multiselect("المدينة", city_options, default=default_cities)

    locations_source = cities_source[cities_source["city_ar"].isin(cities)] if cities else cities_source
    locations: list[str] = []
    if "location_ar" in locations_source.columns and (
        locations_source["location_ar"].nunique() > locations_source["city_ar"].nunique()
    ):
        locations = st.sidebar.multiselect(
            "الحي/الموقع",
            sorted(locations_source["location_ar"].dropna().unique()),
        )

    years_all = sorted(data["year"].dropna().unique())
    quarters_all = sorted(data["quarter"].dropna().unique())
    years = st.sidebar.multiselect("السنة", years_all, default=years_all)
    quarters = st.sidebar.multiselect("الربع", quarters_all, default=quarters_all)

    property_types = st.sidebar.multiselect(
        "نوع العقار",
        sorted(data["property_type"].dropna().unique()),
    )

    min_deals = st.sidebar.slider("حد أدنى للعقود في التصنيفات", 1, 100, 10, step=1)
    trend_mode = st.sidebar.radio(
        "منهج الاتجاه",
        ["مقارنة متوازنة", "كل البيانات"],
        horizontal=False,
    )

    filtered = data.copy()
    if regions:
        filtered = filtered[filtered["region_ar"].isin(regions)]
    if cities:
        filtered = filtered[filtered["city_ar"].isin(cities)]
    if locations:
        filtered = filtered[filtered["location_ar"].isin(locations)]
    if years:
        filtered = filtered[filtered["year"].isin(years)]
    if quarters:
        filtered = filtered[filtered["quarter"].isin(quarters)]
    if property_types:
        filtered = filtered[filtered["property_type"].isin(property_types)]

    st.sidebar.divider()
    st.sidebar.link_button("البيانات المفتوحة للهيئة", REGA_OPEN_DATA_PAGE)

    settings = {
        "min_deals": min_deals,
        "trend_comparable": trend_mode == "مقارنة متوازنة",
    }
    return filtered, settings


def render_riyadh_first_page(data: pd.DataFrame, settings: dict[str, object]) -> None:
    riyadh = data[data["city_ar"].map(normalize_search_text).eq("الرياض")].copy()
    if riyadh.empty:
        return

    st.subheader("أين توجد الفرص العقارية في الرياض؟")
    st.caption("نقطة البداية الآن هي مدينة الرياض. يمكن توسيع الفلاتر لاحقًا، لكن القراءة الأولى تركّز على الأحياء والشرائح الأكثر جاذبية داخل الرياض.")

    scores = opportunity_scores(riyadh, min_deals=int(settings["min_deals"])).head(5).copy()
    if scores.empty:
        st.info("لا توجد فرص كافية الثقة داخل الرياض حسب حد العقود الحالي.")
    else:
        cols = st.columns(min(len(scores), 3))
        for index, (_, row) in enumerate(scores.head(3).iterrows()):
            location = str(row.get("location_ar", "-"))
            property_type = str(row.get("property_type", "-"))
            score = safe_float(row.get("score", 0))
            rent = safe_float(row.get("average_rent", 0))
            deals = safe_float(row.get("total_deals", 0))
            with cols[index % len(cols)]:
                st.metric(f"{location} | {property_type}", f"{score:,.1f}", f"{format_sar(rent)} / {deals:,.0f} عقد")

        top_view = scores[
            ["location_ar", "property_type", "average_rent", "total_deals", "growth_pct", "score"]
        ].rename(
            columns={
                "location_ar": "الحي/الموقع",
                "property_type": "نوع العقار",
                "average_rent": "متوسط الإيجار",
                "total_deals": "العقود",
                "growth_pct": "النمو %",
                "score": "درجة الفرصة",
            }
        )
        with st.expander("عرض أفضل فرص الرياض", expanded=False):
            st.dataframe(
                top_view.style.format(
                    {
                        "متوسط الإيجار": "{:,.0f}",
                        "العقود": "{:,.0f}",
                        "النمو %": "{:,.1f}",
                        "درجة الفرصة": "{:,.1f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    render_property_valuation_engine(riyadh)


def render_property_valuation_engine(riyadh: pd.DataFrame) -> None:
    st.subheader("محرك تقييم عقار سريع")
    st.caption("أدخل السعر والمساحة والحي، ثم قارن السعر المطلوب بمتوسط الحي التقديري. هذا تقييم أولي للمفاضلة والتفاوض وليس تقييمًا رسميًا.")

    left, right = st.columns([1.05, 1])
    with left:
        st.selectbox("المدينة", ["الرياض"], index=0, disabled=True, key="valuation_city")
        district = st.text_input("الحي", value="النرجس", key="valuation_district")
        price = st.number_input(
            "السعر المطلوب (ر.س)",
            min_value=0,
            value=1_200_000,
            step=50_000,
            key="valuation_price",
        )
        area = st.number_input(
            "المساحة (م²)",
            min_value=1,
            value=200,
            step=10,
            key="valuation_area",
        )
        market_gap_pct = st.number_input(
            "فرق السعر عن متوسط الحي (%)",
            value=8.0,
            step=0.5,
            format="%.1f",
            key="valuation_gap_pct",
        )

    result = evaluate_property_price(float(price), float(area), float(market_gap_pct))
    with right:
        st.metric("السعر لكل م²", f"{result['price_per_sqm']:,.0f} ر.س")
        st.metric("متوسط الحي التقديري", format_sar(result["estimated_market_price"]))
        st.metric("الفارق عن المتوسط", format_sar(result["premium_amount"]), f"{market_gap_pct:+.1f}%")

        status, message = valuation_message(float(market_gap_pct), result["negotiation_to_fair"])
        if status == "good":
            st.success(message)
        elif status == "watch":
            st.info(message)
        else:
            st.warning(message)

        context = district_rental_context(riyadh, district)
        if context:
            st.caption(context)


def evaluate_property_price(price: float, area: float, market_gap_pct: float) -> dict[str, float]:
    area = max(area, 1)
    market_multiplier = 1 + (market_gap_pct / 100)
    estimated_market_price = price / market_multiplier if market_multiplier > 0 else price
    premium_amount = price - estimated_market_price
    acceptable_price = estimated_market_price * 1.03
    return {
        "price_per_sqm": price / area,
        "estimated_market_price": estimated_market_price,
        "estimated_market_price_per_sqm": estimated_market_price / area,
        "premium_amount": premium_amount,
        "negotiation_to_fair": max(premium_amount, 0),
        "negotiation_to_acceptable": max(price - acceptable_price, 0),
    }


def valuation_message(market_gap_pct: float, negotiation_to_fair: float) -> tuple[str, str]:
    if market_gap_pct <= -5:
        return "good", f"السعر أقل من متوسط الحي بنحو {abs(market_gap_pct):.1f}%؛ هذه إشارة سعرية جيدة إذا كانت حالة العقار مناسبة."
    if market_gap_pct <= 5:
        return "watch", "السعر قريب من متوسط الحي؛ القرار يعتمد على جودة العقار، الشارع، والخدمات القريبة."
    if market_gap_pct <= 12:
        return (
            "high",
            f"السعر أعلى من متوسط الحي بنحو {market_gap_pct:.1f}%. فاوض على الأقل في حدود {format_sar(negotiation_to_fair)} للوصول إلى المتوسط.",
        )
    return (
        "high",
        f"السعر مرتفع بوضوح عن متوسط الحي بنحو {market_gap_pct:.1f}%. لا تتقدم إلا إذا كانت هناك ميزة قوية، أو اطلب خفضًا يقارب {format_sar(negotiation_to_fair)}.",
    )


def district_rental_context(riyadh: pd.DataFrame, district: str) -> str:
    normalized = normalize_search_text(district)
    if not normalized:
        return ""

    latest_period = riyadh["period_index"].max()
    latest = riyadh[riyadh["period_index"] == latest_period].copy()
    district_mask = latest["location_ar"].map(normalize_search_text).str.contains(normalized, na=False, regex=False)
    if "district_ar" in latest.columns:
        district_mask = district_mask | latest["district_ar"].map(normalize_search_text).str.contains(
            normalized,
            na=False,
            regex=False,
        )
    matches = latest[district_mask]
    if matches.empty:
        return "لا توجد إشارة إيجارية كافية لهذا الحي في آخر فترة ضمن البيانات الحالية."

    avg_rent = weighted_average(matches, "average_rent", "total_deals")
    deals = matches["total_deals"].sum()
    property_types = matches["property_type"].nunique()
    return (
        f"إشارة إيجارية للحي في آخر فترة: متوسط إيجار مرجح {format_sar(avg_rent)}، "
        f"{deals:,.0f} عقد، و{property_types:,.0f} أنواع عقار."
    )


def render_data_quality(data: pd.DataFrame) -> None:
    coverage = period_coverage(data)
    latest = data[data["period_index"] == data["period_index"].max()]
    latest_text = period_label(data)
    regions_count = latest["region_ar"].nunique()
    cities_count = latest["city_ar"].nunique()
    locations_count = latest["location_ar"].nunique()
    property_count = latest["property_type"].nunique()

    st.info(
        f"آخر فترة في الفلتر: {latest_text} | "
        f"التغطية: {regions_count} مناطق، {cities_count} مدن، {locations_count} مواقع، "
        f"{property_count} أنواع عقار. "
        "الاتجاه المتوازن يقارن نفس الموقع ونوع العقار عبر الزمن عندما تكون التغطية غير متساوية."
    )

    with st.expander("تغطية البيانات حسب الفترة"):
        left, right = st.columns([1.5, 1])
        with left:
            fig = px.bar(
                coverage,
                x="period",
                y="locations",
                color="regions",
                text="locations",
                labels={"period": "الفترة", "locations": "المواقع", "regions": "المناطق"},
                title="عدد المواقع المغطاة في كل فترة",
                color_continuous_scale="Teal",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            apply_chart_spacing(
                fig,
                height=430,
                margin={"l": 112, "r": 118, "t": 96, "b": 92},
                colorbar_title="المناطق",
            )
            fig.update_xaxes(title_text="الفترة", title_standoff=34)
            fig.update_yaxes(title_text="المواقع", title_standoff=42, tickformat=",.0f")
            render_chart(fig)
        with right:
            table = coverage.rename(
                columns={
                    "period": "الفترة",
                    "regions": "المناطق",
                    "cities": "المدن",
                    "locations": "المواقع",
                    "property_types": "أنواع العقار",
                    "records": "السجلات",
                    "total_deals": "العقود",
                }
            )[["الفترة", "المناطق", "المدن", "المواقع", "أنواع العقار", "السجلات", "العقود"]]
            st.dataframe(
                table.style.format({"العقود": "{:,.0f}"}),
                width="stretch",
                hide_index=True,
            )


def render_kpis(
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object] | None = None,
) -> None:
    snapshot = snapshot or build_market_snapshot(data, settings)
    avg_rent = float(snapshot["avg_rent"])
    latest_avg = float(snapshot["latest_avg"])
    latest_deals = float(snapshot["latest_deals"])
    avg_delta = snapshot["avg_delta"]
    deals_delta = snapshot["deals_delta"]

    cols = st.columns(4)
    cols[0].metric("متوسط الإيجار المرجح", format_sar(avg_rent))
    cols[1].metric("متوسط آخر فترة", format_sar(latest_avg), format_pct(avg_delta))
    cols[2].metric("عقود آخر فترة", f"{latest_deals:,.0f}", format_pct(deals_delta))
    cols[3].metric("مدن في الفلتر", f"{data['city_ar'].nunique():,.0f}")


def render_charts(
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object] | None = None,
) -> None:
    snapshot = snapshot or build_market_snapshot(data, settings)
    min_deals = int(settings["min_deals"])
    latest_period = data["period_index"].max()
    latest = data[data["period_index"] == latest_period].copy()

    trend = snapshot["trend"]
    entity_latest = aggregate_market(latest, ["region_ar", "city_ar", "location_ar", "property_type"])
    entity_latest = entity_latest[entity_latest["total_deals"] >= min_deals]
    property_mix = aggregate_market(latest, ["property_type"]).sort_values("total_deals", ascending=False)
    growth = snapshot["growth"]
    scores = snapshot["scores"]

    left, right = st.columns([1.45, 1])
    with left:
        render_trend_chart(trend)
    with right:
        render_entity_ranking(entity_latest)

    left, right = st.columns(2)
    with left:
        render_growth_chart(growth)
    with right:
        render_price_demand_scatter(scores)

    left, right = st.columns([1.1, 1])
    with left:
        render_property_mix(property_mix)
    with right:
        render_heatmap(entity_latest)


def apply_chart_spacing(
    fig: go.Figure,
    *,
    height: int = 430,
    margin: dict[str, int] | None = None,
    colorbar_title: str | None = None,
) -> None:
    fig.update_layout(
        height=height,
        margin=margin or {"l": 104, "r": 104, "t": 86, "b": 92},
        font={"family": "Segoe UI, Tahoma, Arial, sans-serif", "size": 12},
        title={"x": 0.5, "xanchor": "center", "font": {"size": 17}},
        hoverlabel={"align": "right"},
        hovermode="closest",
        dragmode=False,
        clickmode="event",
        uirevision="real-estate-intelligence",
        legend={"itemclick": False, "itemdoubleclick": False},
        uniformtext={"minsize": 10, "mode": "hide"},
    )
    fig.update_xaxes(
        automargin=True,
        title_standoff=30,
        title_font={"size": 12},
        tickfont={"size": 10},
        separatethousands=True,
    )
    fig.update_yaxes(
        automargin=True,
        title_standoff=38,
        title_font={"size": 12},
        tickfont={"size": 10},
        separatethousands=True,
    )
    if colorbar_title:
        fig.update_layout(
            coloraxis_colorbar={
                "title": {"text": colorbar_title, "side": "top"},
                "x": 1.08,
                "xpad": 14,
                "ypad": 8,
                "len": 0.78,
                "thickness": 14,
            }
        )


CHART_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "doubleClick": "reset",
    "responsive": True,
    "scrollZoom": False,
    "showTips": False,
}


def render_chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def render_trend_chart(trend: pd.DataFrame) -> None:
    if trend.empty:
        st.warning("لا توجد بيانات كافية لرسم الاتجاه.")
        return

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=trend["period"],
            y=trend["total_deals"],
            name="العقود",
            marker_color="#D8E7E1",
            opacity=0.75,
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=trend["period"],
            y=trend["average_rent"],
            name="متوسط الإيجار المرجح",
            mode="lines+markers",
            line={"color": "#0B6B53", "width": 3},
            marker={"size": 7},
        ),
        secondary_y=False,
    )
    fig.update_layout(
        title="اتجاه الإيجار مع حجم العقود",
        hovermode="closest",
        legend={"orientation": "h", "y": 1.16, "x": 0.02},
    )
    apply_chart_spacing(fig, height=440, margin={"l": 118, "r": 118, "t": 96, "b": 86})
    fig.update_yaxes(
        title_text="الإيجار (ر.س)",
        title_standoff=44,
        tickformat=",.0f",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="العقود",
        title_standoff=44,
        tickformat=",.0f",
        secondary_y=True,
        showgrid=False,
    )
    render_chart(fig)


def render_entity_ranking(entity_latest: pd.DataFrame) -> None:
    if entity_latest.empty:
        st.warning("لا توجد كيانات تتجاوز حد العقود المحدد.")
        return

    top_entities = entity_latest.sort_values("average_rent", ascending=False).head(14).copy()
    top_entities["entity"] = top_entities["location_ar"] + " | " + top_entities["property_type"]
    fig = px.bar(
        top_entities.sort_values("average_rent"),
        x="average_rent",
        y="entity",
        orientation="h",
        color="total_deals",
        hover_data=["region_ar", "total_deals"],
        labels={
            "average_rent": "متوسط الإيجار المرجح",
            "entity": "الموقع | نوع العقار",
            "total_deals": "العقود",
            "region_ar": "المنطقة",
        },
        title="أعلى متوسطات الإيجار في آخر فترة",
        color_continuous_scale="Teal",
    )
    apply_chart_spacing(
        fig,
        height=480,
        margin={"l": 260, "r": 118, "t": 88, "b": 92},
        colorbar_title="العقود",
    )
    fig.update_xaxes(title_text="الإيجار المرجح (ر.س)", title_standoff=34, tickformat=",.0f")
    fig.update_yaxes(title_text="")
    render_chart(fig)


def render_growth_chart(growth: pd.DataFrame) -> None:
    if growth.empty:
        st.warning("لا توجد فترات سابقة كافية لحساب نمو موثوق.")
        return

    top_growth = growth.head(12).copy()
    top_growth["entity"] = top_growth["location_ar"] + " | " + top_growth["property_type"]
    fig = px.bar(
        top_growth.sort_values("growth_pct"),
        x="growth_pct",
        y="entity",
        orientation="h",
        color="total_deals",
        hover_data=["period", "previous_period", "average_rent", "previous_average_rent"],
        labels={
            "growth_pct": "النمو %",
            "entity": "الموقع | نوع العقار",
            "total_deals": "العقود",
        },
        title="أعلى نمو مقابل آخر فترة متاحة لنفس الكيان",
        color_continuous_scale="Teal",
    )
    apply_chart_spacing(
        fig,
        height=470,
        margin={"l": 260, "r": 118, "t": 88, "b": 92},
        colorbar_title="العقود",
    )
    fig.update_xaxes(title_text="النمو %", title_standoff=34)
    fig.update_yaxes(title_text="")
    render_chart(fig)


def render_price_demand_scatter(scores: pd.DataFrame) -> None:
    if scores.empty:
        st.warning("لا توجد فرص تتجاوز حد العقود المحدد.")
        return

    fig = px.scatter(
        scores,
        x="average_rent",
        y="total_deals",
        color="growth_pct",
        size="score",
        hover_data=["region_ar", "city_ar", "location_ar", "property_type", "previous_period"],
        labels={
            "average_rent": "متوسط الإيجار",
            "total_deals": "العقود",
            "growth_pct": "النمو %",
            "score": "درجة الفرصة",
        },
        title="السعر مقابل الطلب والنمو",
        color_continuous_scale="RdYlGn",
    )
    apply_chart_spacing(
        fig,
        height=430,
        margin={"l": 112, "r": 118, "t": 88, "b": 98},
        colorbar_title="النمو %",
    )
    fig.update_xaxes(title_text="متوسط الإيجار (ر.س)", title_standoff=34, tickformat=",.0f")
    fig.update_yaxes(title_text="العقود", title_standoff=42, tickformat=",.0f")
    render_chart(fig)


def render_property_mix(property_mix: pd.DataFrame) -> None:
    if property_mix.empty:
        return

    fig = px.bar(
        property_mix.head(16),
        x="property_type",
        y="total_deals",
        color="average_rent",
        labels={
            "property_type": "نوع العقار",
            "total_deals": "العقود",
            "average_rent": "متوسط الإيجار",
        },
        title="حجم العقود حسب نوع العقار في آخر فترة",
        color_continuous_scale="Teal",
    )
    apply_chart_spacing(
        fig,
        height=470,
        margin={"l": 112, "r": 118, "t": 88, "b": 166},
        colorbar_title="متوسط الإيجار",
    )
    fig.update_layout(xaxis_tickangle=-35)
    fig.update_xaxes(title_text="", tickfont={"size": 10})
    fig.update_yaxes(title_text="العقود", title_standoff=42, tickformat=",.0f")
    render_chart(fig)


def render_heatmap(entity_latest: pd.DataFrame) -> None:
    if entity_latest.empty:
        return

    top_cities = (
        entity_latest.groupby("location_ar")["total_deals"]
        .sum()
        .sort_values(ascending=False)
        .head(12)
        .index
    )
    heat = entity_latest[entity_latest["location_ar"].isin(top_cities)]
    pivot = heat.pivot_table(
        index="property_type",
        columns="location_ar",
        values="average_rent",
        aggfunc="mean",
    )
    if pivot.empty:
        return

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Teal",
        labels={"x": "الموقع", "y": "نوع العقار", "color": "متوسط الإيجار"},
        title="خريطة حرارية لمتوسط الإيجار",
    )
    apply_chart_spacing(
        fig,
        height=470,
        margin={"l": 190, "r": 118, "t": 88, "b": 166},
        colorbar_title="متوسط الإيجار",
    )
    fig.update_xaxes(title_text="", tickangle=-35, tickfont={"size": 10})
    fig.update_yaxes(title_text="", tickfont={"size": 10})
    render_chart(fig)


def render_opportunities(
    data: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object] | None = None,
) -> None:
    snapshot = snapshot or build_market_snapshot(data, settings)
    scores = snapshot["scores"]
    if scores.empty:
        return

    st.subheader("قائمة الفرص المحسوبة")
    view = scores[
        [
            "region_ar",
            "city_ar",
            "location_ar",
            "property_type",
            "period",
            "previous_period",
            "average_rent",
            "previous_average_rent",
            "total_deals",
            "growth_pct",
            "score",
        ]
    ].head(30)
    view = view.rename(
        columns={
            "region_ar": "المنطقة",
            "city_ar": "المدينة",
            "location_ar": "الموقع",
            "property_type": "نوع العقار",
            "period": "الفترة",
            "previous_period": "الفترة السابقة",
            "average_rent": "متوسط الإيجار",
            "previous_average_rent": "متوسط سابق",
            "total_deals": "العقود",
            "growth_pct": "النمو %",
            "score": "النقاط",
        }
    )
    st.dataframe(
        view.style.format(
            {
                "متوسط الإيجار": "{:,.0f}",
                "متوسط سابق": "{:,.0f}",
                "العقود": "{:,.0f}",
                "النمو %": "{:,.1f}",
                "النقاط": "{:,.1f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )


def render_data_table(data: pd.DataFrame) -> None:
    with st.expander("البيانات الموحدة"):
        columns = [
            "year",
            "quarter",
            "region_ar",
            "city_ar",
            "location_ar",
            "district_ar",
            "property_type",
            "total_deals",
            "average_rent",
            "dataset_title_ar",
        ]
        table = data[columns].sort_values(["year", "quarter", "region_ar", "city_ar"])
        table = table.rename(
            columns={
                "year": "السنة",
                "quarter": "الربع",
                "region_ar": "المنطقة",
                "city_ar": "المدينة",
                "location_ar": "الموقع",
                "district_ar": "الحي",
                "property_type": "نوع العقار",
                "total_deals": "العقود",
                "average_rent": "متوسط الإيجار",
                "dataset_title_ar": "مجموعة البيانات",
            }
        )
        st.dataframe(table, width="stretch", hide_index=True)


def format_sar(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:,.0f} ر.س"


def pct_delta(current: float, previous: float) -> float | None:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current - previous) / previous * 100


def format_pct(value: float | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return f"{value:+.1f}%"


def format_pct_text(value: float | None) -> str:
    formatted = format_pct(value)
    return formatted if formatted is not None else "-"


if __name__ == "__main__":
    main()

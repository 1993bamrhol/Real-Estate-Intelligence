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
from real_estate_intel.data_engine import load_market_data, warehouse_status
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
    .decision-grid,
    .alert-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .75rem;
        margin: .75rem 0 1rem;
    }
    .decision-card,
    .alert-card,
    .report-box {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: .95rem 1rem;
        box-shadow: 0 12px 28px rgba(23, 33, 31, 0.06);
    }
    .decision-card {
        border-right: 4px solid var(--teal);
        min-height: 188px;
    }
    .alert-card {
        border-right: 4px solid var(--amber);
        min-height: 132px;
    }
    .decision-card h3,
    .alert-card h3 {
        margin: 0 0 .45rem;
        font-size: 1.02rem;
        letter-spacing: 0;
    }
    .decision-card p,
    .alert-card p,
    .report-box p {
        color: var(--muted);
        line-height: 1.65;
        margin: .3rem 0;
        font-size: .9rem;
    }
    .score-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 72px;
        border-radius: 999px;
        background: var(--teal-soft);
        color: var(--teal);
        font-weight: 800;
        padding: .28rem .65rem;
        margin-bottom: .55rem;
        direction: ltr;
    }
    .decision-meta {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: .45rem;
        margin-top: .75rem;
        border-top: 1px solid var(--line);
        padding-top: .65rem;
    }
    .decision-meta span {
        color: var(--muted);
        font-size: .78rem;
    }
    .decision-meta b {
        display: block;
        color: var(--ink);
        font-size: .92rem;
        direction: ltr;
        text-align: right;
        margin-top: .12rem;
    }
    @media (max-width: 900px) {
        .ai-briefing,
        .insight-row,
        .assistant-facts,
        .coverage-grid,
        .decision-grid,
        .alert-grid {
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
    source = ensure_app_columns(load_rental_data())
    return ensure_app_columns(load_market_data(source))


def raw_data_version() -> tuple[tuple[str, int, int], ...]:
    raw_dir = ROOT / "data" / "raw"
    snapshot = ROOT / "data" / "processed" / "rental_market.csv.gz"
    versions = []
    if snapshot.exists():
        versions.append((str(snapshot.relative_to(ROOT)), snapshot.stat().st_mtime_ns, snapshot.stat().st_size))
    if not raw_dir.exists():
        return tuple(versions)
    versions.extend(
        (path.name, path.stat().st_mtime_ns, path.stat().st_size)
        for path in sorted(raw_dir.glob("*.csv"))
    )
    return tuple(versions)


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
    st.subheader("المحلل العقاري الذكي")
    st.caption("اسأل كمحلل استثماري: مقارنة أحياء، قوة الطلب، المخاطر، السعر المناسب، أو أين توجد فرصة قابلة للدراسة.")

    examples = [
        "اشرح لي وضع العزيزية بالتفصيل",
        "حلل حي النرجس: السعر والطلب والمخاطر",
        "هل أشتري الآن أم أنتظر؟",
        "كيف أقيم سعر عقار قبل الشراء؟",
        "ما أهم مخاطر الاستثمار العقاري؟",
        "لدي 800 ألف ر.س، ما أفضل المناطق للاستثمار؟",
        "معي مليون ر.س، أين أبحث عن شقة في الرياض؟",
        "ما أفضل الفرص العقارية الآن؟",
        "أفضل أحياء الرياض للشقق السكنية",
        "قارن الرياض وجدة للشقق السكنية",
        "أين الطلب قوي والسعر أقل؟",
        "ما مخاطر أفضل فرصة؟",
        "حلل أفضل حي في الرياض للشقق",
        "ما أعلى المواقع نموا؟",
    ]
    left, right = st.columns([1, 2.3])
    with left:
        selected_question = st.selectbox("سؤال سريع", examples)
    with right:
        question = st.text_input(
            "اكتب سؤالك",
            value=selected_question,
            placeholder="مثال: لدي 800 ألف ر.س، ما أفضل المناطق للاستثمار؟",
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
    budget = extract_investment_budget(question)
    profile_target = requested_neighborhood_profile_target(scoped, question)

    if profile_target and budget is None:
        return answer_neighborhood_profile(question, data, filters, min_deals, limit, profile_target)

    if budget is not None:
        return answer_budget_question(question, scoped, filters, min_deals, limit, budget)

    if mode == "compare":
        return answer_comparison_question(question, data, scoped, filters, min_deals, limit)

    if is_general_real_estate_question(question):
        return answer_general_real_estate_question(question, scoped, filters, settings, snapshot, limit)

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


def answer_general_real_estate_question(
    question: str,
    scoped: pd.DataFrame,
    filters: list[str],
    settings: dict[str, object],
    snapshot: dict[str, object],
    limit: int,
) -> dict[str, object]:
    min_deals = int(settings["min_deals"])
    topic = general_real_estate_topic(question)
    market = general_market_context(scoped, settings, snapshot, min_deals)
    ranking = general_topic_table(scoped, topic, min_deals, limit)
    filter_text = "، ".join(filters) if filters else "نطاق الفلاتر الحالي"

    return {
        "title": general_topic_title(topic),
        "decision": general_topic_decision(topic, market, ranking),
        "summary": general_topic_summary(topic, market, ranking, filter_text),
        "method": (
            "حللت السؤال كمستشار عقاري عام ثم ربطته بالمؤشرات المتاحة في قاعدة البيانات: "
            "متوسط الإيجار، حجم العقود، النمو، السيولة، وترتيب الفرص. عند غياب بيانات البيع أستخدم المؤشرات الإيجارية كقراءة سوقية لا كتقييم رسمي."
        ),
        "filters": filters,
        "table": ranking,
        "reasons": general_topic_reasons(topic, market, ranking),
        "warnings": general_topic_warnings(topic),
        "followups": general_topic_followups(topic),
        "limit": limit,
        "facts": {
            "آخر فترة": str(market.get("period", "-")),
            "متوسط الإيجار": format_sar(safe_float(market.get("latest_avg", 0))),
            "العقود": f"{safe_float(market.get('latest_deals', 0)):,.0f}",
            "تغير السوق": format_pct_text(market.get("avg_delta")),
        },
    }


def is_general_real_estate_question(question: str) -> bool:
    normalized = normalize_search_text(question)
    cues = [
        "هل",
        "كيف",
        "متى",
        "لماذا",
        "ماذا عن",
        "نصيحه",
        "نصيحة",
        "استراتيجيه",
        "استراتيجية",
        "اشتري",
        "شراء",
        "ابيع",
        "بيع",
        "انتظر",
        "عائد",
        "دخل",
        "تدفق",
        "تمويل",
        "قرض",
        "تفاوض",
        "مخاطر",
        "خطر",
        "تقييم",
        "قيم",
        "سعر",
        "متر",
        "ايجار",
        "إيجار",
        "محفظه",
        "محفظة",
        "استثمار",
    ]
    excluded = ["اشرح", "حلل حي", "افضل الفرص", "أفضل الفرص", "افضل احياء", "أفضل أحياء"]
    if any(item in normalized for item in [normalize_search_text(value) for value in excluded]):
        return False
    return any(cue in normalized for cue in [normalize_search_text(value) for value in cues])


def general_real_estate_topic(question: str) -> str:
    normalized = normalize_search_text(question)
    if any(word in normalized for word in ["تقييم", "قيم", "سعر", "متر", "تفاوض", "عادل"]):
        return "valuation"
    if any(word in normalized for word in ["عائد", "دخل", "تدفق", "ايجار", "إيجار", "كاش فلو"]):
        return "yield"
    if any(word in normalized for word in ["مخاطر", "خطر", "امان", "آمان", "امن", "آمن"]):
        return "risk"
    if any(word in normalized for word in ["نوع عقار", "شقه", "شقة", "فيلا", "فلل", "دور", "دوبلكس"]):
        return "property_type"
    if any(word in normalized for word in ["اشتري", "شراء", "انتظر", "الان", "الآن", "توقيت"]):
        return "buy_timing"
    return "strategy"


def general_market_context(
    scoped: pd.DataFrame,
    settings: dict[str, object],
    snapshot: dict[str, object],
    min_deals: int,
) -> dict[str, object]:
    trend = quarterly_trend(scoped, comparable=bool(settings["trend_comparable"]))
    latest = trend.tail(1)
    previous = trend.tail(2).head(1) if len(trend) >= 2 else pd.DataFrame()
    latest_avg = safe_float(latest["average_rent"].iloc[0]) if not latest.empty else safe_float(snapshot.get("latest_avg", 0))
    latest_deals = safe_float(latest["total_deals"].iloc[0]) if not latest.empty else safe_float(snapshot.get("latest_deals", 0))
    prev_avg = safe_float(previous["average_rent"].iloc[0], float("nan")) if not previous.empty else float("nan")
    prev_deals = safe_float(previous["total_deals"].iloc[0], float("nan")) if not previous.empty else float("nan")
    scores = opportunity_scores(scoped, min_deals=min_deals).head(5).copy()
    best = scores.iloc[0] if not scores.empty else None
    return {
        "period": period_label(scoped),
        "latest_avg": latest_avg,
        "latest_deals": latest_deals,
        "avg_delta": pct_delta(latest_avg, prev_avg),
        "deals_delta": pct_delta(latest_deals, prev_deals),
        "scores": scores,
        "best": best,
        "locations": scoped["location_ar"].nunique() if "location_ar" in scoped else 0,
        "property_types": scoped["property_type"].nunique() if "property_type" in scoped else 0,
    }


def general_topic_table(scoped: pd.DataFrame, topic: str, min_deals: int, limit: int) -> pd.DataFrame:
    if scoped.empty:
        return pd.DataFrame()

    if topic == "property_type":
        return general_property_type_ranking(scoped, min_deals).head(limit)
    if topic == "yield":
        ranking = opportunity_scores(scoped, min_deals=min_deals).copy()
        if ranking.empty:
            return ranking
        ranking["income_rank"] = ranking["average_rent"].rank(pct=True)
        ranking["score"] = (
            ranking["income_rank"] * 45
            + ranking.get("demand_rank", ranking["total_deals"].rank(pct=True)) * 35
            + ranking.get("growth_rank", ranking["growth_pct"].fillna(0).rank(pct=True)) * 20
        )
        return ranking.sort_values("score", ascending=False).head(limit)
    if topic == "risk":
        ranking = opportunity_scores(scoped, min_deals=min_deals).copy()
        if ranking.empty:
            return ranking
        ranking["risk_adjusted_score"] = (
            ranking.get("demand_rank", ranking["total_deals"].rank(pct=True)) * 55
            + ranking["growth_pct"].fillna(0).clip(lower=-20, upper=20).rank(pct=True) * 25
            + ranking.get("affordability_rank", 1 - ranking["average_rent"].rank(pct=True)) * 20
        )
        ranking["score"] = ranking["risk_adjusted_score"]
        return ranking.sort_values("score", ascending=False).head(limit)
    return opportunity_scores(scoped, min_deals=min_deals).head(limit)


def general_property_type_ranking(scoped: pd.DataFrame, min_deals: int) -> pd.DataFrame:
    if scoped.empty:
        return pd.DataFrame()
    trend = aggregate_market(scoped, ["period_index", "period", "property_type"]).sort_values(
        ["property_type", "period_index"]
    )
    if trend.empty:
        return trend
    grouped = trend.groupby("property_type", dropna=False)
    trend["previous_period"] = grouped["period"].shift(1)
    trend["previous_average_rent"] = grouped["average_rent"].shift(1)
    trend["growth_pct"] = pct_series(trend["average_rent"], trend["previous_average_rent"])
    latest = trend[trend["period_index"] == trend["period_index"].max()].copy()
    latest = latest[latest["total_deals"] >= min_deals].copy()
    if latest.empty:
        return latest
    latest["demand_rank"] = latest["total_deals"].rank(pct=True)
    latest["growth_rank"] = latest["growth_pct"].fillna(0).clip(lower=-50, upper=50).rank(pct=True)
    latest["score"] = latest["demand_rank"] * 55 + latest["growth_rank"] * 45
    return latest.sort_values("score", ascending=False)


def general_topic_title(topic: str) -> str:
    titles = {
        "buy_timing": "تحليل قرار الشراء أو الانتظار",
        "valuation": "منهج تقييم سعر العقار",
        "yield": "تحليل العائد والدخل الإيجاري",
        "risk": "تحليل المخاطر العقارية",
        "property_type": "تحليل نوع العقار الأنسب",
        "strategy": "استشارة عقارية مبنية على البيانات",
    }
    return titles.get(topic, titles["strategy"])


def general_topic_decision(topic: str, market: dict[str, object], ranking: pd.DataFrame) -> str:
    avg_delta = market.get("avg_delta")
    deals_delta = market.get("deals_delta")
    best_text = best_ranking_text(ranking)
    if topic == "buy_timing":
        if avg_delta is not None and deals_delta is not None and avg_delta > 3 and deals_delta > 0:
            return f"القرار: لا تنتظر السوق كله؛ ابحث عن صفقة محددة دون متوسط الحي. المؤشرات تميل للصعود مع نشاط عقود إيجابي. {best_text}"
        if avg_delta is not None and avg_delta < -3:
            return f"القرار: تفاوض بقوة ولا تستعجل؛ توجد إشارة هدوء في متوسط الإيجار. {best_text}"
        return f"القرار: الشراء مناسب فقط عند وجود خصم أو عائد واضح، وليس لمجرد دخول السوق. {best_text}"
    if topic == "valuation":
        return "القرار: لا تقبل السعر قبل مقارنته بثلاث طبقات: متوسط الحي، العائد الإيجاري المتوقع، وحجم الطلب الفعلي في نفس نوع العقار."
    if topic == "yield":
        return f"القرار: ركز على الشرائح ذات إيجار مرتفع وسيولة قوية، لا على أعلى إيجار فقط. {best_text}"
    if topic == "risk":
        return "القرار: أخفض المخاطر باختيار حي لديه عقود كافية ونمو غير حاد، وتجنب القرارات المبنية على قفزة سعرية قصيرة."
    if topic == "property_type":
        return f"القرار: النوع الأفضل هو الذي يجمع عقودًا كثيرة ونموًا مقبولًا. {best_text}"
    return f"القرار: ابدأ بالفرز الرقمي ثم تحقق ميدانيًا من العقار والشارع والخدمات. {best_text}"


def general_topic_summary(topic: str, market: dict[str, object], ranking: pd.DataFrame, filter_text: str) -> str:
    avg_delta = format_pct_text(market.get("avg_delta"))
    deals_delta = format_pct_text(market.get("deals_delta"))
    latest_avg = format_sar(safe_float(market.get("latest_avg", 0)))
    latest_deals = safe_float(market.get("latest_deals", 0))
    scope = f"{market.get('locations', 0):,.0f} موقع و{market.get('property_types', 0):,.0f} أنواع عقار"
    topic_text = {
        "buy_timing": "قراءة التوقيت تعتمد على اتجاه الإيجار وحجم العقود: صعود الإيجار مع نشاط العقود يدعم التحرك الانتقائي، أما الهبوط أو ضعف العقود فيدعم الانتظار أو التفاوض.",
        "valuation": "التقييم الدقيق يبدأ من سعر المتر أو السعر الإجمالي، ثم يُقارن بالإيجار السنوي المتوقع وبمتوسط الحي ونشاط العقود.",
        "yield": "العائد لا يعني أعلى إيجار فقط؛ المهم أن يكون الإيجار مدعومًا بسيولة عقود حتى لا يكون الرقم معزولًا.",
        "risk": "المخاطر الأعلى غالبًا تأتي من قلة الصفقات، نمو حاد غير مستقر، أو سعر أعلى من السوق دون ميزة واضحة.",
        "property_type": "اختيار نوع العقار يعتمد على توازن الطلب والنمو وسهولة التخارج، وليس على الانطباع العام.",
        "strategy": "الاستراتيجية الأفضل تبدأ بتحديد الهدف: دخل إيجاري، نمو رأسمالي، أو حفظ رأس مال؛ ثم ترتيب الأحياء والأنواع وفق البيانات.",
    }
    return (
        f"{topic_text.get(topic, topic_text['strategy'])} داخل {filter_text}، آخر فترة هي {market.get('period', '-')}. "
        f"متوسط الإيجار المرجح {latest_avg}، وإجمالي العقود {latest_deals:,.0f}. "
        f"تغير الإيجار {avg_delta} وتغير العقود {deals_delta}. نطاق القراءة يغطي {scope}."
    )


def general_topic_reasons(topic: str, market: dict[str, object], ranking: pd.DataFrame) -> list[str]:
    reasons = [
        f"اعتمدت على آخر فترة متاحة: {market.get('period', '-')}.",
        f"حجم العقود في النطاق {safe_float(market.get('latest_deals', 0)):,.0f} عقد، وهو مؤشر سيولة أهم من السعر وحده.",
    ]
    avg_delta = market.get("avg_delta")
    if avg_delta is not None:
        reasons.append(f"اتجاه متوسط الإيجار في النطاق {format_pct_text(avg_delta)} مقارنة بالفترة السابقة.")
    if not ranking.empty:
        row = ranking.iloc[0]
        label = row.get("location_ar", row.get("property_type", "-"))
        reasons.append(
            f"أعلى نتيجة في جدول التحليل: {label} بدرجة {safe_float(row.get('score', 0)):,.1f}."
        )
    if topic == "valuation":
        reasons.append("قاعدة عملية: إذا كان السعر أعلى من متوسط الحي، يجب أن يبرره عائد أعلى أو موقع أدق أو جودة أصل واضحة.")
    elif topic == "risk":
        reasons.append("المؤشر يقلل الثقة في الشرائح ذات عقود قليلة أو نمو حاد؛ لأنها قد تعكس عينة صغيرة لا تغيرًا حقيقيًا.")
    elif topic == "yield":
        reasons.append("العائد يحتاج اختبارًا بسعر شراء فعلي؛ البيانات الحالية تعطي قوة الإيجار لا سعر البيع النهائي.")
    return reasons[:5]


def general_topic_warnings(topic: str) -> list[str]:
    warnings = [
        "البيانات الحالية إيجارية؛ لا تحتوي أسعار بيع فعلية أو سعر متر شراء، لذلك لا تعتبر تقييمًا رسميًا.",
        "أي قرار شراء يحتاج فحص العقار والشارع والخدمات والتمويل ورسوم الصيانة قبل التنفيذ.",
    ]
    if topic == "buy_timing":
        warnings.append("قرار التوقيت لا يُحسم من اتجاه السوق العام فقط؛ الصفقة الجيدة قد تظهر حتى في سوق مرتفع.")
    if topic == "valuation":
        warnings.append("لا تقارن عقارًا مفروشًا أو مجددًا بعقار عادي دون تعديل السعر والجودة.")
    if topic == "risk":
        warnings.append("ارتفاع العائد قد يكون تعويضًا عن مخاطر أعلى مثل ضعف الموقع أو صعوبة التأجير.")
    return warnings[:4]


def general_topic_followups(topic: str) -> list[str]:
    followups = {
        "buy_timing": ["ما أفضل الأحياء للتحرك الآن؟", "لدي 900 ألف أين أبحث؟", "اشرح لي وضع النرجس"],
        "valuation": ["قيّم عقار في النرجس سعره 1.2 مليون", "كيف أعرف أن السعر مبالغ؟", "ما متوسط إيجار الحي؟"],
        "yield": ["ما أعلى عائد تقديري؟", "لدي 800 ألف ما أفضل المناطق؟", "قارن الشقق والفلل للعائد"],
        "risk": ["ما مخاطر حي العزيزية؟", "أين الطلب قوي والسعر أقل؟", "قارن النرجس والعارض"],
        "property_type": ["هل الشقق أفضل من الفلل؟", "أفضل نوع عقار في الرياض", "ما أكثر نوع عليه طلب؟"],
        "strategy": ["ابن لي استراتيجية استثمار", "ما أفضل الفرص الآن؟", "اشرح لي وضع العزيزية"],
    }
    return followups.get(topic, followups["strategy"])


def best_ranking_text(ranking: pd.DataFrame) -> str:
    if ranking.empty:
        return ""
    row = ranking.iloc[0]
    if "location_ar" in row:
        return f"أقوى مرشح حاليًا: {row.get('location_ar')} | {row.get('property_type', '-') }."
    if "property_type" in row:
        return f"أقوى نوع حاليًا: {row.get('property_type')}."
    return ""


def answer_neighborhood_profile(
    question: str,
    data: pd.DataFrame,
    filters: list[str],
    min_deals: int,
    limit: int,
    target: str,
) -> dict[str, object]:
    rows = neighborhood_profile_rows(data, target)
    if rows.empty:
        return {
            "title": f"لم أجد بيانات كافية عن {target}",
            "summary": f"لم أجد حيًا مطابقًا لاسم {target} داخل نطاق الفلاتر الحالي.",
            "method": "تم البحث في أسماء الأحياء والمواقع داخل قاعدة البيانات الحالية.",
            "filters": filters,
            "table": pd.DataFrame(),
            "facts": {},
            "reasons": [],
            "warnings": ["جرّب كتابة اسم الحي كما يظهر في البيانات أو وسّع نطاق المدينة من الفلاتر."],
            "followups": default_followups(),
            "limit": limit,
        }

    profile = build_neighborhood_profile(data, rows, target, min_deals).head(limit).copy()
    if profile.empty:
        return {
            "title": f"تحليل {target}",
            "summary": f"وجدت بيانات عن {target}، لكنها لا تتجاوز حد العقود الحالي لقراءة موثوقة.",
            "method": "تم بناء ملف الحي من آخر فترة متاحة ومقارنة أنواع العقار داخل الحي بالسوق المحيط.",
            "filters": [*filters, f"الحي: {target}"],
            "table": profile,
            "facts": {},
            "reasons": [],
            "warnings": ["خفّض حد العقود من الفلاتر أو استخدم نطاقًا زمنيًا أوسع."],
            "followups": neighborhood_followups(target),
            "limit": limit,
        }

    best = profile.iloc[0]
    latest_period = str(best.get("period", period_label(rows)))
    total_deals = safe_float(profile["total_deals"].sum(), 0)
    weighted_rent = weighted_average(profile, "average_rent", "total_deals")
    property_types = profile["property_type"].nunique()
    best_type = str(best.get("property_type", "-"))
    best_score = safe_float(best.get("score", 0))
    growth = best.get("growth_pct", pd.NA)
    growth_text = "-" if pd.isna(growth) else format_pct_text(float(growth))
    rent_gap = best.get("rent_gap_pct")
    rent_gap_text = format_pct_text(rent_gap if rent_gap is not None and not pd.isna(rent_gap) else None)
    city_text = profile_scope_text(rows)

    return {
        "title": f"ملف حي {target}",
        "decision": neighborhood_profile_decision(best, total_deals, min_deals),
        "summary": (
            f"{target} داخل {city_text} يظهر في آخر فترة ({latest_period}) بمتوسط إيجار مرجح {format_sar(weighted_rent)} "
            f"وإجمالي {total_deals:,.0f} عقد عبر {property_types:,.0f} أنواع عقار. "
            f"أقوى شريحة حاليًا هي {best_type} بدرجة {best_score:,.1f}/100، "
            f"مع نمو {growth_text} وفارق عن السوق المحيط {rent_gap_text}."
        ),
        "method": (
            "حللت الحي من قاعدة البيانات حسب آخر فترة متاحة، ثم قارنت كل نوع عقار داخل الحي بمتوسط السوق لنفس النوع، "
            "وقست السيولة بعدد العقود، النمو مقابل الفترة السابقة، وجاذبية السعر النسبية."
        ),
        "filters": [*filters, f"الحي: {target}"],
        "table": profile,
        "reasons": neighborhood_profile_reasons(best, profile, target),
        "warnings": neighborhood_profile_warnings(rows, profile, min_deals),
        "followups": neighborhood_followups(target),
        "limit": limit,
        "facts": {
            "آخر فترة": latest_period,
            "متوسط الحي": format_sar(weighted_rent),
            "العقود": f"{total_deals:,.0f}",
            "أقوى نوع": best_type,
        },
    }


def requested_neighborhood_profile_target(data: pd.DataFrame, question: str) -> str | None:
    if data.empty or not is_neighborhood_profile_question(question):
        return None

    normalized = normalize_search_text(question)
    if "district_ar" in data.columns:
        district_matches = matching_values(data["district_ar"].dropna().unique(), normalized)
        district_matches = [value for value in district_matches if normalize_search_text(value)]
        if district_matches:
            return district_matches[0]

    location_matches = matching_values(data["location_ar"].dropna().unique(), normalized)
    if location_matches:
        location = str(location_matches[0])
        return location.split(" - ")[-1].strip() or location
    return None


def is_neighborhood_profile_question(question: str) -> bool:
    normalized = normalize_search_text(question)
    cues = [
        "اشرح",
        "شرح",
        "حلل",
        "تحليل",
        "وضع",
        "تفصيل",
        "تفصيلا",
        "بالتفصيل",
        "ملف",
        "تقييم",
        "قيمني",
        "كيف",
        "ماذا عن",
    ]
    return any(cue in normalized for cue in cues)


def neighborhood_profile_rows(data: pd.DataFrame, target: str) -> pd.DataFrame:
    normalized = normalize_search_text(target)
    if data.empty or not normalized:
        return data.iloc[0:0].copy()

    mask = pd.Series(False, index=data.index)
    if "district_ar" in data.columns:
        mask = mask | data["district_ar"].map(normalize_search_text).eq(normalized)
    if "location_ar" in data.columns:
        mask = mask | data["location_ar"].map(normalize_search_text).str.contains(
            normalized,
            na=False,
            regex=False,
        )
    return data[mask].copy()


def build_neighborhood_profile(
    data: pd.DataFrame,
    rows: pd.DataFrame,
    target: str,
    min_deals: int,
) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()

    latest_period = rows["period_index"].max()
    latest_rows = rows[rows["period_index"] == latest_period].copy()
    profile = aggregate_market(
        latest_rows,
        ["region_ar", "city_ar", "location_ar", "district_ar", "property_type", "period"],
    )
    profile = profile.dropna(subset=["average_rent", "total_deals"]).copy()
    if profile.empty:
        return profile

    benchmark = neighborhood_profile_benchmark(data, latest_period)
    profile = profile.merge(
        benchmark,
        on="property_type",
        how="left",
    )
    profile["rent_gap_pct"] = profile.apply(
        lambda row: pct_delta(row["average_rent"], row.get("market_average_rent")),
        axis=1,
    )

    growth = neighborhood_profile_growth(rows)
    profile = profile.merge(growth, on="property_type", how="left")
    profile = add_neighborhood_profile_scores(profile, benchmark)
    profile["profile_note"] = profile.apply(profile_row_note, axis=1)
    profile = profile[profile["total_deals"] >= min_deals].copy()
    if profile.empty:
        return profile
    return profile.sort_values(["score", "total_deals"], ascending=False)


def neighborhood_profile_benchmark(data: pd.DataFrame, latest_period: int) -> pd.DataFrame:
    latest = data[data["period_index"] == latest_period].copy()
    market = aggregate_market(latest, ["location_ar", "property_type"])
    if market.empty:
        return pd.DataFrame(columns=["property_type", "market_average_rent", "market_median_deals"])

    market["market_demand_rank"] = market.groupby("property_type")["total_deals"].rank(pct=True)
    market["market_affordability_rank"] = 1 - market.groupby("property_type")["average_rent"].rank(pct=True)
    rows = []
    for property_type, group in market.groupby("property_type", dropna=False):
        rows.append(
            {
                "property_type": property_type,
                "market_average_rent": weighted_average(group, "average_rent", "total_deals"),
                "market_median_deals": group["total_deals"].median(),
                "market_max_deals": group["total_deals"].max(),
            }
        )
    return pd.DataFrame(rows)


def neighborhood_profile_growth(rows: pd.DataFrame) -> pd.DataFrame:
    trend = aggregate_market(rows, ["period_index", "period", "property_type"])
    if trend.empty:
        return pd.DataFrame(columns=["property_type", "previous_period", "previous_average_rent", "growth_pct"])
    trend = trend.sort_values(["property_type", "period_index"]).copy()
    grouped = trend.groupby("property_type", dropna=False)
    trend["previous_period"] = grouped["period"].shift(1)
    trend["previous_average_rent"] = grouped["average_rent"].shift(1)
    trend["growth_pct"] = pct_series(trend["average_rent"], trend["previous_average_rent"])
    latest = trend[trend["period_index"] == trend["period_index"].max()].copy()
    return latest[["property_type", "previous_period", "previous_average_rent", "growth_pct"]]


def add_neighborhood_profile_scores(profile: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    scored = profile.copy()
    max_deals = scored["market_max_deals"].replace(0, pd.NA)
    scored["liquidity_score"] = (scored["total_deals"] / max_deals * 100).clip(lower=0, upper=100)
    scored["affordability_score"] = (100 - scored["rent_gap_pct"].fillna(0)).clip(lower=0, upper=100)
    scored["growth_score"] = ((scored["growth_pct"].fillna(0).clip(lower=-25, upper=35) + 25) / 60 * 100).clip(
        lower=0,
        upper=100,
    )
    scored["score"] = (
        scored["liquidity_score"].fillna(0) * 0.42
        + scored["growth_score"].fillna(50) * 0.30
        + scored["affordability_score"].fillna(50) * 0.28
    ).clip(lower=0, upper=100)
    return scored


def profile_row_note(row: pd.Series) -> str:
    liquidity = safe_float(row.get("liquidity_score", 0))
    growth = row.get("growth_pct", pd.NA)
    gap = row.get("rent_gap_pct", pd.NA)
    if liquidity >= 70 and not pd.isna(growth) and float(growth) >= 5:
        return "طلب قوي مع نمو إيجابي"
    if liquidity >= 70:
        return "سيولة قوية"
    if not pd.isna(gap) and float(gap) <= -8:
        return "سعر أقل من السوق المحيط"
    if not pd.isna(growth) and float(growth) < -5:
        return "تباطؤ يحتاج متابعة"
    return "قراءة متوسطة"


def neighborhood_profile_decision(row: pd.Series, total_deals: float, min_deals: int) -> str:
    score = safe_float(row.get("score", 0))
    liquidity = safe_float(row.get("liquidity_score", 0))
    growth = row.get("growth_pct", pd.NA)
    if score >= 75 and liquidity >= 65:
        return "القرار: الحي نشط وقابل للدراسة، خصوصًا في الشريحة الأعلى درجة، مع ضرورة مقارنة سعر الصفقة الفعلي."
    if score >= 60 and total_deals >= min_deals * 3:
        return "القرار: الحي مناسب للمراقبة الجادة والانتقاء، وليس للشراء العشوائي."
    if not pd.isna(growth) and float(growth) < -8:
        return "القرار: الحي يحتاج حذرًا؛ توجد إشارة تراجع في الشريحة الأقوى."
    return "القرار: القراءة أولية وتحتاج تحققًا ميدانيًا أو بيانات بيع قبل اتخاذ قرار استثماري."


def neighborhood_profile_reasons(row: pd.Series, profile: pd.DataFrame, target: str) -> list[str]:
    reasons = [
        f"أقوى شريحة في {target}: {row.get('property_type', '-')} بدرجة {safe_float(row.get('score', 0)):,.1f}/100.",
        f"حجم العقود في هذه الشريحة {safe_float(row.get('total_deals', 0)):,.0f} عقد، وسيولتها {safe_float(row.get('liquidity_score', 0)):,.0f}/100 مقارنة بنفس النوع.",
    ]
    gap = row.get("rent_gap_pct", pd.NA)
    if not pd.isna(gap):
        reasons.append(f"متوسط الإيجار يختلف عن السوق المحيط لنفس النوع بنحو {format_pct_text(float(gap))}.")
    growth = row.get("growth_pct", pd.NA)
    if not pd.isna(growth):
        reasons.append(f"النمو مقابل الفترة السابقة {format_pct_text(float(growth))}.")
    if profile["property_type"].nunique() > 1:
        best_types = "، ".join(profile["property_type"].astype(str).head(3))
        reasons.append(f"الحي يحتوي أكثر من شريحة قابلة للقراءة، وأبرزها: {best_types}.")
    return reasons[:5]


def neighborhood_profile_warnings(rows: pd.DataFrame, profile: pd.DataFrame, min_deals: int) -> list[str]:
    warnings: list[str] = [
        "البيانات الحالية إيجارية؛ لا تكفي وحدها لتحديد سعر شراء عادل أو سعر متر بيع.",
    ]
    if rows["city_ar"].nunique() > 1:
        cities = "، ".join(rows["city_ar"].dropna().astype(str).unique()[:4])
        warnings.append(f"اسم الحي موجود في أكثر من مدينة داخل النطاق الحالي: {cities}. استخدم فلتر المدينة لقراءة أدق.")
    if safe_float(profile["total_deals"].sum(), 0) < min_deals * 4:
        warnings.append("حجم العقود محدود نسبيًا؛ ارفع الثقة بتوسيع الفترة أو مقارنة الحي بأحياء قريبة.")
    if profile["growth_pct"].isna().all():
        warnings.append("لا توجد مقارنة نمو كافية لكل الشرائح في آخر فترتين.")
    return warnings[:4]


def neighborhood_followups(target: str) -> list[str]:
    return [
        f"قارن {target} مع حي قريب",
        f"ما أفضل نوع عقار داخل {target}؟",
        f"ما مخاطر الاستثمار في {target}؟",
    ]


def profile_scope_text(rows: pd.DataFrame) -> str:
    cities = rows["city_ar"].dropna().astype(str).unique()
    regions = rows["region_ar"].dropna().astype(str).unique()
    if len(cities) == 1:
        return cities[0]
    if len(regions) == 1:
        return regions[0]
    return f"{len(cities):,.0f} مدن"


def answer_budget_question(
    question: str,
    scoped: pd.DataFrame,
    filters: list[str],
    min_deals: int,
    limit: int,
    budget: float,
) -> dict[str, object]:
    source, budget_filters = budget_analysis_scope(scoped, question, budget)
    ranking = budget_opportunity_ranking(source, min_deals, budget).head(limit).copy()
    budget_text = format_sar(budget)
    filter_items = [*filters, *budget_filters, f"رأس المال: {budget_text}"]
    filter_text = "، ".join(filter_items) if filter_items else "حسب الفلاتر الحالية"

    if ranking.empty:
        return {
            "title": "لا توجد نتيجة كافية لهذه الميزانية",
            "summary": (
                f"لم أجد شرائح تتجاوز حد العقود الحالي لتحليل ميزانية {budget_text}. "
                "جرّب تحديد مدينة أوسع أو خفض حد العقود من الفلاتر."
            ),
            "method": "تم البحث في قاعدة البيانات عن شرائح لديها متوسط إيجار وعدد عقود كافيين، ثم لم تظهر عينة قابلة للترتيب.",
            "filters": filter_items,
            "table": ranking,
            "facts": {"الميزانية": budget_text},
            "reasons": [],
            "warnings": ["البيانات الحالية إيجارية؛ لا تحتوي سعر بيع فعلي لكل عقار."],
            "followups": budget_followups(budget),
            "limit": limit,
        }

    best = ranking.iloc[0]
    location = str(best.get("location_ar", "-"))
    property_type = str(best.get("property_type", "-"))
    score = safe_float(best.get("budget_fit_score", 0))
    rent = safe_float(best.get("average_rent", 0))
    deals = safe_float(best.get("total_deals", 0))
    yield_pct = safe_float(best.get("budget_yield_pct", 0))
    growth = best.get("growth_pct", pd.NA)
    growth_text = "-" if pd.isna(growth) else format_pct_text(float(growth))
    top_names = "، ".join(
        f"{row.get('location_ar', '-')}" for _, row in ranking.head(3).iterrows()
    )

    return {
        "title": f"تحليل ميزانية {budget_text}",
        "decision": (
            f"الأفضل مبدئيًا حسب قاعدة البيانات: {location} لنوع {property_type}. "
            f"هذه توصية فرز أولي وليست تأكيدًا أن سعر الشراء متاح بهذا الرقم."
        ),
        "summary": (
            f"بناءً على ميزانية {budget_text}، أفضل المناطق/الشرائح المرشحة هي: {top_names}. "
            f"النتيجة الأولى تعطي عائدًا إيجاريًا تقديريًا {yield_pct:,.2f}% إذا كان رأس المال كاملًا هو سعر الدخول، "
            f"مع {deals:,.0f} عقد ونمو {growth_text}. نطاق الإجابة: {filter_text}."
        ),
        "method": (
            "حللت قاعدة البيانات الحالية بترتيب الشرائح حسب متوسط الإيجار السنوي مقابل رأس المال، "
            "قوة الطلب، النمو، وجاذبية السعر النسبية. لا أتعامل معها كتقييم بيع رسمي لأن مصدر البيانات الحالي إيجاري."
        ),
        "filters": filter_items,
        "table": ranking,
        "reasons": budget_reasons(best, ranking, budget),
        "warnings": [
            "البيانات الحالية لا تحتوي أسعار بيع فعلية أو سعر متر شراء؛ لذلك العائد هنا تقديري مبني على الإيجار فقط.",
            "قبل الشراء قارن سعر الصفقة الفعلي بمتوسط الحي، وحالة العقار، والشارع، والخدمات.",
        ],
        "followups": budget_followups(budget),
        "limit": limit,
        "facts": {
            "الميزانية": budget_text,
            "أفضل درجة": f"{score:,.1f}",
            "عائد تقديري": f"{yield_pct:,.2f}%",
            "العقود": f"{deals:,.0f}",
        },
    }


def budget_opportunity_ranking(frame: pd.DataFrame, min_deals: int, budget: float) -> pd.DataFrame:
    if frame.empty or budget <= 0:
        return pd.DataFrame()

    ranking = opportunity_scores(frame, min_deals=min_deals).copy()
    if ranking.empty:
        return ranking

    ranking = ranking.dropna(subset=["average_rent", "total_deals"]).copy()
    if ranking.empty:
        return ranking

    ranking["estimated_annual_rent"] = pd.to_numeric(ranking["average_rent"], errors="coerce")
    ranking["budget_yield_pct"] = ranking["estimated_annual_rent"] / budget * 100
    ranking["yield_rank"] = ranking["budget_yield_pct"].clip(lower=0, upper=9).rank(pct=True)

    if "demand_rank" not in ranking:
        ranking["demand_rank"] = ranking["total_deals"].rank(pct=True)
    if "growth_rank" not in ranking:
        ranking["growth_rank"] = ranking["growth_pct"].fillna(0).clip(lower=-50, upper=50).rank(pct=True)
    if "affordability_rank" not in ranking:
        ranking["affordability_rank"] = 1 - ranking["average_rent"].rank(pct=True)

    ranking["budget_fit_score"] = (
        ranking["yield_rank"] * 38
        + ranking["demand_rank"] * 28
        + ranking["growth_rank"] * 22
        + ranking["affordability_rank"] * 12
    ).clip(lower=0, upper=100)
    ranking["score"] = ranking["budget_fit_score"]
    ranking["budget_note"] = ranking.apply(budget_row_note, axis=1)
    return ranking.sort_values("budget_fit_score", ascending=False)


def budget_analysis_scope(
    frame: pd.DataFrame,
    question: str,
    budget: float,
) -> tuple[pd.DataFrame, list[str]]:
    if frame.empty or "property_type" not in frame.columns:
        return frame, []

    normalized = normalize_search_text(question)
    explicit_types = matching_property_types(frame["property_type"].dropna().unique(), normalized)
    if explicit_types:
        return frame, []

    property_types = set(frame["property_type"].dropna().astype(str))
    if budget <= 1_500_000 and "شقة" in property_types:
        return frame[frame["property_type"].eq("شقة")].copy(), ["نوع العقار الافتراضي: شقة"]

    residential_types = [value for value in ["شقة", "دور", "دوبلاكس", "فيلا"] if value in property_types]
    if residential_types:
        return frame[frame["property_type"].isin(residential_types)].copy(), ["النطاق: العقارات السكنية"]

    return frame, []


def budget_row_note(row: pd.Series) -> str:
    yield_pct = safe_float(row.get("budget_yield_pct", 0))
    demand_rank = safe_float(row.get("demand_rank", 0))
    if yield_pct >= 5 and demand_rank >= 0.65:
        return "عائد وطلب قويان"
    if yield_pct >= 4:
        return "عائد مقبول يحتاج تحقق"
    if demand_rank >= 0.75:
        return "طلب قوي لكن العائد أقل"
    return "فرصة مراقبة"


def budget_reasons(row: pd.Series, ranking: pd.DataFrame, budget: float) -> list[str]:
    reasons = assistant_reasons(row, ranking, "opportunity")
    yield_pct = safe_float(row.get("budget_yield_pct", 0))
    rent = safe_float(row.get("estimated_annual_rent", row.get("average_rent", 0)))
    reasons.insert(
        0,
        f"إذا اعتبرنا {format_sar(budget)} رأس مال للدخول، فإن متوسط الإيجار السنوي يعطي عائدًا تقديريًا {yield_pct:,.2f}% ({format_sar(rent)} سنويًا).",
    )
    note = str(row.get("budget_note", ""))
    if note:
        reasons.append(f"قراءة الميزانية: {note}.")
    return reasons[:5]


def budget_followups(budget: float) -> list[str]:
    budget_text = format_sar(budget)
    return [
        f"حلل {budget_text} للشقق فقط في الرياض",
        f"ما أعلى عائد تقديري لميزانية {budget_text}؟",
        f"قارن أفضل حيّين لميزانية {budget_text}",
    ]


def extract_investment_budget(question: str) -> float | None:
    text = (
        arabic_digits_to_western(str(question))
        .replace(",", "")
        .replace("٬", "")
        .replace("٫", ".")
    )
    normalized = normalize_search_text(text)
    search_text = text.lower()
    has_budget_cue = any(
        cue in normalized
        for cue in [
            "لدي",
            "معي",
            "ميزانيه",
            "ميزانية",
            "راس المال",
            "رأس المال",
            "استثمر",
            "استثمار",
            "مبلغ",
            "كاش",
        ]
    )

    pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(الف|ألف|الاف|ألاف|آلاف|مليون|ملايين|مليونين|k|m)?")
    candidates: list[float] = []
    for match in pattern.finditer(search_text):
        value = float(match.group(1))
        suffix = match.group(2) or ""
        if suffix in {"الف", "ألف", "الاف", "ألاف", "آلاف", "k"}:
            value *= 1_000
        elif suffix in {"مليون", "ملايين", "مليونين", "m"}:
            value *= 1_000_000
        elif has_budget_cue and 100 <= value < 10_000:
            value *= 1_000

        if value >= 100_000 and (has_budget_cue or suffix or value >= 500_000):
            candidates.append(value)

    if not candidates:
        return None
    return max(candidates)


def arabic_digits_to_western(text: str) -> str:
    translation = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    return text.translate(translation)


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
        "district_ar",
        "property_type",
        "period",
        "average_rent",
        "rent_gap_pct",
        "budget_yield_pct",
        "total_deals",
        "growth_pct",
        "liquidity_score",
        "budget_fit_score",
        "score",
        "budget_note",
        "profile_note",
    ]
    available = [column for column in columns if column in table.columns]
    if "budget_fit_score" in available and "score" in available:
        available.remove("score")
    view = table[available].head(limit).rename(
        columns={
            "region_ar": "المنطقة",
            "city_ar": "المدينة",
            "location_ar": "الموقع",
            "district_ar": "الحي",
            "property_type": "نوع العقار",
            "period": "الفترة",
            "average_rent": "متوسط الإيجار",
            "rent_gap_pct": "فارق السوق %",
            "budget_yield_pct": "عائد تقديري %",
            "total_deals": "العقود",
            "growth_pct": "النمو %",
            "liquidity_score": "السيولة",
            "budget_fit_score": "ملاءمة الميزانية",
            "score": "الدرجة",
            "budget_note": "قراءة الميزانية",
            "profile_note": "قراءة الشريحة",
        }
    )
    formatters = {
        "متوسط الإيجار": "{:,.0f}",
        "فارق السوق %": "{:,.1f}",
        "عائد تقديري %": "{:,.2f}",
        "العقود": "{:,.0f}",
        "النمو %": "{:,.1f}",
        "السيولة": "{:,.1f}",
        "ملاءمة الميزانية": "{:,.1f}",
        "الدرجة": "{:,.1f}",
    }
    st.dataframe(
        view.style.format({key: value for key, value in formatters.items() if key in view.columns}),
        width="stretch",
        hide_index=True,
    )


def render_data_engine_status() -> None:
    status = warehouse_status()
    with st.container(border=True):
        st.subheader("Data Engine V1")
        if status.get("ready"):
            cols = st.columns(4)
            cols[0].metric("حالة القاعدة", "جاهزة")
            cols[1].metric("السجلات", f"{safe_float(status.get('rows', 0)):,.0f}")
            cols[2].metric("المواقع", f"{safe_float(status.get('locations', 0)):,.0f}")
            cols[3].metric("آخر فترة", str(status.get("latest_period", "-")))
            st.caption(f"المسار المحلي: {status.get('path')}")
        else:
            st.warning("لم يتم إنشاء قاعدة البيانات المحلية بعد. سيستخدم التطبيق البيانات المعالجة كمسار احتياطي.")
            st.caption(f"المسار المتوقع: {status.get('path')}")


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
    decision_tab, analyst_tab, market_tab, data_tab = st.tabs(
        ["قرار المستثمر", "المحلل العقاري", "السوق والخرائط", "البيانات والجودة"]
    )

    with decision_tab:
        render_riyadh_first_page(data, settings)

    with analyst_tab:
        render_ai_briefing(filtered, settings, snapshot)
        render_decision_assistant(filtered, settings, snapshot)

    with market_tab:
        render_kpis(filtered, settings, snapshot)
        render_charts(filtered, settings, snapshot)
        with st.expander("قائمة الفرص المحسوبة", expanded=False):
            render_opportunities(filtered, settings, snapshot)
        riyadh = riyadh_focus_data(data)
        if not riyadh.empty:
            with st.expander("خرائط الرياض الحرارية وتوزيع الصفقات", expanded=False):
                render_riyadh_market_maps(riyadh, settings)

    with data_tab:
        render_data_engine_status()
        render_market_coverage(data, filtered)
        render_data_quality(filtered)
        with st.expander("البيانات الموحدة", expanded=False):
            render_data_table(filtered, nested=True)


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
    riyadh = riyadh_focus_data(data)
    if riyadh.empty:
        return

    st.subheader("أين توجد الفرص العقارية في الرياض؟")
    st.caption("هذه الصفحة مختصرة للقرار: أفضل الفرص، سبب الترشيح، مقارنة الأحياء، ومحرك تقييم سريع. الخرائط والجداول التفصيلية موجودة في تبويبات منفصلة.")

    decision_scores = build_riyadh_property_scores(riyadh, int(settings["min_deals"]))
    render_riyadh_decision_platform(riyadh, decision_scores, settings)

    st.divider()
    render_property_valuation_engine(riyadh)


def riyadh_focus_data(data: pd.DataFrame) -> pd.DataFrame:
    return data[data["city_ar"].map(normalize_search_text).eq(normalize_search_text("الرياض"))].copy()


def build_riyadh_property_scores(riyadh: pd.DataFrame, min_deals: int) -> pd.DataFrame:
    if riyadh.empty:
        return pd.DataFrame()

    work = riyadh.copy()
    work["neighborhood"] = work.apply(neighborhood_label, axis=1)
    market = aggregate_market(work, ["period_index", "period", "neighborhood", "property_type"])
    if market.empty:
        return market

    market = market.sort_values(["neighborhood", "property_type", "period_index"]).copy()
    grouped = market.groupby(["neighborhood", "property_type"], dropna=False)
    market["previous_period"] = grouped["period"].shift(1)
    market["previous_average_rent"] = grouped["average_rent"].shift(1)
    market["previous_total_deals"] = grouped["total_deals"].shift(1)
    market["growth_pct"] = pct_series(market["average_rent"], market["previous_average_rent"])
    market["deals_growth_pct"] = pct_series(market["total_deals"], market["previous_total_deals"])

    latest_period = market["period_index"].max()
    latest = market[market["period_index"] == latest_period].copy()
    latest = latest.dropna(subset=["average_rent", "total_deals"])
    latest = latest[latest["total_deals"] >= min_deals].copy()
    if latest.empty:
        return latest

    city_averages = []
    for property_type, group in latest.groupby("property_type", dropna=False):
        city_averages.append(
            {
                "property_type": property_type,
                "city_average_rent": weighted_average(group, "average_rent", "total_deals"),
            }
        )
    latest = latest.merge(pd.DataFrame(city_averages), on="property_type", how="left")
    latest["price_gap_pct"] = latest.apply(
        lambda row: pct_delta(row["average_rent"], row["city_average_rent"]),
        axis=1,
    )

    latest["growth_pct"] = pd.to_numeric(latest["growth_pct"], errors="coerce")
    latest["deals_growth_pct"] = pd.to_numeric(latest["deals_growth_pct"], errors="coerce")
    latest["average_rent"] = pd.to_numeric(latest["average_rent"], errors="coerce")
    latest["total_deals"] = pd.to_numeric(latest["total_deals"], errors="coerce")
    latest["demand_rank"] = latest["total_deals"].rank(pct=True)
    latest["growth_rank"] = latest["growth_pct"].fillna(0).clip(lower=-50, upper=50).rank(pct=True)
    latest["affordability_rank"] = 1 - latest["average_rent"].rank(pct=True)
    volatility = latest["growth_pct"].fillna(0).abs().clip(lower=0, upper=80) / 80
    latest["risk_score"] = (latest["demand_rank"] * 65 + (1 - volatility) * 35).clip(lower=0, upper=100)
    latest["liquidity_score"] = latest["demand_rank"] * 100
    latest["property_score"] = (
        latest["growth_rank"] * 35
        + latest["demand_rank"] * 30
        + latest["affordability_rank"] * 20
        + (latest["risk_score"] / 100) * 15
    ).clip(lower=0, upper=100)
    latest["score"] = latest["property_score"]
    return latest.sort_values("property_score", ascending=False)


def render_riyadh_decision_platform(
    riyadh: pd.DataFrame,
    scores: pd.DataFrame,
    settings: dict[str, object],
) -> None:
    st.subheader("Decision Intelligence Platform")
    st.caption("طبقة قرار فوق بيانات الرياض: فرص قابلة للتنفيذ، تنبيهات سوق، مقارنة أحياء، وتقرير عقاري ذكي للمستثمر.")

    if scores.empty:
        st.info("لا توجد فرص كافية الثقة داخل الرياض حسب حد العقود الحالي. خفف حد العقود أو انتظر تحديث بيانات أوسع.")
        return

    render_market_alerts(scores)

    opportunity_tab, comparison_tab, report_tab = st.tabs(
        ["Investment Opportunities", "مقارنة الأحياء", "AI Report Generator"]
    )
    with opportunity_tab:
        render_investment_opportunities(scores)
    with comparison_tab:
        render_neighborhood_comparison_engine(scores)
    with report_tab:
        render_ai_report_generator(scores, riyadh, settings)


def render_investment_opportunities(scores: pd.DataFrame) -> None:
    st.markdown("### أفضل فرص الفترة الحالية")
    st.caption("Property Score يجمع النمو، السيولة، جاذبية السعر، واستقرار الإشارة. القراءة هنا أولية وليست تقييمًا رسميًا.")

    top = scores.head(10).copy()
    cards = top.head(3)
    cols = st.columns(min(len(cards), 3))
    for index, (_, row) in enumerate(cards.iterrows()):
        with cols[index % len(cols)]:
            render_opportunity_card(row, index + 1)

    view = top.assign(
        **{
            "Property Score": top["property_score"].map(lambda value: f"{safe_float(value):,.1f}/100"),
            "فارق عن متوسط الرياض": top["price_gap_pct"].map(format_pct_text),
            "النمو": top["growth_pct"].map(format_pct_text),
            "السيولة": top["liquidity_score"].map(lambda value: f"{safe_float(value):,.0f}/100"),
            "المخاطر": top["risk_score"].map(risk_label),
            "متوسط الإيجار": top["average_rent"].map(format_sar),
            "العقود": top["total_deals"].map(lambda value: f"{safe_float(value):,.0f}"),
        }
    )
    st.dataframe(
        view[
            [
                "neighborhood",
                "property_type",
                "Property Score",
                "متوسط الإيجار",
                "فارق عن متوسط الرياض",
                "النمو",
                "العقود",
                "السيولة",
                "المخاطر",
            ]
        ].rename(columns={"neighborhood": "الحي", "property_type": "نوع العقار"}),
        width="stretch",
        hide_index=True,
    )


def render_opportunity_card(row: pd.Series, rank: int) -> None:
    neighborhood = str(row.get("neighborhood", "-"))
    property_type = str(row.get("property_type", "-"))
    score = safe_float(row.get("property_score", 0))
    rent = format_sar(safe_float(row.get("average_rent", 0)))
    deals = safe_float(row.get("total_deals", 0))
    growth = format_pct_text(row.get("growth_pct"))
    gap = format_pct_text(row.get("price_gap_pct"))
    with st.container(border=True):
        st.metric(f"{rank}- {neighborhood} | {property_type}", f"{score:,.1f}/100")
        st.write(investment_reason(row))
        st.info(score_recommendation(score))
        metric_cols = st.columns(2)
        metric_cols[0].metric("متوسط الإيجار", rent)
        metric_cols[1].metric("العقود", f"{deals:,.0f}")
        metric_cols[0].metric("النمو", growth)
        metric_cols[1].metric("الفارق", gap)


def investment_reason(row: pd.Series) -> str:
    gap = row.get("price_gap_pct")
    growth = row.get("growth_pct")
    demand_rank = safe_float(row.get("demand_rank", 0))

    reasons = []
    if gap is not None and not pd.isna(gap):
        if float(gap) <= -8:
            reasons.append(f"السعر/الإيجار أقل من متوسط الرياض بنحو {abs(float(gap)):.1f}%")
        elif float(gap) >= 8:
            reasons.append(f"السعر/الإيجار أعلى من متوسط الرياض بنحو {float(gap):.1f}%")
        else:
            reasons.append("السعر قريب من متوسط الرياض لنفس النوع")
    if growth is not None and not pd.isna(growth):
        reasons.append(f"النمو {format_pct_text(float(growth))}")
    if demand_rank >= 0.75:
        reasons.append("السيولة مرتفعة")
    elif demand_rank >= 0.45:
        reasons.append("السيولة متوسطة")
    else:
        reasons.append("السيولة تحتاج متابعة")
    return "، ".join(reasons) + "."


def score_recommendation(score: float) -> str:
    if score >= 78:
        return "قرار أولي: دراسة جادة"
    if score >= 62:
        return "قرار أولي: مراقبة مع تفاوض"
    return "قرار أولي: يحتاج تحقق إضافي"


def render_market_alerts(scores: pd.DataFrame) -> None:
    alerts = market_alerts(scores)
    if not alerts:
        return
    st.markdown("### تنبيهات سوق تعطي سببًا للعودة")
    cols = st.columns(min(len(alerts), 4))
    for index, alert in enumerate(alerts):
        with cols[index % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**{alert['title']}**")
                st.write(alert["body"])


def market_alerts(scores: pd.DataFrame) -> list[dict[str, str]]:
    if scores.empty:
        return []

    alerts: list[dict[str, str]] = []
    top = scores.iloc[0]
    alerts.append(
        {
            "title": "فرصة جديدة في أعلى القائمة",
            "body": (
                f"{top['neighborhood']} | {top['property_type']} وصلت إلى "
                f"{safe_float(top.get('property_score', 0)):,.1f}/100 مع {safe_float(top.get('total_deals', 0)):,.0f} عقد."
            ),
        }
    )

    undervalued = scores[
        (scores["price_gap_pct"].notna())
        & (scores["price_gap_pct"] <= -8)
        & (scores["demand_rank"] >= 0.55)
    ].sort_values("property_score", ascending=False)
    if not undervalued.empty:
        row = undervalued.iloc[0]
        alerts.append(
            {
                "title": "سعر أقل من متوسط السوق",
                "body": (
                    f"{row['neighborhood']} | {row['property_type']} أقل من متوسط الرياض لنفس النوع "
                    f"بنحو {abs(safe_float(row.get('price_gap_pct', 0))):.1f}% مع طلب قابل للقياس."
                ),
            }
        )

    moving = scores[
        (scores["growth_pct"].notna())
        & (scores["growth_pct"] >= 8)
        & (scores["total_deals"] >= scores["total_deals"].median())
    ].sort_values("growth_pct", ascending=False)
    if not moving.empty:
        row = moving.iloc[0]
        alerts.append(
            {
                "title": "حي بدأ يتحرك",
                "body": (
                    f"{row['neighborhood']} | {row['property_type']} سجل نموًا "
                    f"{format_pct_text(row.get('growth_pct'))} مع سيولة أعلى من متوسط القائمة."
                ),
            }
        )

    liquid = scores[
        (scores["deals_growth_pct"].notna())
        & (scores["deals_growth_pct"] >= 15)
    ].sort_values("deals_growth_pct", ascending=False)
    if not liquid.empty:
        row = liquid.iloc[0]
        alerts.append(
            {
                "title": "نشاط صفقات متسارع",
                "body": (
                    f"{row['neighborhood']} | {row['property_type']} ارتفع نشاط العقود "
                    f"{format_pct_text(row.get('deals_growth_pct'))} مقارنة بالفترة السابقة."
                ),
            }
        )

    return alerts[:4]


def render_neighborhood_comparison_engine(scores: pd.DataFrame) -> None:
    st.markdown("### محرك مقارنة الأحياء")
    st.caption("اختر حيّين ونوع العقار، ثم قارن السعر، النمو، السيولة، عدد العقود، والمخاطر.")

    property_types = sorted(scores["property_type"].dropna().astype(str).unique())
    preferred_type = "شقة" if "شقة" in property_types else property_types[0]
    selected_type = st.selectbox(
        "نوع العقار للمقارنة",
        property_types,
        index=property_types.index(preferred_type),
        key="comparison_property_type",
    )
    scope = scores[scores["property_type"].eq(selected_type)].copy()
    neighborhoods = sorted(scope["neighborhood"].dropna().astype(str).unique())
    if len(neighborhoods) < 2:
        st.info("لا توجد أحياء كافية للمقارنة لهذا النوع ضمن حد العقود الحالي.")
        return

    default_a = neighborhoods.index("النرجس") if "النرجس" in neighborhoods else 0
    default_b = neighborhoods.index("العارض") if "العارض" in neighborhoods else min(1, len(neighborhoods) - 1)
    if default_a == default_b:
        default_b = 1 if default_a == 0 else 0

    left, right = st.columns(2)
    with left:
        first = st.selectbox("الحي الأول", neighborhoods, index=default_a, key="comparison_first")
    with right:
        second = st.selectbox("الحي الثاني", neighborhoods, index=default_b, key="comparison_second")

    row_a = score_row_for_neighborhood(scope, first)
    row_b = score_row_for_neighborhood(scope, second)
    if row_a is None or row_b is None:
        st.warning("لا توجد بيانات كافية لأحد الحيين داخل نوع العقار المختار.")
        return

    st.dataframe(comparison_metric_table(row_a, row_b), width="stretch", hide_index=True)
    verdict_type, verdict = comparison_verdict(row_a, row_b)
    if verdict_type == "success":
        st.success(verdict)
    elif verdict_type == "warning":
        st.warning(verdict)
    else:
        st.info(verdict)


def score_row_for_neighborhood(scope: pd.DataFrame, neighborhood: str) -> pd.Series | None:
    normalized = normalize_search_text(neighborhood)
    match = scope[scope["neighborhood"].map(normalize_search_text).eq(normalized)].copy()
    if match.empty:
        return None
    return match.sort_values("property_score", ascending=False).iloc[0]


def comparison_metric_table(row_a: pd.Series, row_b: pd.Series) -> pd.DataFrame:
    first = str(row_a["neighborhood"])
    second = str(row_b["neighborhood"])
    return pd.DataFrame(
        [
            {"المؤشر": "Property Score", first: f"{safe_float(row_a['property_score']):,.1f}/100", second: f"{safe_float(row_b['property_score']):,.1f}/100"},
            {"المؤشر": "متوسط الإيجار", first: format_sar(row_a["average_rent"]), second: format_sar(row_b["average_rent"])},
            {"المؤشر": "الفارق عن متوسط الرياض", first: format_pct_text(row_a.get("price_gap_pct")), second: format_pct_text(row_b.get("price_gap_pct"))},
            {"المؤشر": "النمو", first: format_pct_text(row_a.get("growth_pct")), second: format_pct_text(row_b.get("growth_pct"))},
            {"المؤشر": "السيولة", first: f"{safe_float(row_a.get('liquidity_score', 0)):,.0f}/100", second: f"{safe_float(row_b.get('liquidity_score', 0)):,.0f}/100"},
            {"المؤشر": "عدد العقود", first: f"{safe_float(row_a['total_deals']):,.0f}", second: f"{safe_float(row_b['total_deals']):,.0f}"},
            {"المؤشر": "المخاطر", first: risk_label(row_a.get("risk_score")), second: risk_label(row_b.get("risk_score"))},
        ]
    )


def comparison_verdict(row_a: pd.Series, row_b: pd.Series) -> tuple[str, str]:
    first_score = safe_float(row_a.get("property_score", 0))
    second_score = safe_float(row_b.get("property_score", 0))
    diff = first_score - second_score
    if abs(diff) < 3:
        return (
            "info",
            "النتيجة متقاربة. القرار النهائي يعتمد على سعر الصفقة الفعلي، جودة العقار، والشارع داخل الحي.",
        )

    winner = row_a if diff > 0 else row_b
    loser = row_b if diff > 0 else row_a
    winner_name = str(winner["neighborhood"])
    loser_name = str(loser["neighborhood"])
    winner_growth = format_pct_text(winner.get("growth_pct"))
    winner_liquidity = safe_float(winner.get("liquidity_score", 0))
    message = (
        f"الأفضل للاستثمار طويل المدى حاليًا: {winner_name}. "
        f"يتفوق على {loser_name} بدرجة {abs(diff):,.1f} نقطة، "
        f"مع نمو {winner_growth} وسيولة {winner_liquidity:,.0f}/100. "
        "استخدم هذه النتيجة كبداية للتفاوض وليس كقرار شراء نهائي."
    )
    return ("success" if abs(diff) >= 8 else "warning", message)


def render_ai_report_generator(
    scores: pd.DataFrame,
    riyadh: pd.DataFrame,
    settings: dict[str, object],
) -> None:
    st.markdown("### AI Report Generator")
    st.caption("ينشئ تقريرًا عقاريًا مختصرًا من المؤشرات الحالية: الفرص، الحركة، السيولة، والمخاطر.")

    focus = st.selectbox(
        "نوع التقرير",
        ["تقرير فرص الرياض", "تقرير مخاطر السوق", "تقرير مقارنة أفضل الأحياء"],
        key="ai_report_focus",
    )
    report = build_investor_report(scores, riyadh, focus, int(settings["min_deals"]))
    report_signature = f"{focus}:{period_label(riyadh)}:{len(scores)}"
    if st.session_state.get("investor_report_signature") != report_signature:
        st.session_state["investor_report_text"] = report
        st.session_state["investor_report_signature"] = report_signature
    if st.button("إنشاء تقرير عقاري", type="primary", key="generate_investor_report"):
        st.session_state["investor_report_text"] = report
        st.session_state["investor_report_signature"] = report_signature
    if "investor_report_text" not in st.session_state:
        st.session_state["investor_report_text"] = report

    report_text = str(st.session_state["investor_report_text"])
    with st.container(border=True):
        st.markdown(report_text)
    with st.expander("النص الخام للتقرير", expanded=False):
        st.text_area("نسخة Markdown", value=report_text, height=280)
    period = period_label(riyadh).replace(" ", "-") or "latest"
    st.download_button(
        "تحميل التقرير",
        data=report_text,
        file_name=f"riyadh-investor-report-{period}.md",
        mime="text/markdown",
        key="download_investor_report",
    )


def build_investor_report(
    scores: pd.DataFrame,
    riyadh: pd.DataFrame,
    focus: str,
    min_deals: int,
) -> str:
    period = period_label(riyadh) or "آخر فترة متاحة"
    top = scores.head(5)
    best = top.iloc[0]
    alerts = market_alerts(scores)
    average_score = safe_float(scores["property_score"].mean(), 0)
    high_confidence = scores[scores["total_deals"] >= max(min_deals * 3, min_deals)]

    lines = [
        "# تقرير المحلل العقاري - الرياض",
        f"الفترة: {period}",
        f"نوع التقرير: {focus}",
        "",
        "## الملخص التنفيذي",
        (
            f"أفضل فرصة محسوبة حاليًا هي {best['neighborhood']} | {best['property_type']} "
            f"بدرجة {safe_float(best.get('property_score', 0)):,.1f}/100. "
            f"متوسط درجة الفرص داخل القائمة {average_score:,.1f}/100، "
            f"وعدد الشرائح الأعلى ثقة من ناحية العقود {len(high_confidence):,.0f}."
        ),
        "",
        "## أفضل الفرص",
    ]

    for index, (_, row) in enumerate(top.iterrows(), start=1):
        lines.append(
            (
                f"{index}. {row['neighborhood']} | {row['property_type']} - "
                f"Score {safe_float(row.get('property_score', 0)):,.1f}/100، "
                f"متوسط الإيجار {format_sar(row['average_rent'])}، "
                f"النمو {format_pct_text(row.get('growth_pct'))}، "
                f"العقود {safe_float(row['total_deals']):,.0f}، "
                f"المخاطر {risk_label(row.get('risk_score'))}."
            )
        )

    lines.extend(["", "## إشارات تستحق المتابعة"])
    for alert in alerts:
        lines.append(f"- {alert['title']}: {alert['body']}")

    lines.extend(
        [
            "",
            "## قرار أولي",
            investor_decision_text(best),
            "",
            "## ملاحظة منهجية",
            "المؤشرات تعتمد على بيانات الإيجار والعقود المتاحة حاليًا، لذلك فهي مناسبة للفرز والمقارنة والتفاوض الأولي. قرار الشراء النهائي يحتاج سعر صفقة فعلي، حالة العقار، موقعه الدقيق، والتمويل.",
        ]
    )
    return "\n".join(lines)


def investor_decision_text(row: pd.Series) -> str:
    score = safe_float(row.get("property_score", 0))
    if score >= 78:
        action = "ابدأ دراسة الصفقة والتفاوض فور توفر عقار بسعر قريب أو أقل من متوسط الحي."
    elif score >= 62:
        action = "ضع الحي في قائمة المراقبة واطلب خصمًا واضحًا إذا كان السعر أعلى من المتوسط."
    else:
        action = "لا تتخذ قرارًا سريعًا؛ اطلب بيانات صفقة أدق أو قارن ببدائل أقوى."
    return f"{action} القراءة الأقوى حاليًا: {row['neighborhood']} | {row['property_type']}."


def risk_label(value: object) -> str:
    score = safe_float(value, 0)
    if score >= 75:
        return "منخفضة"
    if score >= 55:
        return "متوسطة"
    return "مرتفعة"


def render_riyadh_market_maps(riyadh: pd.DataFrame, settings: dict[str, object]) -> None:
    min_deals = int(settings["min_deals"])
    latest_market = riyadh_neighborhood_market(riyadh, min_deals)
    if latest_market.empty:
        return

    st.subheader("خريطة السوق العقاري في الرياض")
    st.caption("قراءة سوقية حسب الحي ونوع العقار. المصدر الحالي لا يحتوي إحداثيات جغرافية، لذلك تعرض الخريطة كثافة الأسعار والصفقات بين الأحياء.")

    price_tab, deals_tab, compare_tab = st.tabs(["Heat map الأسعار", "توزيع الصفقات", "مقارنة الأحياء"])
    with price_tab:
        render_riyadh_price_heatmap(latest_market)
    with deals_tab:
        render_riyadh_deals_distribution(latest_market)
    with compare_tab:
        render_riyadh_neighborhood_comparison(latest_market)


def riyadh_neighborhood_market(riyadh: pd.DataFrame, min_deals: int) -> pd.DataFrame:
    if riyadh.empty:
        return pd.DataFrame()

    latest_period = riyadh["period_index"].max()
    latest = riyadh[riyadh["period_index"] == latest_period].copy()
    latest["neighborhood"] = latest.apply(neighborhood_label, axis=1)
    market = aggregate_market(latest, ["neighborhood", "property_type"])
    market = market.dropna(subset=["average_rent", "total_deals"]).copy()
    market = market[market["total_deals"] >= min_deals]
    if market.empty:
        return market

    market["demand_rank"] = market["total_deals"].rank(pct=True)
    market["affordability_rank"] = 1 - market["average_rent"].rank(pct=True)
    market["score"] = market["demand_rank"] * 60 + market["affordability_rank"] * 40
    return market.sort_values("score", ascending=False)


def neighborhood_label(row: pd.Series) -> str:
    district = str(row.get("district_ar", "")).strip()
    if district:
        return district
    location = str(row.get("location_ar", "")).strip()
    return location.replace("الرياض -", "").strip() or "غير محدد"


def riyadh_neighborhood_options(riyadh: pd.DataFrame) -> list[str]:
    if riyadh.empty:
        return ["النرجس"]
    labels = riyadh.apply(neighborhood_label, axis=1)
    options = sorted({label for label in labels if label and label != "غير محدد"})
    return options or ["النرجس"]


def render_riyadh_price_heatmap(market: pd.DataFrame) -> None:
    top_neighborhoods = (
        market.groupby("neighborhood")["total_deals"]
        .sum()
        .sort_values(ascending=False)
        .head(18)
        .index
    )
    top_types = (
        market.groupby("property_type")["total_deals"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .index
    )
    heat = market[
        market["neighborhood"].isin(top_neighborhoods)
        & market["property_type"].isin(top_types)
    ].copy()
    pivot = heat.pivot_table(
        index="neighborhood",
        columns="property_type",
        values="average_rent",
        aggfunc="mean",
    )
    if pivot.empty:
        st.info("لا توجد بيانات كافية لرسم Heat map الأسعار.")
        return

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Teal",
        labels={"x": "نوع العقار", "y": "الحي", "color": "متوسط الإيجار"},
        title="Heat map متوسط الإيجار حسب الحي ونوع العقار",
    )
    apply_chart_spacing(
        fig,
        height=620,
        margin={"l": 190, "r": 130, "t": 92, "b": 126},
        colorbar_title="متوسط الإيجار",
    )
    fig.update_xaxes(title_text="", tickangle=-30, tickfont={"size": 10})
    fig.update_yaxes(title_text="", tickfont={"size": 10})
    render_chart(fig)


def render_riyadh_deals_distribution(market: pd.DataFrame) -> None:
    deals = market.sort_values("total_deals", ascending=False).head(35).copy()
    if deals.empty:
        st.info("لا توجد بيانات كافية لرسم توزيع الصفقات.")
        return

    fig = px.treemap(
        deals,
        path=["property_type", "neighborhood"],
        values="total_deals",
        color="average_rent",
        color_continuous_scale="Teal",
        labels={
            "property_type": "نوع العقار",
            "neighborhood": "الحي",
            "total_deals": "العقود",
            "average_rent": "متوسط الإيجار",
        },
        title="توزيع الصفقات حسب نوع العقار والحي",
    )
    apply_chart_spacing(
        fig,
        height=560,
        margin={"l": 24, "r": 118, "t": 92, "b": 30},
        colorbar_title="متوسط الإيجار",
    )
    fig.update_traces(textinfo="label+value", textfont_size=13)
    render_chart(fig)


def render_riyadh_neighborhood_comparison(market: pd.DataFrame) -> None:
    comparison = aggregate_market(market, ["neighborhood"])
    extras = (
        market.groupby("neighborhood", as_index=False)
        .agg(property_types=("property_type", "nunique"), score=("score", "max"))
    )
    comparison = comparison.merge(extras, on="neighborhood", how="left")
    comparison = comparison.sort_values("score", ascending=False).head(24)
    if comparison.empty:
        st.info("لا توجد بيانات كافية لمقارنة الأحياء.")
        return

    fig = px.scatter(
        comparison,
        x="average_rent",
        y="total_deals",
        size="property_types",
        color="score",
        text="neighborhood",
        color_continuous_scale="Teal",
        labels={
            "average_rent": "متوسط الإيجار",
            "total_deals": "العقود",
            "property_types": "تنوع الأنواع",
            "score": "درجة الفرصة",
            "neighborhood": "الحي",
        },
        title="مقارنة الأحياء: السعر مقابل الطلب",
    )
    apply_chart_spacing(
        fig,
        height=560,
        margin={"l": 112, "r": 132, "t": 92, "b": 106},
        colorbar_title="درجة الفرصة",
    )
    fig.update_traces(textposition="top center", textfont={"size": 10})
    fig.update_xaxes(title_text="متوسط الإيجار (ر.س)", title_standoff=34, tickformat=",.0f")
    fig.update_yaxes(title_text="العقود", title_standoff=42, tickformat=",.0f")
    render_chart(fig)


def render_property_valuation_engine(riyadh: pd.DataFrame) -> None:
    st.subheader("محرك تقييم عقار سريع")
    st.caption("أدخل السعر والمساحة والحي ونوع العقار. المحلل يربط السعر بمؤشرات الإيجار والطلب في الحي، مع بقاء فرق السعر عن متوسط الحي مدخلًا يدويًا إذا كان متاحًا لديك.")

    left, right = st.columns([1.05, 1])
    neighborhoods = riyadh_neighborhood_options(riyadh)
    default_neighborhood = neighborhoods.index("النرجس") if "النرجس" in neighborhoods else 0
    with left:
        st.selectbox("المدينة", ["الرياض"], index=0, disabled=True, key="valuation_city")
        district = st.selectbox(
            "الحي",
            neighborhoods,
            index=default_neighborhood,
            key="valuation_district",
        )
        property_options = neighborhood_property_type_options(riyadh, district)
        default_type = property_options.index("شقة") if "شقة" in property_options else 0
        property_type = st.selectbox(
            "نوع العقار",
            property_options,
            index=default_type,
            key="valuation_property_type",
        )
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

    market = district_market_snapshot(riyadh, district, property_type)
    result = evaluate_property_price(float(price), float(area), float(market_gap_pct), market)
    with right:
        st.metric("السعر لكل م²", f"{result['price_per_sqm']:,.0f} ر.س")
        st.metric("متوسط إيجار الحي", format_sar(market["average_rent"]))
        st.metric("العائد الإيجاري التقريبي", f"{result['gross_yield_pct']:,.2f}%", f"{result['payback_years']:,.1f} سنة")
        st.metric("العقود في آخر فترة", f"{market['total_deals']:,.0f}", market["period"])

        st.metric(
            "فارق السعر عن متوسط الحي",
            format_sar(result["premium_amount"]),
            f"{market_gap_pct:+.1f}%",
        )

        status, message = valuation_message(float(market_gap_pct), result["negotiation_to_fair"], result, market)
        if status == "good":
            st.success(message)
        elif status == "watch":
            st.info(message)
        else:
            st.warning(message)

        st.markdown("**رأي المحلل العقاري**")
        st.write(real_estate_analyst_opinion(district, property_type, result, market))
        st.caption(district_rental_context(riyadh, district, property_type))


def neighborhood_property_type_options(riyadh: pd.DataFrame, district: str) -> list[str]:
    matches = district_rows(riyadh, district)
    if matches.empty:
        values = riyadh["property_type"].dropna().astype(str).str.strip()
    else:
        values = matches["property_type"].dropna().astype(str).str.strip()
    options = sorted({value for value in values if value})
    return options or ["شقة"]


def district_rows(riyadh: pd.DataFrame, district: str) -> pd.DataFrame:
    normalized = normalize_search_text(district)
    if riyadh.empty or not normalized:
        return riyadh.iloc[0:0].copy()

    district_mask = riyadh["location_ar"].map(normalize_search_text).str.contains(
        normalized,
        na=False,
        regex=False,
    )
    if "district_ar" in riyadh.columns:
        district_mask = district_mask | riyadh["district_ar"].map(normalize_search_text).str.contains(
            normalized,
            na=False,
            regex=False,
        )
    return riyadh[district_mask].copy()


def district_market_snapshot(riyadh: pd.DataFrame, district: str, property_type: str) -> dict[str, object]:
    latest_period = riyadh["period_index"].max()
    latest = riyadh[riyadh["period_index"] == latest_period].copy()
    latest["neighborhood"] = latest.apply(neighborhood_label, axis=1)

    rows = district_rows(latest, district)
    typed = rows[rows["property_type"].eq(property_type)].copy()
    if typed.empty:
        typed = rows.copy()

    city_type = latest[latest["property_type"].eq(property_type)].copy()
    city_avg = weighted_average(city_type, "average_rent", "total_deals") if not city_type.empty else float("nan")
    avg_rent = weighted_average(typed, "average_rent", "total_deals") if not typed.empty else float("nan")
    total_deals = float(typed["total_deals"].sum()) if not typed.empty else 0
    rent_gap_pct = pct_delta(avg_rent, city_avg)

    market = riyadh_neighborhood_market(riyadh, 1)
    same_type = market[market["property_type"].eq(property_type)].copy()
    selected = same_type[same_type["neighborhood"].map(normalize_search_text).eq(normalize_search_text(district))]
    score = safe_float(selected["score"].max(), 0) if not selected.empty else 0
    demand_rank = safe_float(selected["demand_rank"].max(), 0) if not selected.empty else 0

    return {
        "average_rent": avg_rent,
        "city_average_rent": city_avg,
        "rent_gap_pct": rent_gap_pct,
        "total_deals": total_deals,
        "period": period_label(latest),
        "score": score,
        "demand_rank": demand_rank,
        "rows": len(typed),
    }


def evaluate_property_price(
    price: float,
    area: float,
    market_gap_pct: float,
    market: dict[str, object],
) -> dict[str, float]:
    area = max(area, 1)
    market_multiplier = 1 + (market_gap_pct / 100)
    estimated_market_price = price / market_multiplier if market_multiplier > 0 else price
    premium_amount = price - estimated_market_price
    acceptable_price = estimated_market_price * 1.03
    annual_rent = safe_float(market.get("average_rent", 0))
    gross_yield_pct = (annual_rent / price * 100) if price > 0 and annual_rent > 0 else 0
    payback_years = (price / annual_rent) if annual_rent > 0 else 0
    return {
        "price_per_sqm": price / area,
        "estimated_market_price": estimated_market_price,
        "estimated_market_price_per_sqm": estimated_market_price / area,
        "premium_amount": premium_amount,
        "negotiation_to_fair": max(premium_amount, 0),
        "negotiation_to_acceptable": max(price - acceptable_price, 0),
        "gross_yield_pct": gross_yield_pct,
        "payback_years": payback_years,
    }


def valuation_message(
    market_gap_pct: float,
    negotiation_to_fair: float,
    result: dict[str, float],
    market: dict[str, object],
) -> tuple[str, str]:
    yield_pct = result["gross_yield_pct"]
    demand_rank = safe_float(market.get("demand_rank", 0))
    if market_gap_pct <= -5:
        return "good", f"السعر أقل من متوسط الحي بنحو {abs(market_gap_pct):.1f}%؛ هذه إشارة سعرية جيدة إذا كانت حالة العقار مناسبة."
    if market_gap_pct <= 5:
        if yield_pct >= 4 or demand_rank >= 0.75:
            return "good", "السعر قريب من متوسط الحي، ومؤشرات الطلب أو العائد تدعم دراسة العقار بجدية."
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


def real_estate_analyst_opinion(
    district: str,
    property_type: str,
    result: dict[str, float],
    market: dict[str, object],
) -> str:
    yield_pct = result["gross_yield_pct"]
    rent_gap = market.get("rent_gap_pct")
    deals = safe_float(market.get("total_deals", 0))
    score = safe_float(market.get("score", 0))

    if yield_pct >= 4.5 and score >= 65:
        action = "النتيجة إيجابية: الحي ونوع العقار يظهران طلبًا جيدًا والعائد الإيجاري مقبول."
    elif yield_pct >= 3.5 and deals >= 50:
        action = "النتيجة متوسطة إلى جيدة: الطلب موجود، لكن القرار يحتاج تفاوضًا أو ميزة في العقار."
    else:
        action = "النتيجة تحتاج حذرًا: السعر الحالي لا يعطي عائدًا قويًا مقارنة بمؤشرات الإيجار."

    rent_text = ""
    if rent_gap is not None:
        rent_text = f" متوسط إيجار {property_type} في {district} يختلف عن متوسط الرياض بنحو {format_pct_text(rent_gap)}."

    return (
        f"{action} العائد التقريبي {yield_pct:,.2f}%، وعدد العقود {deals:,.0f} في آخر فترة."
        f"{rent_text}"
    )


def district_rental_context(riyadh: pd.DataFrame, district: str, property_type: str | None = None) -> str:
    rows = district_rows(riyadh, district)
    if rows.empty:
        return ""

    latest_period = rows["period_index"].max()
    matches = rows[rows["period_index"] == latest_period].copy()
    if property_type:
        typed = matches[matches["property_type"].eq(property_type)].copy()
        if not typed.empty:
            matches = typed
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


def render_data_table(data: pd.DataFrame, nested: bool = False) -> None:
    context = st.container() if nested else st.expander("البيانات الموحدة")
    with context:
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


def pct_series(current: pd.Series, previous: pd.Series) -> pd.Series:
    current_values = pd.to_numeric(current, errors="coerce")
    previous_values = pd.to_numeric(previous, errors="coerce")
    result = (current_values - previous_values) / previous_values * 100
    return result.mask(previous_values.le(0) | previous_values.isna())


def format_pct(value: float | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return f"{value:+.1f}%"


def format_pct_text(value: float | None) -> str:
    formatted = format_pct(value)
    return formatted if formatted is not None else "-"


if __name__ == "__main__":
    main()

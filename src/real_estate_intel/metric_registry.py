from __future__ import annotations

from typing import Final

import pandas as pd


VALID_CLASSIFICATIONS: Final = {"Raw", "Calculated", "Estimated", "Forecast", "Inference"}

METRIC_DEFINITIONS: Final = (
    {
        "metric_id": "published_average_rent",
        "indicator_ar": "متوسط الإيجار المنشور",
        "classification": "Raw",
        "unit": "SAR",
        "grain": "quarter × region × city × district × property type × class",
        "formula": "قيمة average_rent كما نشرها المصدر بعد قواعد استبعاده",
        "source_ar": "الهيئة العامة للعقار - بيانات الإيجار المفتوحة",
        "period_rule": "الفترة الربعية المنشورة",
        "cohort": "صف المصدر نفسه",
        "eligibility": "average_rent > 0",
        "decision_use_ar": "مرساة الإيجار للشريحة نفسها",
        "limitation_ar": "لا يمثل سعر البيع أو سعر المتر ولا يصف عقارًا منفردًا.",
    },
    {
        "metric_id": "weighted_average_rent",
        "indicator_ar": "متوسط الإيجار المجمّع",
        "classification": "Calculated",
        "unit": "SAR",
        "grain": "النطاق والفترة المختاران",
        "formula": "Σ(average_rent × total_deals) / Σ(total_deals)",
        "source_ar": "حساب قارنة من بيانات الإيجار المفتوحة",
        "period_rule": "لا يخلط فترات إلا في العرض التاريخي الصريح",
        "cohort": "الشرائح داخل الفلتر بعد إزالة تداخل المصادر",
        "eligibility": "total_deals > 0 and average_rent is not null",
        "decision_use_ar": "مقارنة مستوى الإيجار على نطاق مركب",
        "limitation_ar": "مرجّح بعدد العقود المنشور، لا بعدد الوحدات الخام غير المتاح محليًا.",
    },
    {
        "metric_id": "rental_deals",
        "indicator_ar": "عدد عقود الإيجار",
        "classification": "Raw",
        "unit": "contracts",
        "grain": "صف المصدر؛ ويجمع بعد إزالة التداخل",
        "formula": "total_deals المنشور؛ Σ عند التجميع",
        "source_ar": "الهيئة العامة للعقار - بيانات الإيجار المفتوحة",
        "period_rule": "الفترة الربعية المنشورة",
        "cohort": "مفتاح الأعمال الفريد",
        "eligibility": "total_deals >= 0",
        "decision_use_ar": "قياس نشاط سوق التأجير، لا سيولة البيع",
        "limitation_ar": "لا يقيس سرعة بيع الأصل أو عدد الوحدات الفريدة.",
    },
    {
        "metric_id": "quarterly_rent_growth",
        "indicator_ar": "نمو الإيجار الربعي",
        "classification": "Calculated",
        "unit": "%",
        "grain": "نفس المنطقة والمدينة والموقع ونوع العقار",
        "formula": "(rent_t / rent_t-1 - 1) × 100",
        "source_ar": "حساب قارنة من بيانات الإيجار المفتوحة",
        "period_rule": "ربعان متتاليان فقط؛ period_gap = 1",
        "cohort": "نفس مفتاح الكيان في الفترتين",
        "eligibility": "عقود كل فترة >= min_deals ومتوسط الفترة السابقة > 0",
        "decision_use_ar": "وصف الحركة المرصودة بين ربعين",
        "limitation_ar": "ليس نموًا سنويًا رسميًا ولا دليلًا على استمرار الاتجاه.",
    },
    {
        "metric_id": "opportunity_score",
        "indicator_ar": "Opportunity Score / درجة الفرصة",
        "classification": "Inference",
        "unit": "0-100 relative score",
        "grain": "كيان × أحدث ربع مؤهل",
        "formula": "40% سيولة + 35% نمو + 25% جاذبية سعر",
        "source_ar": "استدلال قارنة مشتق من مؤشرات REGA",
        "period_rule": "أحدث ربع يملك مقارنة متصلة ومؤهلة",
        "cohort": "نفس نوع العقار ونفس المستوى الجغرافي",
        "eligibility": "عقود الربع الحالي والسابق >= min_deals",
        "decision_use_ar": "ترتيب أولي للبحث، لا توصية شراء",
        "limitation_ar": "درجة نسبية تتغير مع مجموعة المقارنة ولا تمثل احتمال نجاح.",
    },
    {
        "metric_id": "property_score",
        "indicator_ar": "Property Score / درجة العقار",
        "classification": "Inference",
        "unit": "0-100 relative score",
        "grain": "حي الرياض × نوع العقار × أحدث ربع مؤهل",
        "formula": "35% نمو + 30% طلب + 20% جاذبية سعر + 15% استقرار مرصود",
        "source_ar": "استدلال قارنة مشتق من مؤشرات REGA",
        "period_rule": "أحدث ربع يملك مقارنة متصلة ومؤهلة",
        "cohort": "نفس نوع العقار داخل الرياض",
        "eligibility": "عقود الربع الحالي والسابق >= min_deals",
        "decision_use_ar": "ترتيب شرائح الرياض لبدء الدراسة",
        "limitation_ar": "ليس تقييمًا رسميًا ولا ثقة احتمالية ولا بديلًا عن فحص الأصل.",
    },
    {
        "metric_id": "purchase_price_estimate",
        "indicator_ar": "تقدير سعر الشراء",
        "classification": "Estimated",
        "unit": "SAR",
        "grain": "العقار المدخل × مقارنة الحي والنوع المتاحة",
        "formula": "المساحة × متوسط سعر المتر المتطابق، ثم اختبارات دخل وتمويل",
        "source_ar": "مؤشرات البيع الرسمية المتاحة + افتراضات المستخدم",
        "period_rule": "أحدث فترة بيع متاحة مع الإفصاح عن تاريخها",
        "cohort": "نفس الحي والنوع عند التوفر",
        "eligibility": "مقارنة بيع موجبة ومتطابقة أو إفصاح صريح عن البديل",
        "decision_use_ar": "نطاق تفاوض أولي",
        "limitation_ar": "ليس تثمينًا معتمدًا ويتأثر بحالة العقار والتمويل.",
    },
    {
        "metric_id": "market_forecast",
        "indicator_ar": "توقع الإيجار والطلب",
        "classification": "Forecast",
        "unit": "SAR and contracts",
        "grain": "النطاق المختار × ربع مستقبلي × سيناريو",
        "formula": "اتجاه ربعي مخفّض الأثر مع نطاق من تذبذب التاريخ",
        "source_ar": "نموذج قارنة حتمي على التاريخ المرصود",
        "period_rule": "حتى 12 ربعًا تاريخيًا و4 أرباع مستقبلية افتراضيًا",
        "cohort": "النطاق المفلتر نفسه",
        "eligibility": "4 أرباع مكتملة على الأقل",
        "decision_use_ar": "اختبار سيناريو، لا نقطة توقع مؤكدة",
        "limitation_ar": (
            "اختبار رجعي من 8 طيات: خطأ الإيجار ≈ 18.989% وخطأ الطلب ≈ 45.383%؛ "
            "سيناريو ثانوي عالي الخطأ، وليس ادعاء ثقة مرتفعة."
        ),
    },
    {
        "metric_id": "data_sufficiency",
        "indicator_ar": "كفاية البيانات",
        "classification": "Inference",
        "unit": "ordinal label",
        "grain": "النطاق المختار",
        "formula": "قواعد معلنة على حجم العقود والتغطية الجغرافية وتنوع الأنواع",
        "source_ar": "فحص حوكمة قارنة",
        "period_rule": "أحدث فترة ضمن النطاق",
        "cohort": "الفلتر الحالي",
        "eligibility": "لا يوجد",
        "decision_use_ar": "تحديد ما إذا كانت العينة تسمح بالمقارنة",
        "limitation_ar": "ليست ثقة إحصائية ولا احتمال صحة أو دقة تنبؤية.",
    },
)


def metric_governance_frame() -> pd.DataFrame:
    frame = pd.DataFrame(METRIC_DEFINITIONS)
    invalid = set(frame["classification"]) - VALID_CLASSIFICATIONS
    if invalid:
        raise ValueError(f"Invalid metric classifications: {sorted(invalid)}")
    if frame["metric_id"].duplicated().any():
        raise ValueError("Metric IDs must be unique.")
    return frame


def investor_metric_lineage_frame() -> pd.DataFrame:
    frame = metric_governance_frame()
    selected = frame[
        frame["metric_id"].isin(
            {
                "weighted_average_rent",
                "rental_deals",
                "quarterly_rent_growth",
                "opportunity_score",
                "property_score",
                "purchase_price_estimate",
                "market_forecast",
                "data_sufficiency",
            }
        )
    ].copy()
    selected["classification_ar"] = selected["classification"].map(
        {
            "Raw": "منشور",
            "Calculated": "محسوب",
            "Estimated": "تقديري",
            "Forecast": "توقع سيناريو مختبر رجعيًا",
            "Inference": "استدلالي",
        }
    )
    selected["method_ar"] = selected["formula"] + " | " + selected["period_rule"]
    return selected[
        [
            "indicator_ar",
            "source_ar",
            "classification_ar",
            "method_ar",
            "decision_use_ar",
            "limitation_ar",
        ]
    ].reset_index(drop=True)

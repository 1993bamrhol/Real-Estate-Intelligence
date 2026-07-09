from __future__ import annotations

import pandas as pd


OFFICIAL_REGA_OPEN_DATA_URL = "https://rega.gov.sa/البيانات-المفتوحة/"
OFFICIAL_OPEN_DATA_URL = "https://open.data.gov.sa/ar/home"
OFFICIAL_GASTAT_URL = "https://www.stats.gov.sa/en"
OFFICIAL_DATASAUDI_URL = "https://datasaudi.sa/en"
OFFICIAL_RIYADH_OPEN_DATA_URL = "https://www.alriyadh.gov.sa/en/open-data"
OFFICIAL_RER_URL = "https://rer.sa/"


def official_sources_frame() -> pd.DataFrame:
    """Return the official-source registry used to qualify every insight."""
    rows = [
        {
            "source_id": "rega_rental_open_data",
            "name_ar": "الهيئة العامة للعقار - بيانات الإيجار المفتوحة",
            "owner_ar": "الهيئة العامة للعقار",
            "url": OFFICIAL_REGA_OPEN_DATA_URL,
            "access_ar": "مجاني / بيانات مفتوحة",
            "status_ar": "نشط داخل المنتج",
            "coverage_ar": "مؤشرات الإيجار حسب المنطقة والمدينة والحي ونوع العقار والفترة",
            "used_for_ar": "متوسط الإيجار، عدد العقود، النمو، السيولة، مؤشرات الفرص",
            "trust_score": 95,
            "active": True,
        },
        {
            "source_id": "national_open_data_platform",
            "name_ar": "منصة البيانات المفتوحة الوطنية",
            "owner_ar": "سدايا والجهات الحكومية الناشرة",
            "url": OFFICIAL_OPEN_DATA_URL,
            "access_ar": "مجاني / بيانات مفتوحة",
            "status_ar": "مصدر رسمي مساند",
            "coverage_ar": "كتالوج وملفات حكومية متعددة بصيغ قابلة لإعادة الاستخدام",
            "used_for_ar": "تحديث الكتالوج والتحقق من مصدر ملفات REGA وغيرها",
            "trust_score": 90,
            "active": True,
        },
        {
            "source_id": "gastat",
            "name_ar": "الهيئة العامة للإحصاء",
            "owner_ar": "الهيئة العامة للإحصاء",
            "url": OFFICIAL_GASTAT_URL,
            "access_ar": "مجاني غالبا / جداول ومنشورات وطلبات بيانات",
            "status_ar": "جاهز للدمج في V2",
            "coverage_ar": "السكان، الإسكان، الأسعار، العمل، المؤشرات المكانية",
            "used_for_ar": "قياس الطلب السكاني، الدخل، التركز السكني، ومقارنة المدن",
            "trust_score": 92,
            "active": False,
        },
        {
            "source_id": "datasaudi",
            "name_ar": "DataSaudi",
            "owner_ar": "وزارة الاقتصاد والتخطيط وشركاء البيانات",
            "url": OFFICIAL_DATASAUDI_URL,
            "access_ar": "مجاني / مؤشرات رسمية",
            "status_ar": "جاهز للدمج في V2",
            "coverage_ar": "مؤشرات اقتصادية وقطاعية ومقارنات زمنية",
            "used_for_ar": "ربط العقار بالاقتصاد والتمويل والنمو العام",
            "trust_score": 88,
            "active": False,
        },
        {
            "source_id": "riyadh_municipality",
            "name_ar": "أمانة منطقة الرياض - البيانات المفتوحة والبوابة الجغرافية",
            "owner_ar": "أمانة منطقة الرياض",
            "url": OFFICIAL_RIYADH_OPEN_DATA_URL,
            "access_ar": "مجاني / بيانات وطلبات بيانات",
            "status_ar": "جاهز للدمج في الخرائط",
            "coverage_ar": "بيانات بلدية، خرائط، مواقع وخدمات حضرية بحسب التوفر",
            "used_for_ar": "حدود الأحياء، الخدمات، جودة الموقع، الخرائط الحرارية الدقيقة",
            "trust_score": 88,
            "active": False,
        },
        {
            "source_id": "rer",
            "name_ar": "السجل العقاري",
            "owner_ar": "السجل العقاري",
            "url": OFFICIAL_RER_URL,
            "access_ar": "خدمات رسمية / قد يتطلب صلاحيات أو طلب بيانات",
            "status_ar": "مصدر مطلوب للتقييم النهائي",
            "coverage_ar": "التسجيل العيني، وثائق الملكية، خدمات العقار وقوائمه بحسب الإتاحة",
            "used_for_ar": "التحقق من الملكية والصفقات والبيانات العقارية التفصيلية عند توفرها",
            "trust_score": 96,
            "active": False,
        },
    ]
    return pd.DataFrame(rows)


def metric_lineage_frame() -> pd.DataFrame:
    """Describe what each investor-facing metric can and cannot prove."""
    rows = [
        {
            "indicator_ar": "متوسط الإيجار",
            "source_ar": "REGA - بيانات الإيجار المفتوحة",
            "confidence_ar": "عال",
            "method_ar": "متوسط مرجح بعدد العقود داخل الفترة والحي ونوع العقار",
            "decision_use_ar": "تقدير قوة الدخل الإيجاري ومقارنة الأحياء",
            "limitation_ar": "لا يمثل سعر البيع أو سعر المتر مباشرة",
        },
        {
            "indicator_ar": "السيولة / عدد العقود",
            "source_ar": "REGA - بيانات الإيجار المفتوحة",
            "confidence_ar": "عال",
            "method_ar": "إجمالي العقود المنشورة في الشريحة المختارة",
            "decision_use_ar": "قياس نشاط السوق وسهولة التأجير",
            "limitation_ar": "لا يقيس سرعة بيع الأصل ولا عمق سوق التملك",
        },
        {
            "indicator_ar": "نمو الإيجار",
            "source_ar": "REGA - بيانات الإيجار المفتوحة",
            "confidence_ar": "متوسط إلى عال",
            "method_ar": "مقارنة متوسط الإيجار لنفس الحي ونوع العقار عبر الفترات",
            "decision_use_ar": "كشف الأحياء التي تتحرك إيجاريا",
            "limitation_ar": "يتأثر بتغير مزيج العقارات إذا كان عدد العقود منخفضا",
        },
        {
            "indicator_ar": "Property Score",
            "source_ar": "مؤشر مشتق من REGA",
            "confidence_ar": "متوسط",
            "method_ar": "دمج النمو والسيولة وجاذبية السعر واستقرار الإشارة",
            "decision_use_ar": "فرز أولي للفرص وترتيب المتابعة",
            "limitation_ar": "ليس تقييما رسميا ولا بديلا عن بيانات البيع وحالة العقار",
        },
        {
            "indicator_ar": "الخريطة الحرارية",
            "source_ar": "مؤشر مشتق من REGA",
            "confidence_ar": "متوسط",
            "method_ar": "توزيع الأحياء حسب متوسط الإيجار وعدد العقود",
            "decision_use_ar": "رؤية مناطق النشاط والفروق بين الأحياء",
            "limitation_ar": "الدقة الجغرافية النهائية تحتاج حدود أحياء وإحداثيات رسمية",
        },
        {
            "indicator_ar": "تقييم سعر شراء محدد",
            "source_ar": "يتطلب صفقات بيع رسمية وبيانات مساحة",
            "confidence_ar": "غير مفعل حاليا",
            "method_ar": "يجب مقارنته بسعر متر وصفقات بيع مماثلة عند توفرها",
            "decision_use_ar": "قبول أو رفض سعر صفقة بعينها",
            "limitation_ar": "لا ينبغي بيعه كتقييم نهائي قبل دمج بيانات البيع",
        },
    ]
    return pd.DataFrame(rows)


def official_source_summary(data: pd.DataFrame) -> dict[str, object]:
    if data.empty:
        return {
            "readiness_label": "غير جاهز",
            "readiness_score": 0,
            "active_sources": 0,
            "rows": 0,
            "datasets": 0,
            "locations": 0,
            "latest_period": "-",
            "official_rows_pct": 0.0,
        }

    dataset_series = data.get("dataset_id", pd.Series([], dtype="object")).fillna("").astype(str).str.strip()
    official_rows_pct = float((dataset_series != "").mean() * 100) if len(dataset_series) else 100.0
    datasets = int(dataset_series[dataset_series != ""].nunique()) if len(dataset_series) else 1
    locations = int(data["location_ar"].nunique()) if "location_ar" in data else 0
    rows = int(len(data))
    latest_period = "-"
    if {"period_index", "period"}.issubset(data.columns) and not data["period_index"].dropna().empty:
        latest_period_index = data["period_index"].max()
        latest = data[data["period_index"].eq(latest_period_index)]
        if not latest.empty:
            latest_period = str(latest["period"].iloc[0])

    readiness_score = _readiness_score(rows, datasets, locations, official_rows_pct)
    readiness_label = _readiness_label(readiness_score)
    return {
        "readiness_label": readiness_label,
        "readiness_score": readiness_score,
        "active_sources": 2,
        "rows": rows,
        "datasets": datasets,
        "locations": locations,
        "latest_period": latest_period,
        "official_rows_pct": official_rows_pct,
    }


def official_limitations() -> list[str]:
    return [
        "المؤشرات الحالية دقيقة لتحليل الإيجارات والعقود، لكنها ليست تقييما نهائيا لسعر البيع.",
        "تقييم صفقة شراء يحتاج بيانات بيع رسمية، مساحة، سعر متر، عمر العقار، حالة العقار، وموقعه الدقيق.",
        "الخريطة الحالية تقارن الأحياء من بيانات الإيجار؛ الدقة الجغرافية الأعلى تحتاج حدود أحياء رسمية قابلة للتحميل.",
        "أي تقرير تجاري يجب أن يذكر المصدر والفترة ونطاق الثقة حتى لا يخلط بين الإشارة الاستثمارية والتقييم الرسمي.",
    ]


def _readiness_score(rows: int, datasets: int, locations: int, official_rows_pct: float) -> int:
    row_score = min(rows / 45000, 1) * 35
    dataset_score = min(datasets / 50, 1) * 25
    location_score = min(locations / 8000, 1) * 25
    official_score = min(official_rows_pct / 100, 1) * 15
    return int(round(row_score + dataset_score + location_score + official_score))


def _readiness_label(score: int) -> str:
    if score >= 85:
        return "جاهز لتحليلات الإيجار الرسمية"
    if score >= 65:
        return "قوي كبداية رسمية"
    if score >= 40:
        return "قابل للاستخدام مع تحفظات"
    return "يحتاج بيانات إضافية"

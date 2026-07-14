from __future__ import annotations

from dataclasses import dataclass


BRAND_NAME_AR = "قرينة"
BRAND_NAME_EN = "QAREENA"
BRAND_TAGLINE = "الدليل قبل القرار العقاري"
BRAND_PROMISE = "من بيانات السوق إلى قرار تدعمه قرائن واضحة وقابلة للمشاركة."
BRAND_DISCLAIMER = "هوية عمل أولية؛ اعتماد الاسم التجاري النهائي يتطلب فحص العلامة التجارية رسميًا."


@dataclass(frozen=True)
class PricingPlan:
    name: str
    price: str
    audience: str
    features: tuple[str, ...]
    call_to_action: str


@dataclass(frozen=True)
class UseCase:
    title: str
    audience: str
    question: str
    outcome: str


PRICING_PLANS: tuple[PricingPlan, ...] = (
    PricingPlan(
        name="استكشاف",
        price="مجاني",
        audience="للباحث والمستثمر في مرحلة الاستكشاف",
        features=("ملخصات السوق", "الفلاتر الأساسية", "جودة ومصادر البيانات"),
        call_to_action="ابدأ الاستكشاف",
    ),
    PricingPlan(
        name="محترف",
        price="149 ر.س / شهر — مقترح",
        audience="للمستثمر والوسيط المحترف",
        features=("تقييم العقار", "توقعات وسيناريوهات", "تقارير PDF", "مقارنة البدائل"),
        call_to_action="سجّل اهتمامك",
    ),
    PricingPlan(
        name="فرق",
        price="حسب الاستخدام",
        audience="للمطورين والفرق العقارية",
        features=("حسابات متعددة", "تصدير موسع", "تكاملات بيانات", "دعم مخصص"),
        call_to_action="اطلب عرضًا",
    ),
)


USE_CASES: tuple[UseCase, ...] = (
    UseCase(
        title="فحص صفقة سكنية",
        audience="مستثمر",
        question="هل السعر المطلوب يحقق عائدًا مناسبًا بعد المصاريف والتمويل؟",
        outcome="تقدير السعر العادل، التدفق النقدي، اختبار الضغط، وبدائل أحياء قابلة للمقارنة.",
    ),
    UseCase(
        title="إعداد عرض لعميل",
        audience="وسيط",
        question="كيف أشرح للعميل سبب ترشيح هذا الحي بدل ثلاثة بدائل؟",
        outcome="مقارنة موحدة للطلب والعائد والمخاطر مع تقرير قابل للمشاركة.",
    ),
    UseCase(
        title="اختيار نطاق تطوير",
        audience="مطور عقاري",
        question="أين يتجمع الطلب، وما نوع العقار الأكثر نشاطًا؟",
        outcome="خريطة طلب واتجاهات دورية ومزيج عقاري مع إظهار حدود التغطية والثقة.",
    ),
)

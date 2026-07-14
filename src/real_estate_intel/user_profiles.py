from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfile:
    key: str
    label: str
    description: str
    primary_question: str
    next_action: str
    focus_metrics: tuple[str, ...]
    tab_labels: tuple[str, str, str, str]


USER_PROFILES: dict[str, UserProfile] = {
    "investor": UserProfile(
        key="investor",
        label="مستثمر",
        description="قرار شراء مبني على العائد والمخاطر والسعر العادل.",
        primary_question="هل أشتري هذا العقار، وبأي سعر؟",
        next_action="ابدأ بمحرك تقييم العقار ثم قارن الحي بالبدائل.",
        focus_metrics=("العائد", "التدفق النقدي", "المخاطر", "السعر العادل"),
        tab_labels=("قرار الاستثمار", "تحليل الفرص", "السوق والبدائل", "مصادر البيانات"),
    ),
    "broker": UserProfile(
        key="broker",
        label="وسيط",
        description="اختيار الفرص المناسبة للعميل وإثباتها بمقارنات واضحة.",
        primary_question="ما الفرصة الأنسب لاحتياج العميل؟",
        next_action="ابدأ بقائمة الفرص ثم استخدم مقارنة الأحياء في العرض للعميل.",
        focus_metrics=("السيولة", "حجم الطلب", "فجوة السعر", "البدائل"),
        tab_labels=("فرص العملاء", "تحليل وتسويق", "السوق والمقارنات", "موثوقية البيانات"),
    ),
    "developer": UserProfile(
        key="developer",
        label="مطور عقاري",
        description="قراءة الطلب والنمو والمزيج العقاري قبل اختيار موقع المشروع.",
        primary_question="أين يوجد طلب قابل للتطوير والنمو؟",
        next_action="ابدأ بخريطة الطلب ثم راجع نمو الأحياء ومزيج أنواع العقار.",
        focus_metrics=("نمو الطلب", "حجم السوق", "المزيج العقاري", "اتجاه الإيجار"),
        tab_labels=("قرار التطوير", "تحليل الجدوى السوقية", "الطلب والخرائط", "تغطية البيانات"),
    ),
    "researcher": UserProfile(
        key="researcher",
        label="باحث",
        description="تحليل الاتجاهات مع وضوح التغطية والمنهجية وجودة المصدر.",
        primary_question="ما الاتجاه الذي تدعمه البيانات، وما حدود الثقة؟",
        next_action="ابدأ بالاتجاهات ثم راجع التغطية والمصادر قبل الاستنتاج.",
        focus_metrics=("الاتجاه الزمني", "التغطية", "جودة البيانات", "المصادر"),
        tab_labels=("ملخص البحث", "التحليل المتقدم", "الاتجاهات والخرائط", "البيانات والمنهجية"),
    ),
}


DEFAULT_USER_PROFILE = "investor"


def get_user_profile(key: str | None) -> UserProfile:
    return USER_PROFILES.get(str(key or ""), USER_PROFILES[DEFAULT_USER_PROFILE])


def user_profile_labels() -> list[str]:
    return [profile.label for profile in USER_PROFILES.values()]


def user_profile_key_from_label(label: str) -> str:
    for key, profile in USER_PROFILES.items():
        if profile.label == label:
            return key
    return DEFAULT_USER_PROFILE

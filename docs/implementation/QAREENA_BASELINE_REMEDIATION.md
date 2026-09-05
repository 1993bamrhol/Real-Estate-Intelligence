# Qareena — Baseline Remediation قبل Batch 0

التاريخ: 2026-09-06  
النطاق: إغلاق موانع Baseline الثلاثة فقط  
القرار النهائي: **BASELINE READY TO FREEZE**

## Executive Summary

أُغلقت الموانع الثلاثة المحددة دون تغيير UI أو CSS أو Figma ودون بدء Batch 0:

1. أُعيد بناء `data/warehouse/real_estate.sqlite` من المصدر المحكوم `data/processed/rental_market.csv.gz` عبر pipeline المشروع الحالي. أصبحت SQLite مطابقة دلاليًا للـCSV: **44,455 صفًا، 0 duplicate groups، وآخر فترة 2026 Q1**، مع `PRAGMA integrity_check = ok`.
2. صُحح وصف Forecast في Metric Registry من وصف ينفي وجود الاختبار الرجعي إلى وصف سيناريو مختبر رجعيًا. وثقت القيود الحالية صراحةً: **8 folds، Rent MAPE ≈ 18.989%، Demand MAPE ≈ 45.383%، سيناريو ثانوي عالي الخطأ، ولا يوجد ادعاء High Confidence**. لم تتغير خوارزمية Forecast أو حساباتها.
3. أصبح `build_market_signals()` يعيد استخدام قاعدة الاستمرارية المعتمدة في `entity_period_market()`، ولا ينتج نمو إيجار أو عقود عند وجود فجوة بين الفترات أو غياب الفترة السابقة.

## 1. SQLite Synchronization

### مصدر الحقيقة والمسار

- Source of Truth: `data/processed/rental_market.csv.gz`
- Pipeline المستخدم: `scripts/build_data_engine.py` → `load_rental_data()` → `build_sqlite_warehouse()`
- لم يُنشأ مسار بيانات جديد، ولم تتغير fallback precedence؛ ما زال runtime يفضل SQLite محليًا ثم CSV.
- أضيفت حماية إزالة التكرار داخل `prepare_clean_market()` باستخدام `deduplicate_rental_observations()` الحالية نفسها، بحيث يبقى بناء SQLite وPostgreSQL آمنًا حتى إذا وصل source متداخل.

### Before → After

| الفحص | Before | After |
|---|---:|---:|
| SQLite rows | 45,198 | 44,455 |
| Duplicate business-key groups | 743 | 0 |
| Latest period | 2026 Q1 | 2026 Q1 |
| `PRAGMA integrity_check` | ok | ok |

### Semantic parity

تمت مقارنة النسخة المحملة من CSV مع جدول `rental_market_clean` في SQLite، وكذلك نتيجة `load_market_data()` عند إجبار المسار المحلي:

- business-key sets: متطابقة.
- row count: متطابق، 44,455.
- duplicate groups: صفر في المصدرين.
- latest period: متطابقة، 2026 Q1.
- مجموع العقود: متطابق.
- مجموع `average_rent × total_deals` المستخدم في دلالة المتوسط الموزون: متطابق ضمن دقة الاختبار.
- أعمدة runtime الأساسية موجودة ومتوافقة: الفترة، الجغرافيا، نوع/تصنيف العقار، العقود، ومتوسط الإيجار.

النتيجة: **CSV ↔ SQLite semantic parity = PASS**.

## 2. Forecast Description

### Before

كان وصف التصنيف العربي في lineage:

> توقع غير مختبر رجعيًا

وهذا يتعارض مع التنفيذ الفعلي ونتيجة KPI Audit.

### After

أصبح وصف التصنيف:

> توقع سيناريو مختبر رجعيًا

وأصبحت limitation المسجلة:

> اختبار رجعي من 8 طيات: خطأ الإيجار ≈ 18.989% وخطأ الطلب ≈ 45.383%؛ سيناريو ثانوي عالي الخطأ، وليس ادعاء ثقة مرتفعة.

بقي التصنيف `Forecast`، وبقي `decision_use_ar` يحصره في اختبار سيناريو لا نقطة توقع مؤكدة. لم تُعدّل `forecast_market()` أو rolling backtest أو أي قيمة محسوبة. أُعيد بناء SQLite بعد التعديل، وتحتوي `metric_lineage` على الوصف الجديد.

النتيجة: **Forecast governance description = PASS**.

## 3. Market Signals Continuity

كان `build_market_signals()` يستخدم `shift(1)` مباشرة، ولذلك كان يمكنه معاملة آخر سجل قديم على أنه الربع السابق حتى عند وجود فجوة زمنية.

أصبح المسار يستدعي `entity_period_market()`، وهي قاعدة الاستمرارية المعتمدة التي تحسب `previous_period_index` و`period_gap` وتسمح بالنمو فقط عندما `period_gap == 1`. ثم تطبق القاعدة نفسها على `deals_growth_pct`.

نتائج التحقق على المستودع المعاد بناؤه:

- non-consecutive growth comparisons: **0**.
- missing prior period exposed as growth: **0**.
- missing prior period لا يتحول إلى 0 growth.
- لا يوجد silent fallback إلى stale prior period.
- KPI Audit: `growth_candidates_rejected_for_period_gap = 8,611` و`max_growth_period_gap = 1` بين المقارنات المقبولة.

لم يُحذف المسار؛ ما زال يُنتج `rental_market_signals`، لكنه أصبح آمنًا ومتسقًا مع analytics canonical path.

النتيجة: **Market signals continuity = PASS**.

## 4. Tests Added or Updated

أضيفت أقل تغطية لازمة داخل `tests/test_metric_governance.py`:

- رفض نمو market signals للفترات غير المتتالية، للإيجار والعقود.
- حماية SQLite builder من duplicate business keys مع اختيار المصدر الأحدث.
- semantic parity بين CSV المنشور وSQLite.
- صحة وصف وتصنيف Forecast وحدود backtesting الحالية.
- إغلاق اتصالات SQLite صراحةً بعد البناء/القراءة لتجنب file locking على Windows.

نتيجة full suite:

> **77 passed, 5 subtests passed**

## 5. Validation Evidence

### KPI Audit

النتيجة: **PASS**

- rental rows: 44,455.
- business-key duplicate groups: 0.
- latest period: 2026 Q1.
- nonconsecutive growth comparisons: 0.
- opportunity missing previous period: 0.
- forecast validation: `backtested_high_error`.
- folds: 8.
- rent MAPE: 18.989%.
- demand MAPE: 45.383%.
- جميع 9 metrics لها classification وperiod rule وcohort وeligibility محكومة.

ملاحظة تشغيلية: ظهرت تحذيرات Streamlit الخاصة بالتشغيل في bare mode فقط؛ لا تؤثر في نتيجة التدقيق.

### Release Validator

النتيجة: **PASS** (`release_validation=ok`)

- rows: 44,455.
- regions: 13.
- locations: 8,132.
- latest rental period: 2026 Q1.
- sale rows: 44.
- latest sale period: 2026 Q2.

استخدم validator fallback المحلي بنجاح لأن اتصال PostgreSQL غير متاح من بيئة التنفيذ. ظهرت تحذيرات Streamlit deprecated لـ`use_container_width`؛ لم تُعالج لأنها خارج نطاق هذه المهمة ولا تمنع الـBaseline.

### Opportunity spot checks

على cohort الرياض / استديو / 2026 Q1:

| الحي | Opportunity Score | Growth context |
|---|---:|---|
| ثليم | 84.5 | 2025 Q4 → 2026 Q1، +5.893686% QoQ |
| المرقب | 83.7 | 2025 Q4 → 2026 Q1، +4.187068% QoQ |

النتيجة: **PASS**.

### QoQ semantics

تم التحقق من أن +5.9% لثليم ناتج عن مقارنة `2026 Q1` مع `2025 Q4`، بفجوة `period_gap = 1` وتصنيف `Calculated QoQ`. لا يوجد استخدام لفترة قديمة غير متتالية.

النتيجة: **PASS**.

## 6. Files Changed in This Remediation

- `data/warehouse/real_estate.sqlite` — إعادة بناء من CSV المحكومة.
- `src/real_estate_intel/data_engine.py` — حماية dedup، إعادة استخدام continuity canonical rule، وإغلاق SQLite engine بعد البناء.
- `src/real_estate_intel/metric_registry.py` — تصحيح وصف Forecast وتوثيق backtesting/high-error limitation.
- `tests/test_metric_governance.py` — اختبارات parity، duplicate protection، continuity، وForecast governance.
- `docs/implementation/QAREENA_BASELINE_REMEDIATION.md` — هذا التقرير.

لم تُعدّل في هذه المهمة أي ملفات UI أو CSS أو Figma أو `docs/ux`، ولم يحدث commit أو push.

## 7. Residual Notes and Decision

لا يوجد blocker جديد ضمن نطاق Baseline Remediation. عدم توفر PostgreSQL من بيئة التحقق لا يمنع النتيجة لأن المطلوب كان مزامنة واختبار fallback SQLite، وقد اجتاز release validator والمسار المحلي. تحذيرات Streamlit deprecated معلومة وخارج النطاق.

**Baseline decision: BASELINE READY TO FREEZE**

توقفت المهمة هنا. لم يبدأ Batch 0.

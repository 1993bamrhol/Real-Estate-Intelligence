# Qareena — Implementation Readiness & Migration Plan

**التاريخ:** 2026-09-05  
**النطاق:** تخطيط Read-Only للانتقال من تطبيق Streamlit الحالي إلى Core High-Fi المجمد  
**القرار:** **READY WITH PRECONDITIONS**

## 1. الجواب التنفيذي

لا يحتاج Qareena إلى إعادة بناء من الصفر. طبقات البيانات والتحليلات والاكتتاب والتقارير الحالية توفر معظم السلوك المطلوب، بينما الفجوة الأساسية هي طبقة العرض والتنقل وعقود السياق بين الصفحات. المسار الأقل مخاطرة هو إبقاء `app.py` كنقطة دخول واحدة، نقل العرض تدريجيًا إلى وحدات صفحات صغيرة، واستخدام route واحد في `st.session_state` بدل التبويبات السبعة التي تنفذ محتواها معًا.

التقدير الوظيفي القابل لإعادة الاستخدام هو **72%**: الحسابات، الوصول إلى البيانات، قواعد الأهلية، البيع المطابق، الاكتتاب، التوقع والتقارير قابلة لإعادة الاستخدام. الباقي Presentation/State/CSS أو إعادة تركيب قدرات موجودة. النسبة تقدير مرجح بحسب قدرات الرحلات الأربع، وليست نسبة أسطر كود.

الشرط الوحيد قبل أول تعديل Production هو إنشاء baseline Git نظيف ومراجع؛ الحالة الحالية على `main` تحتوي تغييرات مترابطة وملفات حوكمة غير متتبعة، و`official_sources.py` يعتمد فعليًا على `metric_registry.py` غير المتتبع. بعد ذلك يبدأ التنفيذ بـBatch 0 لحماية العقود والقيم قبل لمس الواجهة.

## 2. حدود ومصادر التدقيق

اعتمد التدقيق على:

- التطبيق الفعلي: `app.py` ووحدات `src/real_estate_intel/`.
- البيانات الحالية: rental snapshot بعدد 45,198 صفًا وsale snapshot بعدد 44 صفًا.
- Metric Registry وقواعد Data Prep وAnalytics والاختبارات الحالية.
- وثائق IA وCore High-Fi Gate وP1 remediation والعقود المجمدة في Figma.
- إعدادات Streamlit وPython والتبعيات وGitHub Actions وحالة Git المحلية.

لم تُعامل قيم Figma كمصدر حساب. لم تُعدّل Figma أو CSS أو كود أو بيانات، ولم يُنشأ commit أو branch أو stash.

## 3. Current Application Audit

### 3.1 البنية الحالية

| الطبقة | التنفيذ الحالي | الحكم |
|---|---|---|
| Entry point | `app.py` ثم `main()` | يبقى entry point؛ يخف دوره إلى bootstrap/router تدريجيًا |
| Navigation | سبعة `st.tabs` داخل `main()`، تتغير أول ثلاثة منها حسب الدور | يحتاج REFACTOR إلى ست وجهات IA ثابتة |
| UI | أكثر من 5,300 سطر في `app.py` مع CSS وHTML وrenderers وحسابات page-level | أكبر منطقة مخاطرة؛ تفكيك تدريجي لا rewrite شامل |
| Analytics | `analytics.py`, `decision_support.py`, `underwriting.py`, `forecasting.py` | REUSE مع adapters/view-models رقيقة |
| Data access | `data_engine.py`: PostgreSQL عند `DATABASE_URL` ثم SQLite ثم CSV | REUSE؛ fallback جيد ومختبر |
| Data preparation | `data_prep.py`: normalize، business-key dedup، source precedence، period index | REUSE؛ لا تغيير في migration المرئي |
| Metric Registry | `metric_registry.py` وخط lineage عبر `official_sources.py` | REUSE؛ يجب إدخاله baseline لأنه غير متتبع حاليًا |
| Sales | `sales.py` و`latest_sale_comparable()` | REUSE؛ exact match أو missing state فقط |
| State | مفاتيح widgets متفرقة للمصادقة والمطور والخريطة والتقييم والتقارير | يحتاج namespace وعقد سياق محدود للـCore |
| Filters | `render_filters()` في sidebar ويؤثر على جميع التبويبات | REFACTOR؛ Market scope داخل Market، Deal inputs داخل Deal |
| Caching | `st.cache_data` للإيجار والبيع، `st.cache_resource` للمخزن/عارض الخريطة | الأساس جيد؛ ينقص cache للـview-models الثقيلة حسب scope |
| Charts | Plotly Express/Graph Objects/Subplots عبر `render_chart()` | REUSE؛ يحتاج contract للحالات والفترات المفقودة |
| Map | Folium + `streamlit_folium` مع جدول إحداثيات وجيل عشوائي fallback | غير صالح للإنتاج؛ BLOCKED BY DATA |
| Reports | HTML/PDF memo في `reporting.py` وneighborhood PDF مستقل | REUSE/MOVE إلى وجهة التقارير |
| CSS/theme | theme خفيف في `.streamlit/config.toml` وCSS global داخل `app.py` | استبدال تدريجي بتوكنز semantic وselectors محدودة |
| Tests | 14 ملفًا؛ 73 test + 5 subtests ناجحة في الفحص الحالي | baseline جيد للتحليلات؛ تغطية UI/state ناقصة |
| CI | workflow شهري لتحديث البيانات والتحقق، بلا workflow مستقل لكل PR | إضافة validation workflow ضمن Batch 0 |

### 3.2 Current UI → function/module → data dependency

| Current UI | Underlying function/module | Data dependency | قرار الهجرة |
|---|---|---|---|
| Header/status strip | `render_digital_header()` | كامل rental dataframe و`period_label` | REUSE + RESTYLE ثم تقليل الإحصاءات العامة |
| Role selector/banner | `render_user_profile_selector()`, `render_user_profile_overview()` | `user_profiles.py` | HIDE/DEFER من Core shell؛ الدور لا يغير IA |
| Global filters | `render_filters()` | أعمدة rental الأساسية | REFACTOR إلى Market scope محلي |
| Investor first page | `render_riyadh_first_page()` | Riyadh rental + sales | تفكيك إلى Home وDeal بدل صفحة مركبة |
| Opportunity list/cards | `build_riyadh_property_scores()`, `render_investment_opportunities()` | current/prior rental periods | REUSE + RESTYLE؛ إبقاء Inference/cohort |
| Market signals | `detect_market_signals()`, `render_market_signals_platform()` | opportunity score dataframe | REUSE بحذر؛ لا CTA شرائي مطلق |
| Comparison | `render_neighborhood_comparison_engine()` | scored eligible segments | REFACTOR إلى أداة واحدة بعقد context |
| Deal inputs/results | `render_property_valuation_engine()` | rental scope، sales match، user inputs | REUSE + RESTYLE مع submit/edit state صريح |
| Deal economics | `evaluate_property_price()`, `analyze_property()`, `stress_test_property()` | user inputs + market snapshot | REUSE |
| Sale evidence | `latest_sale_comparable()` | sale snapshot | REUSE؛ Missing Sale Match عند عدم التطابق |
| Forecast | `forecast_market()`, `render_market_forecast()` | 4+ historical quarters | HIDE/DEFER كقسم ثانوي، لا Hero KPI |
| Alternatives | `rank_alternatives()`, `render_investment_alternatives()` | scored same-type candidates | MOVE إلى Comparison/contextual action |
| Market KPIs/charts | `render_kpis()`, `render_charts()` | filtered rental + snapshot | REUSE + RESTYLE/REFACTOR chart payload |
| Data quality/sources | `render_data_quality()`, `render_official_sources_status()`, registry lineage | rental/sales/catalog | MOVE إلى البيانات والمنهجية |
| Reports/downloads | `build_investment_memo_html/pdf()`, `build_investor_report()` | deal/market results | MOVE إلى التقارير؛ لا تكرار generators داخل Core |
| Neighborhood report | `neighborhood_interface.py`, `neighborhood_report.py` | rental snapshot | MOVE إلى التقارير لاحقًا |
| Standalone Riyadh map | `riyadh_map_viewer.py` | rental + unverified coordinates | HIDE؛ لا route مستقل ولا markers قبل verified geography |
| Platform/pricing | `render_platform_page()` | static brand/pricing | HIDE/DEFER خارج workspace |

## 4. Figma → Code Mapping

### 4.1 Home (`21:3`)

| Figma section/component | Current implementation | Classification | أقل تغيير صحيح |
|---|---|---|---|
| App shell + six destinations | Header + sidebar + seven role-dependent tabs | REFACTOR | route ثابت وستة labels، مع conditional render لصفحة واحدة |
| Value proposition | أجزاء من `digital-header` و`render_platform_page()` | NEW PRESENTATION ONLY | copy/render function بلا منطق جديد |
| Primary/secondary actions | لا يوجد routing صريح بين Home/Deal/Market | NEW PRESENTATION ONLY | زران يغيران route فقط |
| Scope line | sidebar filters/status strip | REFACTOR | view-model ثابت: Riyadh/all districts/studio/2026 Q1 |
| City KPI trio | `aggregate_market`, `quarterly_trend`, `render_kpis` | REUSE + RESTYLE | bind 20,255، 11,713، +0.2% من البيانات |
| Opportunity review cards | property/opportunity score renderers | REUSE + RESTYLE | 84.5/83.7 من analytics مع Inference/cohort |
| Data sufficiency/evidence | `confidence_status`, source renderers | REFACTOR | rename to sufficiency، metric classification من registry |
| Methodology teaser | full data/source tab | MOVE | سطر دليل + link إلى البيانات والمنهجية |

### 4.2 Deal Analysis (`40:3`, `40:4`)

| Figma section/component | Current implementation | Classification | أقل تغيير صحيح |
|---|---|---|---|
| Deal form | inputs في `render_property_valuation_engine()` | REUSE + RESTYLE | نفس الحقول والvalidators داخل form واضح |
| Input → Result → Edit | الحساب حي مع كل rerun، بلا submitted snapshot | REFACTOR | draft + submitted snapshot + mode فقط |
| Decision answer-first | `analyze_property()` ورسائل decision | REUSE + RESTYLE | القرار أولًا، ثم الأسباب والاقتصاديات |
| Market evidence | `district_market_snapshot()` | REUSE + RESTYLE | bind 10,295 Raw، 437 contracts، +5.9 QoQ |
| Sale match/missing | `latest_sale_comparable()` وحالة info | REUSE + RESTYLE | لا fallback غير متكافئ |
| Economics/stress | `underwriting.py` | REUSE + RESTYLE | لا تغيير formulas |
| Deal inference | `deal_score` في underwriting | REUSE + RESTYLE | Inference منفصل عن Opportunity وضمن input scenario |
| Forecast | `forecast_market()` | HIDE/DEFER | يبقى بعد الفعلي/الضغط وبـvalidation quality |
| Alternatives | `rank_alternatives()` | MOVE | إلى Comparison مع context متكافئ |
| PDF/HTML downloads | `reporting.py` | MOVE | وجهة التقارير؛ يمكن CTA سياقي فقط |

### 4.3 Market Exploration (`58:39`, `58:108`, `58:177`, `58:246`, `58:315`)

| Figma section/component | Current implementation | Classification | أقل تغيير صحيح |
|---|---|---|---|
| Market-only filters | global `render_filters()` | REFACTOR | widgets namespaced داخل Market |
| Overview KPIs | `build_market_snapshot()`, `render_kpis()` | REUSE + RESTYLE | نفس analytics مع scope ظاهر |
| Rental trend | `quarterly_trend()`, `render_trend_chart()` | REFACTOR | dense period axis + null gap + states |
| Segment list/ranking | opportunity tables/cards | REUSE + RESTYLE | أعمدة priority بدل الجدول العريض الحالي |
| Segment detail | district helpers + score rows | REFACTOR | تركيب view-model واحد للشريحة |
| List/Map switch | لا يوجد switch موحد؛ توجد tabs متعددة | NEW PRESENTATION ONLY | state واحد داخل Market |
| Verified map view | Folium الحالي يولد/يخمن مواقع | BLOCKED BY DATA | Approved insufficient state فقط |
| Empty/insufficient/sale messages | رسائل `st.info/warning` متفرقة | NEW PRESENTATION ONLY | helper موحد للرسالة والفعل |
| Contextual compare action | comparison موجود في tab آخر | REFACTOR | يملأ anchor ويحفظ cohort ثم يفتح Comparison |

### 4.4 Comparison (`63:3`, `63:72`, `63:141`)

| Figma section/component | Current implementation | Classification | أقل تغيير صحيح |
|---|---|---|---|
| Selection | selectboxes في comparison engine | REUSE + RESTYLE | دعم anchor القادم من Market |
| Locked comparable context | غير ممثل كعقد state | REFACTOR | derive+validate city/type/period/grain/cohort |
| Answer-first result | table + `comparison_verdict()` | REUSE + RESTYLE | لغة نسبية لا winner مطلقًا |
| Metric comparison | `comparison_metric_table()` | REUSE + RESTYLE | bind registry، units، periods، classification |
| Opportunity difference | property score rows | REUSE + RESTYLE | 84.5 مقابل 83.7 وفرق 0.8 Inference |
| Eligibility/mismatch | فحص محدود لوجود صفين فقط | REFACTOR | reject grain/type/period/cohort mismatch |
| Duplicate comparisons | market map compare + investment alternatives + map page compare | HIDE/DEFER | أداة Comparison واحدة؛ القدرات تنتقل إليها |

### 4.5 حصيلة التصنيف

- **REUSE:** data access، data prep، metric formulas، underwriting، matching، reporting engines.
- **REUSE + RESTYLE:** KPI output، opportunity cards، deal result، segment list، comparison result.
- **REFACTOR:** router، scope، submitted deal state، chart data contract، comparable context.
- **MOVE:** alternatives/reports/methodology/map view إلى وجهاتها المعتمدة.
- **HIDE/DEFER:** role-dependent workspace IA، pricing/platform، forecast prominence، duplicate comparisons.
- **NEW PRESENTATION ONLY:** Hero، shell wrappers، evidence/data messages، view switch؛ لا feature logic جديد.
- **BLOCKED BY DATA:** verified geographic map markers/heat layer.

## 5. Analytics Preservation Contract

لا يُنقل أي literal من Figma إلى Production. الصفحة تطلب view-model، والـview-model يستدعي analytics/registry ثم ينسق العرض.

| Contract | مصدر الحقيقة | Production assertion |
|---|---|---|
| Home rent | `weighted_average_rent` | Riyadh/all districts/studio/2026 Q1 = 20,254.958… → 20,255 Calculated |
| Home contracts | deduplicated `total_deals` sum | 11,713 Raw aggregate للنطاق نفسه |
| Thulaim rent | published row | 10,294.91 → 10,295 Raw، studio/residential/2026 Q1 |
| Thulaim growth | `entity_period_market()` | 9,721.93 → 10,294.91 = +5.8937% → +5.9% QoQ |
| Growth period | period index | 2025 Q4 → 2026 Q1 و`period_gap=1` |
| Opportunity | governed score | Thulaim 84.5، Al-Murabba/المرقب 83.7، Inference داخل same-type geo cohort |
| Deal score | `underwriting.analyze_property()` | Inference لسيناريو المدخلات، ليس Opportunity Score |
| Sufficiency | rule-based eligibility | label ordinal؛ لا تسمى confidence أو probability |
| Sales | `latest_sale_comparable()` | تعرض فقط exact city/district/property-type coverage؛ وإلا Missing Sale Match |
| Missing growth | `growth_pct is null` | «غير متاح»، لا صفر ولا وصل غير متتالٍ |
| Forecast | `forecast_market()` | secondary scenario؛ history sufficiency منفصلة عن backtest status/error |

ملاحظة تدقيقية: البيانات الحالية أعادت إنتاج 20,254.958، 11,713، 10,294.91، 437، 9,721.93 و340. التغطية البيعية الحالية للأراضي السكنية فقط ولا تطابق ثليم/استديو. اختبارات الحوكمة الحالية تمنع growth غير المتتالي وتثبت cohort eligibility.

## 6. Navigation Migration

الطريقة الأقل تغييرًا والمتوافقة مع الحد الأدنى الحالي `streamlit>=1.30`:

1. إبقاء `app.py` entry point واحدًا.
2. إنشاء route key واحد `core.route` وقائمة ثابتة من ست وجهات.
3. renderer بسيط يختار صفحة واحدة بـ`if/elif`؛ لا `st.tabs` للوجهات لأن محتوى tabs ينفذ في كل rerun.
4. استعمال control تنقل واحد في shell (sidebar/native control ثم restyle محدود) بدل HTML links وهمية.
5. كل action سياقي يكتب state صالحًا، يغير route، ثم `st.rerun()`.

الوجهات:

1. الرئيسية
2. تحليل صفقة
3. استكشاف السوق
4. المقارنة
5. التقارير
6. البيانات والمنهجية

الخريطة `market.view = "map"` وليست route. التقارير تجمع generators الحالية. المقارنة الوحيدة تستقبل context من Market أو تبدأ selection مستقلة. Market filters لا تظهر خارج Market، وDeal widgets لا تقرأ Market scope تلقائيًا.

لا أوصي بـ`st.navigation` في Batch 1 ما دام المشروع يعلن دعم Streamlit 1.30؛ استعماله يفرض رفع minimum واختبار نشر أوسع دون حاجة وظيفية.

## 7. Session State / Context Contract

### 7.1 المفاتيح الدنيا

| Key | النوع | المالك | القاعدة |
|---|---|---|---|
| `core.route` | enum | Shell | إحدى الوجهات الست فقط |
| `market.city` | string | Market | الافتراضي الرياض |
| `market.property_type` | string | Market | مستقل عن Deal |
| `market.period_index` | int | Market | أحدث فترة صالحة افتراضيًا |
| `market.geography_level` | enum | Market | city/district حسب الشاشة |
| `market.selected_segment` | string/null | Market | segment profile الحالي |
| `market.view` | enum | Market | list/map؛ لا route إضافي |
| `comparison.anchor_segment` | string/null | Comparison | يملأ من Market أو يدويًا |
| `comparison.candidate_segment` | string/null | Comparison | البديل الثاني |
| `comparison.source_route` | enum/null | Comparison | للعودة/الإلغاء مع حفظ المصدر |
| `deal.mode` | enum | Deal | input/result |
| `deal.submitted` | mapping/null | Deal | snapshot وحيد للمدخلات التي ولدت النتيجة |

لا نخزن `comparison cohort` كقيمة مستقلة قابلة للانحراف؛ يشتق من `{city, property_type, period_index, geography_level}` المحفوظة ضمن payload validated عند الانتقال. ويمكن تمثيل draft deal بمفاتيح widgets ذات prefix `deal.input.*`، دون نسخة dict ثانية؛ عند submit فقط تؤخذ نسخة إلى `deal.submitted`.

### 7.2 Market → Segment → Comparison

1. تغيير filter يحدث Market view-model فقط.
2. اختيار row يكتب `market.selected_segment` ويعرض Segment مع scope نفسه.
3. «مقارنة بدائل متكافئة» ينسخ anchor وsource ويثبت payload الحالي.
4. Comparison يعيد التحقق من وجود anchor ومن مطابقة city/type/period/grain/cohort في البيانات الحالية.
5. mismatch أو stale context يعرض حالة غير مؤهلة؛ لا يصحح الاختيار بصمت.
6. Cancel/Back يعيد `core.route=market` ويحافظ على Market keys.

### 7.3 Deal Input → Result → Edit

1. widgets تحرر draft فقط.
2. submit يحقق الحقول، ينسخها إلى `deal.submitted` ويضبط `deal.mode=result`.
3. النتيجة تُحسب في كل rerun من submitted + current governed data؛ لا نخزن نتيجة مشتقة طويلة العمر.
4. Edit يعيد input مع draft مساويًا لـsubmitted.
5. Market scope لا يغير deal submitted أو reference دون action صريح.

## 8. Component Strategy

الـabstraction المقترح صغير ومبني على تكرار حقيقي:

### Helpers تستحق الإنشاء

- `render_app_shell(route, on_navigate)` للتنقل والعنوان فقط.
- `render_page_header(title, scope, evidence)`.
- `render_metric(label, value, unit, classification, period, note)`؛ formatting لا calculation.
- `render_evidence_badge(classification)` من Registry mapping.
- `render_data_message(kind, title, body, action)` للحالات المشتركة.
- `render_section(title, description)` كغلاف خفيف.
- `render_view_switch()` للـList/Map فقط.
- `render_chart_container(state, metadata, figure, fallback_rows)`.

### تبقى functions بسيطة

- Hero Home وترتيب CTA.
- قوائم الأسباب وmarket scope summary.
- Deal decision narrative.
- Segment row/card وcomparison metric row.
- Methodology teaser.

لا ننشئ Button/Input/Card framework خاصًا؛ نستعمل Streamlit widgets ونطبق keys/labels/CSS موحدة. لا ندخل inheritance أو component registry أو مكتبة frontend جديدة.

## 9. CSS Strategy

### ما يبقى

- light theme في `.streamlit/config.toml` كنقطة fallback.
- قواعد RTL العامة واتجاه الأرقام والـPlotly LTR عند الحاجة.
- custom properties، لكن يعاد تسميتها semantic مثل `--surface-default`, `--surface-subtle`, `--text-primary`, `--text-secondary`, `--border-default`, `--action-primary`.

### ما يستبدل تدريجيًا

- `Segoe UI/Tahoma/Arial` يستبدل بـCairo Regular/SemiBold/Bold عبر ملفات font محلية مرخصة؛ لا اعتماد شبكة خارجي.
- الألوان المباشرة والgradients/shadows داخل `.profile-banner`, `.marketing-hero`, `.assistant-shell` تربط بتوكنز Foundation أو تزال إن لم تعد ضمن High-Fi.
- البطاقات القديمة القوية بصريًا تستبدل containers أخف حسب hierarchy المجمدة.

### selectors خطرة

- `html, body, [class*="css"]`: واسع وهش وقد يطابق classes داخلية غير مقصودة.
- `.stApp`, `.block-container`, `.stPlotlyChart`: selectors عالمية مرتبطة ببنية Streamlit.
- `div[data-testid="..."]` و`section[data-testid="stSidebar"]`: أكثر ثباتًا نسبيًا، لكنها تبقى implementation details وتتطلب smoke test عند ترقية Streamlit.
- global styling لـmetric labels/values يجعل كل destination متطابقة حتى عندما تختلف hierarchy.

الاستراتيجية: token block واحد + selectors stable بأضيق نطاق ممكن + custom classes للHTML المملوك لنا. لا نسخ pixel-by-pixel، ولا استبدال كامل للCSS في دفعة واحدة. يحذف legacy rule فقط بعد انتقال آخر consumer واختبار responsive.

## 10. Chart Strategy

Plotly 6 الحالي قادر على العقد المطلوب؛ لا حاجة لمكتبة جديدة.

- **Default:** figure من payload محكوم ومع metadata ظاهرة: metric، unit، grain، scope، period.
- **Loading:** يظهر قبل بناء payload/figure، ولا يعاد تفسير غياب dataframe كتحميل.
- **Insufficient:** data message + سبب الأهلية + fallback rows عند توفرها.
- **Missing period:** densify محور الأرباع، ضع `None/NaN` للفترة الغائبة، واستخدم `connectgaps=False`. مجرد حذف 2025 Q3 من dataframe غير كافٍ لأن Plotly قد يصل 2025 Q2 بـ2025 Q4.
- **Arabic/RTL:** النص المحيط RTL، plot canvas LTR؛ labels عربية، والأرقام والوحدات في hovertemplate صريحة.
- **Correct semantics:** figure لا يحسب metric؛ يستقبل chart data contract من view-model.
- **Accessibility:** fallback text/table من payload نفسه، لا نسخة حساب ثانية.

يُحتفظ بـ`render_chart()` و`CHART_CONFIG`، ويضاف فوقهما container/state contract بدل إعادة كتابة كل chart.

## 11. Map Decision

**القرار: عرض الحالة المعتمدة «المواضع غير موثقة» داخل Market Map view، مع List بديل؛ وعدم عرض أي markers أو heat layer جغرافي.**

السبب المؤكد: `riyadh_map_viewer.py` يستخدم قاموس إحداثيات يدويًا، ثم `np.random.uniform()` لأي حي غير موجود. كما أن متوسطه الحالي بسيط عبر التاريخ وليس metric scope المعتمد. لذلك:

- يخفي route «خريطة الرياض» في Batch 1.
- لا يستدعى renderer الجغرافي القديم من Core Market.
- يمكن إبقاء ملفه مؤقتًا للرجوع/الاختبارات، لكن لا يصل Production navigation.
- heatmap غير الجغرافية الحالية يمكن الاحتفاظ بها كـmatrix chart إذا سميت بوضوح، لا كخريطة مواقع.

لتفعيل الخريطة مستقبلًا يلزم: مصدر حدود/centroids موثق، identifier ثابت يربط district، provenance/version، coverage threshold، فحص unmatched/duplicate IDs، واختبار يمنع أي fallback عشوائي أو تقريبي. هذه **Data Dependency** وليست blocker لباقي Market.

## 12. Reports وData/Methodology

- **Reports (B):** تأتي في Batch 6 بعد الرحلات الأربع. تعيد استخدام `reporting.py`, `neighborhood_report.py` وmarket report builder، وتجمع الإنشاء والتنزيل في وجهة واحدة. لا يعاد تصميم engine قبل تجميعه.
- **Data & Methodology (A):** أيضًا Batch 6، لكن كمسار مستقل يبدأ بـregistry/source/coverage overview ثم metric detail. لا يُسحب full current data tab حرفيًا إلى Home.
- إلى أن تُعتمد High-Fi الخاصة بهما، تنفذ فقط shell destination وحالة/صفحة محافظة تعتمد الأنماط الحالية دون توسيع محتوى.

## 13. Responsive Strategy

| المنطقة | الخطر الحالي | approach |
|---|---|---|
| Navigation | ستة عناصر أفقية قد تضيق؛ tabs الحالية scroll/تلتبس | control رأسي/قابل للطي في sidebar، نفس labels/routes |
| KPI groups | `st.columns(4)` يكدس الأرقام أو يخفيها | 3 كحد Core؛ stack طبيعي واختبار 320/768/1024/1440 |
| Filters | sidebar طويل وعالمي | Market filters داخل expander/stack على الهاتف |
| Horizontal comparison | table عريض | A → فرق/سبب → B كبطاقات متتابعة؛ لا horizontal scroll كحل وحيد |
| Charts | margins ثابتة 100–260px | responsive height/margins + fallback table |
| List/Map | خريطة 1200px ثابتة حاليًا | switch واحد؛ القائمة default على الهاتف؛ map insufficient state fluid |
| Deal result | عمود input/result مزدوج وطويل | result-first sections ثم edit action؛ لا إبقاء form بمحاذاة النتيجة على الهاتف |

لا يعتمد responsive على اكتشاف device server-side. نعتمد layout مرن، column stacking الطبيعي، CSS media queries محدودة، واختبارات viewport فعلية.

## 14. Performance

### المخاطر الحالية

- `st.tabs` تنفذ كل محتوى الصفحات؛ `main()` يبني snapshot ثم يشغل تحليلات ورسوم وتقارير حتى للتبويبات غير المرئية.
- `build_market_snapshot()` وproperty scores وdistrict aggregations يعاد حسابها في المسارات المتعددة.
- توليد PDF داخل rerun في Deal يحدث قبل طلب التنزيل.
- تحميل rental/sales كاملين cache جيد، لكن كل filter ينسخ dataframes كبيرة عدة مرات.
- Folium map وبناء كل markers مكلف وغير مطلوب الآن.
- مفاتيح widgets المتناثرة تزيد reruns غير المفهومة وتعرض stale state.

### المعالجة المناسبة

1. route-based conditional rendering سيزيل أكبر تكلفة بلا optimization إضافي.
2. حافظ على data caches الحالية keyed بـwarehouse version.
3. cache view-models الثقيلة فقط بمفاتيح primitive: warehouse version + city + type + period + grain + min_deals.
4. لا cache للـUI nodes أو user inputs الحساسة؛ احسب underwriting من submitted snapshot سريعًا.
5. أنشئ PDF عند action صريح، ثم خزّن bytes/signature للجلسة.
6. ابق figure creation داخل الصفحة الظاهرة؛ لا precompute لكل route.
7. قس زمن rerun والذاكرة بعد Batch 5 قبل أي indexing أو preaggregation إضافي.

## 15. Testing Strategy

### الوضع الحالي

تشغيل `python -B -m pytest -p no:cacheprovider -q` أعطى **73 passed + 5 subtests passed**. الاختبارات تغطي auth، data URL، sales matching، analytics governance، forecast، underwriting، reporting، developer paths، map utilities وneighborhood report. لا توجد حاليًا اختبارات route/context أو metric-to-view binding أو responsive/accessibility.

### ما يضاف قبل وأثناء الهجرة

| Test layer | المطلوب |
|---|---|
| Metric anchor integration | snapshot assertions للقيم الست المرجعية، مع تحديث مقصود عند تغير snapshot لا literal داخل UI |
| Metric semantics | Raw/Calculated/Inference، QoQ period pair، insufficiency≠confidence |
| Navigation | ست routes فقط، route invalid يعود Home، Map ليست route |
| State | Market→Segment→Comparison يحفظ payload؛ cancel يعود؛ mismatch يرفض |
| Deal | draft/submitted/result/edit وعدم تأثر submitted بفلاتر Market |
| Eligibility | current/prior min-deals، nonconsecutive growth، sale exact match، comparison cohort |
| Missing states | empty، insufficient، missing prior، missing sale، forecast limited/high error |
| Chart contract | dense periods، null gap، `connectgaps=False`، unit/grain/period/fallback rows |
| Map blocking | Core renderer لا يستدعي unverified coordinates، ويعرض approved message/list |
| Content contract | labels العربية الست، QoQ لا YoY، evidence classes الصحيحة |
| Smoke rendering | `streamlit.testing.v1.AppTest` لكل route وحالة حرجة |
| Visual/responsive | screenshots عند 320/768/1024/1440، RTL/Cairo/overflow/focus |
| Deployment matrix | Python 3.12 canonical؛ 3.14 advisory حتى اعتمادها، PostgreSQL وSQLite fallback |

تبقى اختبارات Data/Analytics الحالية gate لا يسمح بتغيير توقعاتها لمجرد تمرير UI. أي تغير metric يحتاج Metric Governance مستقلة، لا تعديل snapshot assertion بصمت.

## 16. Migration Batches

### Batch 0 — Safety, baseline contracts, and route seam

- **Files المتوقعة:** `tests/test_core_metric_contract.py`, `tests/test_core_state_contract.py`, `tests/test_core_routes.py`, fixture صغيرة تحت `tests/fixtures/`, وworkflow PR validation؛ وقد يضاف `src/real_estate_intel/ui/contracts.py` بلا UI.
- **Dependencies:** Git baseline نظيف ومراجع.
- **Acceptance:** كل 73+5 اختبارًا يبقى ناجحًا؛ anchors والـQoQ/cohort/sales/missing rules مغطاة؛ route/state contract pure ومختبر.
- **Rollback:** commit مستقل لا يغير العرض أو البيانات.
- **Risk:** LOW.

### Batch 1 — Shell, navigation, and visual foundations

- **Files المتوقعة:** `app.py`, `.streamlit/config.toml`, `assets/fonts/`, `src/real_estate_intel/ui/shell.py`, `components.py`, `styles.py` أو stylesheet واحد مملوك للتطبيق.
- **Dependencies:** Batch 0، Cairo assets/licensing، قرار baseline.
- **Acceptance:** ست وجهات ثابتة؛ route واحد يُعرض؛ Map ليست destination؛ global filters لا تعطل الصفحات؛ no analytics diff؛ RTL/Cairo/tokens smoke pass.
- **Rollback:** الرجوع إلى router القديم في commit واحد؛ وحدات UI الجديدة غير مستخدمة بعده.
- **Risk:** MEDIUM.

### Batch 2 — Home

- **Files المتوقعة:** `ui/home.py`, presentation/view-model module، `app.py` router، tests.
- **Dependencies:** Batches 0–1.
- **Acceptance:** hierarchy/CTA مطابقان؛ 20,255/11,713/+0.2 تأتي من current data؛ 84.5/83.7 Inference؛ methodology progressive disclosure؛ لا forecast/sales غير مؤهلة.
- **Rollback:** route Home يعود renderer القديم دون التأثير على بقية routes.
- **Risk:** MEDIUM.

### Batch 3 — Deal Analysis

- **Files المتوقعة:** `ui/deal.py`, `ui/contracts.py`, presentation adapter، tests؛ analytics/underwriting تبقى دون تعديل إلا لbug مثبت مستقل.
- **Dependencies:** Batch 0–2؛ scenario fixture كاملة.
- **Acceptance:** Input→Result→Edit؛ submitted ثابت؛ 10,295 Raw و+5.9 QoQ والفترتان صحيحة؛ sale match guarded؛ decision/economics يعاد إنتاجها؛ reports/alternatives secondary/moved.
- **Rollback:** Deal route فقط يعود renderer الحالي.
- **Risk:** HIGH.

### Batch 4 — Market Exploration

- **Files المتوقعة:** `ui/market.py`, chart/view-model helpers، tests، `app.py` routing.
- **Dependencies:** Batches 0–2؛ chart contract.
- **Acceptance:** filters محلية؛ overview/list/segment تحفظ scope؛ missing Q3 line gap؛ map view يعرض unverified state/list؛ لا random coordinates؛ contextual compare payload صحيح.
- **Rollback:** Market route فقط؛ geographic legacy remains unreachable.
- **Risk:** HIGH.

### Batch 5 — Comparison

- **Files المتوقعة:** `ui/comparison.py`, context validators، tests؛ إخفاء entry points المكررة في `app.py`.
- **Dependencies:** Batch 4 payload contract.
- **Acceptance:** أداة واحدة؛ independent + Market-prefilled selection؛ exact comparable eligibility؛ 84.5/83.7 و0.8 Inference؛ context/back محفوظ؛ mobile sequence صحيح.
- **Rollback:** Comparison route وentry actions فقط.
- **Risk:** HIGH.

### Batch 6 — Supporting destinations

- **Files المتوقعة:** `ui/reports.py`, `ui/methodology.py`, adapters حول `reporting.py`, `neighborhood_report.py`, `official_sources.py`, `metric_registry.py`.
- **Dependencies:** Core routes مستقرة؛ اعتماد مستوى العرض المحافظ للتقارير وData/Methodology.
- **Acceptance:** generators مركزية؛ metric/source definitions قابلة للتتبع؛ partial report مفصح؛ لا duplication داخل Core.
- **Rollback:** كل destination مستقلة.
- **Risk:** MEDIUM.

### Batch 7 — Responsive, accessibility, performance, deployment hardening

- **Files المتوقعة:** UI/CSS/tests/config فقط بحسب العيوب المثبتة؛ إزالة `use_container_width` المتبقي.
- **Dependencies:** Batches 1–6.
- **Acceptance:** viewport matrix، keyboard/focus/contrast/screen reader smoke، no overlap، rerun budget، PostgreSQL/SQLite parity، Python 3.12 release validation، no deprecated width usage.
- **Rollback:** fixes صغيرة منفصلة بحسب concern.
- **Risk:** MEDIUM.

## 17. Git Strategy

الحالة المدققة:

- Branch: `main` يتتبع `origin/main`.
- HEAD: `0caa1e5 Add neighborhood reports and Riyadh map explorer`.
- Tracked modified: `app.py`, rental snapshot، وسبع وحدات analytics/data/developer/forecast/source/reporting/underwriting.
- Untracked: `docs/audits/`, `docs/ux/`, `outputs/`, سكربتا KPI audit، `metric_registry.py`, `test_metric_governance.py`.
- التغير tracked الحالي: 203 additions / 114 deletions إضافة إلى binary snapshot.

التوصية قبل التنفيذ:

1. راجع التغييرات الحالية كحزمة Metric Remediation/Governance؛ لا تخلطها مع migration.
2. افصل artifacts الثقيلة في `outputs/` عن production commit، وحدد ما يجب حفظه فقط.
3. اجعل UX docs commit مستقلًا عن كود/بيانات governance.
4. بعد اعتماد baseline نظيف ومشترك، أنشئ branch مثل `codex/qareena-core-migration` من ذلك commit.
5. كل Batch commit/PR مستقل مع rollback boundary المذكور.
6. لا تستخدم stash/reset لتنظيف الحالة الحالية؛ هي عمل سابق يجب حفظه/مراجعته بقرار المستخدم.

وجود `metric_registry.py` غير متتبع بينما `official_sources.py` المعدل يستورده يجعل الحالة الحالية غير قابلة لإعادة البناء من Git وحده؛ لذلك تنظيف baseline **Implementation Blocker** حقيقي.

## 18. Deployment Impact

| البند | الوضع/الأثر | المعالجة |
|---|---|---|
| Current hosting | Streamlit Cloud، `app.py` main file | لا يتغير entry point؛ migration قابلة للنشر تدريجيًا |
| Database | PostgreSQL/Supabase عند `DATABASE_URL`، ثم SQLite/CSV | إبقاء fallback؛ اختبار parity في كل release |
| Auth | Supabase URL + publishable key اختياريان | Shell refactor لا يغير auth contract؛ لا تسرب secrets |
| Local runtime | Python 3.14.0، Streamlit 1.56.0، pandas 3.0.5، Plotly 6.9.0 | مفيد كforward check، ليس canonical وحده |
| CI runtime | Python 3.12 في refresh workflow | اجعله canonical release runtime حتى اعتماد 3.14 رسميًا |
| Dependency bounds | `streamlit>=1.30` بلا upper/pin | لا تستخدم APIs أحدث قبل رفع minimum واختبار Cloud؛ أضف constraints/lock لاحقًا |
| Deprecated API | 8 مواضع `use_container_width=True` في neighborhood/map modules | استبدالها بـ`width="stretch"` في Batch 7 أو عند لمس الملف |
| Release validation | `validate_release.py` يجمع ملفات محددة ولا يشمل كل الوحدات الجديدة تلقائيًا | استبداله/توسيعه إلى compile-all + pytest + route smoke في Batch 0/7 |
| Data refresh | workflow يكتب snapshots مباشرة إلى `main` | لا يتأثر UI وظيفيًا؛ تجنب تزامنه مع migration merge وراجع anchor updates |

التطبيق الحالي سيظل قابلًا للنشر لأن entry point وdata interfaces لا تتغير. أكبر مخاطر النشر ليست الحسابات، بل selectors المرتبطة بإصدار Streamlit، font assets، route reruns، واختلاف بيئة 3.14 المحلية عن 3.12 في CI.

## 19. Blockers Register

### IMPLEMENTATION BLOCKER — 1

1. **IB-01: لا يوجد Git baseline نظيف قابل لإعادة البناء.** يجب مراجعة وفصل/حفظ تغييرات governance الحالية وإدخال dependency غير المتتبع `metric_registry.py` قبل أول تعديل Production.

### BATCH BLOCKER — 2

1. **BB-01 (Batch 4 Map):** لا markers/geo heat layer قبل verified geography dataset وعقد الربط.
2. **BB-02 (Batch 6):** Reports وData/Methodology ليستا Core High-Fi مجمدتين؛ التنفيذ يقتصر على معالجة محافظة حتى اعتماد تفاصيلهما.

### DATA DEPENDENCY — 3

1. Verified district geography + stable IDs/provenance/coverage.
2. Matched sales coverage على city/district/property type/period؛ الغياب الحالي يظل Missing Sale Match.
3. Forecast validation quality/history continuity؛ high-error أو insufficient history يبقى scenario/hidden.

### TECH DEBT — 7

1. `app.py` monolith وخلط UI بالحسابات page-level.
2. تكرار aggregations/view preparation في أكثر من renderer.
3. ثلاث واجهات مقارنة/بدائل متنافسة وتقارير موزعة.
4. CSS global/Streamlit-internal selectors وألوان مباشرة.
5. `use_container_width` deprecated في 8 مواضع.
6. dependency ranges واسعة واختلاف Python 3.12/3.14 بلا matrix ثابتة.
7. release validation file list يدوي وغياب PR test workflow.

### VALIDATION — 9

1. Regression suite + metric anchors على Python 3.12 وadvisory 3.14.
2. Six-route navigation، invalid route، back/refresh.
3. Market→Segment→Comparison context retention/eligibility/cancel.
4. Deal submit/result/edit reproducibility وعزل Market state.
5. Metric binding/classification/period/sales/missing-data states.
6. Chart default/loading/insufficient/gap/unit/fallback contract.
7. Responsive viewports وcomparison/list/filter stacking.
8. RTL/Cairo/keyboard/focus/contrast/screen-reader/touch.
9. Streamlit Cloud smoke وPostgreSQL→SQLite fallback parity/performance.

## 20. Batch Summary

| Batch | Scope | Risk | Main files | Preconditions | Acceptance Gate |
|---|---|---|---|---|---|
| 0 | Safety, metric/state/route contracts | LOW | tests, fixtures, CI, `ui/contracts.py` | Clean reviewed baseline | Existing suite + core contracts all pass |
| 1 | Shell, six routes, tokens/Cairo seam | MEDIUM | `app.py`, config, assets, `ui/shell.py`, components/styles | Batch 0 | One route rendered; IA/RTL/Cairo/tokens pass |
| 2 | Home | MEDIUM | `ui/home.py`, presentation adapter, tests | Batches 0–1 | Data-bound Home and hierarchy pass |
| 3 | Deal | HIGH | `ui/deal.py`, state adapter, tests | Batches 0–2, scenario fixture | Reproducible submit/result/edit and governed evidence |
| 4 | Market | HIGH | `ui/market.py`, chart helpers, tests | Chart contract; geo fallback approved | Scope/list/segment/gap/map-block/context pass |
| 5 | Comparison | HIGH | `ui/comparison.py`, validators, tests | Batch 4 payload | One comparable tool, state and metrics pass |
| 6 | Reports + Data/Methodology | MEDIUM | support pages + existing report/source modules | Core stable; conservative design scope | Centralized outputs and traceable registry |
| 7 | Responsive/A11y/performance/deploy hardening | MEDIUM | UI/CSS/tests/config | Batches 1–6 | Viewport, accessibility, latency, deploy matrix pass |

## 21. Final Readiness

### Summary

- **Current architecture:** Streamlit monolith مع analytics/data modules جيدة، سبعة tabs عالمية وفلاتر sidebar.
- **Figma → code:** معظم السلوك موجود؛ المطلوب route/state/presentation rewrite محدود وإعادة تموضع القدرات.
- **Reusable implementation:** **72%** وظيفيًا.
- **Refactor-required:** navigation، page scope، Deal submitted state، Comparison context/eligibility، chart gap/state contract، تفكيك renderers.
- **New-presentation-only:** Hero، shell wrappers، metric/evidence/data-message treatment، List/Map switch.
- **Data blockers:** verified geography، matched sales coverage، forecast validation quality.
- **Map:** approved insufficient state داخل Market + List؛ لا random/approximate markers.
- **Navigation:** single-entry، session-state route، conditional page renderer، ست وجهات.
- **Session state:** namespaced minimal keys؛ derive ولا تكرر cohort/results.
- **CSS:** semantic tokens + Cairo محلي + migration scoped تدريجيًا؛ إزالة global legacy لاحقًا.
- **Charts:** Plotly يبقى؛ dense periods/null gap/states/fallback table.
- **Responsive:** stacking وترتيب محتوى، لا تصغير جداول/شاشات كامل.
- **Performance:** route conditional rendering أول تحسين؛ cache data/view-models فقط، PDF on demand.
- **Testing:** 73 tests + 5 subtests ناجحة؛ يضاف contract/state/smoke/visual/deploy coverage.
- **Git/worktree:** dirty `main`، 9 tracked modifications وكتل untracked؛ baseline منفصل إلزامي.
- **Deployment:** entry/fallback لا يتغيران؛ اختبر Streamlit selectors/fonts وPython 3.12/3.14.
- **Implementation Blockers:** 1.
- **Batch Blockers:** 2.
- **Data Dependencies:** 3.
- **Tech Debt:** 7.
- **Validation items:** 9.

### Decision

**READY WITH PRECONDITIONS**

### أول Batch موصى به

**Batch 0 — Safety, baseline contracts, and route seam.**

يبدأ فقط بعد تنظيف واعتماد baseline الحالي. السبب: التصميم مجمد والتحليلات صحيحة، لكن الانتقال سيغير مواضع عرض نفس المقاييس والسياق بين الرحلات. تثبيت anchors وQoQ/cohort/sales/missing rules وعقد route/state قبل تغيير الواجهة يمنع regression الصامت، ويجعل كل Batch التالية قابلة للرجوع والاختبار بصورة مستقلة.


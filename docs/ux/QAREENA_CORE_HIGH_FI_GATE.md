# Qareena — Core High-Fidelity Gate Review

**التاريخ:** 2026-09-04  
**نوع المراجعة:** Read-Only Audit  
**النطاق:** Home، Deal Analysis، Market Exploration، Comparison كمنتج واحد  
**القرار النهائي:** **CONDITIONAL PASS**

## Technical Summary

يمكن بناء Prototype قابل للاختبار من الرحلات الأربع الحالية. البنية العامة متماسكة، الوجهات الست ثابتة، Home تشرح قيمة قرينة وتفصل مساري «حلّل صفقة» و«استكشف السوق»، والمنتج يحافظ غالبًا على التسلسل: **السياق → النتيجة → السبب → الدليل → القيد → التفاصيل**.

لكن واجهة الإنتاج ليست جاهزة للتنفيذ الآمن بعد. يوجد تعارضان عابران للشاشات يجب حسمهما قبل Implementation:

- Home وDeal يعرضان لثليم/استديو/2026 Q1 متوسط إيجار **28,400 ر.س** بوصفه Calculated، بينما Market وComparison يعرضان **10,295 ر.س** بوصفه Raw published aggregate للنطاق نفسه ظاهريًا.
- Home وDeal يسميان **+5.9%** «النمو السنوي/مقارنة سنوية»، بينما Market وComparison يثبتانه كتغير ربعي متصل من **2025 Q4 إلى 2026 Q1**.

هذه التناقضات لا تمنع اختبار بنية الرحلة في Prototype، لكنها تمنع نقل النصوص والقيم الحالية كما هي إلى Streamlit. الخريطة كذلك جاهزة تصميميًا فقط، وليست جاهزة ببيانات إنتاج موثقة.

## Gate Scorecard

| البند | النتيجة |
|---|---|
| Final Gate Decision | **CONDITIONAL PASS** |
| P0 — Blocker | **0** |
| P1 — Must Fix Before Implementation | **4** |
| P2 — Can Defer | **3** |
| Data Dependency | **3** |
| Validation Needed | **5** |
| Journey consistency | **PASS للـPrototype / مشروط قبل Implementation** |
| Terminology consistency | **NEEDS FIX قبل Implementation** |
| Data semantics | **مشروطة؛ التصنيف جيد لكن يوجد drift في متوسط الإيجار والفترة** |
| Design System consistency | **PASS مع تحقق تنفيذي شامل لاحقًا** |
| Map readiness | **Design-ready فقط؛ غير Production-ready** |
| Responsive readiness | **قابلة للتحويل دون إعادة بناء IA؛ تحتاج مواصفة تنفيذ** |
| Accessibility readiness | **Heuristic PASS؛ الامتثال الفعلي غير مثبت** |
| Reports recommendation | **B** |
| Data & Methodology recommendation | **A** |
| Prototype readiness | **READY مع Interaction Contract محدد أدناه** |
| Implementation readiness | **NOT READY حتى إغلاق P1 وحواجز البيانات** |

## Scope and Evidence

تمت مراجعة Frames التالية من ملف Figma `L6FRBHQ4M3Q7ik1OV5Fwzi` دون أي تعديل:

| الرحلة | Frames المراجعة |
|---|---|
| Home | `21:3` |
| Deal Analysis | `40:3`، `40:4` |
| Market Exploration | `58:39`، `58:108`، `58:177`، `58:246`، `58:315` |
| Comparison | `63:3`، `63:72`، `63:141` |
| Phase 2 System | `16:4` |
| Reports Low-Fi | `2:132`، `2:141` |
| Data & Methodology Low-Fi | `2:150`، `2:159` |

راجعت أيضًا عقد الـIA الحالي، Gate الـLow-Fi، سجل المقاييس، ومخرجات KPI Audit الحالية:

- `docs/ux/QAREENA_INFORMATION_ARCHITECTURE_UX_BLUEPRINT.md`
- `docs/ux/QAREENA_LOW_FI_GATE_REVIEW.md`
- `src/real_estate_intel/metric_registry.py`
- `outputs/kpi_data_audit_after.json`

هذه مراجعة Heuristic وStructural، وليست اختبار مستخدمين أو تدقيق WCAG أو اختبار تطبيق منفذ.

## 1. Journey Coherence

### Home → Deal Analysis

**النتيجة: PASS للـPrototype.** زر «حلّل صفقة» هو Primary Action واضح، ووجهته تطابق اسم التنقل «تحليل صفقة». شاشة الإدخال تشرح أن القيم مدخلات مستخدم وليست دليلًا رسميًا، ثم تحفظ الفصل بين Deal inputs وMarket scope. الانتقال إلى النتيجة منطقي عبر «حلّل الصفقة»، والنتيجة تبدأ بسؤال القرار قبل الاقتصاديات والتفاصيل.

السياق المطلوب نقله: المدينة، الحي، نوع العقار، السعر، المساحة، افتراضات الاستثمار والتمويل، وفترة مرجع السوق. يجب ألا تتغير هذه القيم بصمت عند تغيير Market scope.

### Home → Market Exploration

**النتيجة: PASS للـPrototype.** زر «استكشف السوق» Secondary Action واضح ومختلف عن تحليل عقار محدد. Market تبدأ بنطاق ظاهر ثم KPIs ثم الاتجاه ثم الشرائح والقيود. الاختلاف بين المهمة الاستكشافية ومهمة الصفقة مفهوم بصريًا ونصيًا.

السياق المطلوب نقله: المدينة، الفترة، ونوع العقار الافتراضي. نطاق «كل الأحياء» يبقى Market filter ولا يتحول إلى Deal input.

### Market Exploration → Comparison

**النتيجة: CONDITIONAL.** المقارنة موجودة كوجهة واحدة في IA، وتحافظ على نفس النوع والفترة والمستوى الجغرافي. إلا أن نقطة الدخول السياقية الأوضح من Market تظهر داخل معالجة «لا توجد مقارنة بيع مطابقة» بصيغة «مقارنة بدائل متكافئة»، وليست Action عامة ثابتة بعد اختيار شريحتين. يمكن ربط Prototype الحالي، لكن يجب توثيق Trigger والاختيارات المنقولة قبل Implementation.

السياق المطلوب نقله: البديلان، المدينة، المستوى الجغرافي، نوع العقار، الفترة الحالية، الفترة السابقة المتصلة، وتعريفات المقاييس. لا يسمح بمقارنة غير متكافئة بصمت.

### Dead Ends and Duplicate Capabilities

- لا توجد نسخة ثانية مستقلة للخريطة؛ هي View داخل Market.
- المقارنة وجهة واحدة، ولا يظهر محرك مقارنة مكرر.
- التقارير وجهة واحدة في IA، ولم تُوزع كمولدات متعددة داخل Core High-Fi.
- نتائج Comparison تنتهي فعليًا عند «البيانات والمنهجية» أو التنقل العالمي. هذا مقبول كنهاية Prototype، لكنه لا يحقق بعد رابط IA السياقي إلى Deal/Report.
- لا توجد Actions وهمية ظاهرة على أنها وظائف مكتملة؛ لكن كل الروابط والأزرار ما زالت بلا Prototype interactions، وهو متوقع في هذه البوابة.

## 2. First-Visit Experience

**Heuristic result: PASS.** خلال 5–10 ثوانٍ، Home توضح أن قرينة منصة ذكاء عقاري قائمة على البيانات تساعد على فهم السوق وتحليل الفرص قبل القرار. التسلسل المرئي واضح:

1. ما هي قرينة وما فائدتها.
2. «حلّل صفقة» كإجراء أولي أساسي.
3. «استكشف السوق» كمسار ثانوي.
4. ماذا يحدث في النطاق الحالي.
5. ما الذي يستحق المراجعة.
6. المنهجية عند الحاجة.

الفرق بين المسارين واضح: Deal يبدأ من عقار ومدخلات مستخدم؛ Market يبدأ من نطاق وبيانات مرصودة. هذه النتيجة Cognitive walkthrough فقط وليست User Test.

## 3. Information Hierarchy

**النتيجة: PASS.** التسلسل العام متسق:

- Home: قيمة المنتج → الإجراء → KPIs → فرص للمراجعة → منهجية ثانوية.
- Deal: مدخلات المستخدم → قرار → أسباب القرار → دليل السوق → كفاية البيانات → منهجية.
- Market: نطاق → KPIs → Insight/Trend → شرائح → حدود القراءة.
- Comparison: سياق التكافؤ → خلاصة answer-first → الفروق → لماذا تهم → كفاية البيانات.

لا يسبق Score الدليل بوصفه حقيقة رسمية؛ يظهر Inference وداخل cohort. Charts لا تصبح Hero، والمنهجية لا تسيطر على الشاشات. مجموعات KPI محدودة عادة بثلاثة مؤشرات. الاستثناء المطلوب حسمه ليس ترتيبًا بصريًا بل تعارض تعريف/قيمة بين الرحلات.

## 4. Terminology Audit

| المفهوم | الاستخدام المتسق | الملاحظة |
|---|---|---|
| تحليل صفقة | «حلّل صفقة» للإجراء، «تحليل صفقة» للوجهة | متسق وظيفيًا |
| Market | «استكشف السوق» للإجراء، «استكشاف السوق» للوجهة | متسق وظيفيًا |
| Comparison | «المقارنة» كوجهة واحدة | متسق |
| العقود | «العقود»/«العقود المسجلة»/«عقود الإيجار» | المعنى واضح؛ يمكن توحيد الصيغة لاحقًا |
| Opportunity Score | Inference داخل المقارنة الحالية | متسق في المعنى |
| Data Sufficiency | «كفاية البيانات» مع نفي صريح لمعادلتها بالثقة | متسق |
| Missing Sale Match | «لا توجد مقارنة بيع مطابقة» | متسق |
| Evidence classes | Raw / Calculated / Estimated / Inference | متسق منهجيًا، تقني لغويًا |
| الفترة | `Q1 2026` و`2026 Q1` | Drift شكلي قابل للتأجيل |
| Data & Methodology | «البيانات والمنهج» في Nav و«البيانات والمنهجية» في الأزرار | Drift تسمية قابل للتأجيل |
| النمو | «سنوي» في Home/Deal و«ربعي» في Market/Comparison | **تعارض جوهري قبل Implementation** |

## 5. Data Semantics Audit

### ما بقي صحيحًا

- مدخلات Deal موسومة `User-provided` ولا تظهر كبيانات رسمية.
- Opportunity Score وDeal signal موسومان `Inference` ولا يقدمان احتمال نجاح.
- العائد `Estimated`، وDSCR وحد الشراء `Calculated`، والعقود `Raw`.
- Data Sufficiency موصوفة كأهلية/كفاية وليست Confidence.
- Forecast لا يظهر كHero KPI أو Primary Insight في Core High-Fi.
- Sales لا تعرض كرقم عند غياب matched coverage؛ تظهر حالة صريحة بدل البديل غير المتكافئ.
- الفترة المفقودة `2025 Q3` لا تتحول إلى صفر، وخط الاتجاه مقطوع عبرها.
- Comparison ترفض المقارنة إذا اختلف التعريف أو الفترة أو الحبة.

### ما يحتاج إصلاحًا

- متوسط إيجار ثليم متعارض في القيمة والتصنيف بين Home/Deal وMarket/Comparison.
- نمو +5.9% متعارض في baseline الزمني بين Home/Deal وMarket/Comparison.
- دقة Score إلى منزلة عشرية مقبولة للترتيب النسبي ما دام السياق واضحًا؛ لا يجوز تحويلها لاحقًا إلى دقة احتمالية أو رسمية.

## 6. Opportunity Score Consistency

**النتيجة: PASS.** في Home وMarket وComparison:

- الدرجة موسومة `Inference`.
- cohort يشير إلى الاستديو والمستوى الجغرافي/المقارنة الحالية.
- اللغة تستخدم «الأعلى ضمن المقارنة الحالية» و«ترتيب داخل المقارنة الحالية» بدل «أفضل السوق».
- المقاييس الرسمية من إيجار وعقود ونمو تسبق الدرجة أو تمتلك وزنًا بصريًا أعلى.
- التعريف المنهجي في Metric Registry ثابت: 40% سيولة، 35% نمو، 25% جاذبية سعر، داخل نفس نوع العقار والمستوى الجغرافي.

في Deal لا يظهر Opportunity Score نفسه كحكم على العقار؛ يظهر Deal signal مستقل `≈23/100` بوصفه Inference داخل سيناريو المدخلات. يجب إبقاء الاسمين والتعريفين منفصلين في التنفيذ.

## 7. Data Sufficiency and States

**النتيجة: PASS.** الحالات الموجودة تفرق بوضوح بين:

- Empty Scope: لا توجد بيانات للنطاق والفترة، مع إجراء تغيير النطاق.
- Insufficient Sample: العينة دون حد الأهلية، مع رابط قواعد الأهلية.
- Missing Sale Match: لا توجد مقارنة بيع متكافئة، ولا يُحقن بديل غير مطابق.
- Missing Growth: «غير متاح» وليس صفرًا، ولا تربط فترات غير متتالية.
- Insufficient Verified Geography: لا markers غير موثقة، مع بديل القائمة.
- Sufficiency ≠ Confidence: توضيح أن العدد/التغطية لا يتحولان إلى نسبة ثقة.

الرسائل المهمة ظاهرة في الصفحة وليست محجوبة في Tooltip. الأنماط تستخدم حدودًا ونصوصًا، ولا تعتمد على اللون وحده.

## 8. Data Visualization Audit

يوجد Chartان فعليان في Phase 5:

| Chart | السؤال | Metric / Unit | Grain / Period | Missing behavior | الحكم |
|---|---|---|---|---|---|
| Market Overview | كيف تغير متوسط الإيجار المجمّع عبر الفترات المرصودة؟ | Weighted average rent / SAR | ربعي؛ 2025 Q1–2026 Q1 | قطع الخط عند 2025 Q3 | PASS |
| Thulaim Segment | كيف تغير متوسط الإيجار المنشور في ثليم؟ | Published average rent / SAR | ربعي؛ نفس الشريحة | قطع الخط عند 2025 Q3 | PASS |

كل Chart يستخدم Series واحدة ولون بيانات واحد، مع وحدة ومحور وفترة واضحة. قطع الخط يمنع إيحاء الاستمرارية عبر الفترة المفقودة. الرسومان يجيبان عن سؤال اتجاهي حقيقي، ولا يكفي KPI واحد لاستبدالهما.

ملاحظة تنفيذية: الرسوم الحالية مركبة كطبقات Screen-level ولا تظهر كـVisualization Container instance. قبل Implementation يجب ربط Default/Loading/Insufficient states بعقد Chart واحد حتى لا تختلف سلوكيات التحميل والنقص عن Phase 2.

## 9. Map Readiness

**Design readiness: PASS.** Map View داخل Market وليست وجهة مستقلة، تحفظ النطاق نفسه، وتوفر عودة واضحة إلى القائمة. الحالة الحالية تقول صراحة إن المواقع غير موثقة ولا تعرض markers.

**Production data readiness: FAIL للـMap فقط.** لا يجوز نقل الإحداثيات التقريبية أو المولدة عشوائيًا إلى الإنتاج. المطلوب Dataset جغرافي موثق، مفتاح ربط ثابت للحي/الموقع، واختبارات تغطية وفشل الربط.

هذا ليس Blocker للمنتج كله. Market List، Segment، Comparison، وDeal قابلة للتنفيذ دون Map markers. إنه **Data Dependency خاص بالـMap**، ويجب إبقاء الخريطة في حالة Insufficient أو خارج الإصدار حتى تكتمل البيانات الموثقة.

## 10. Component and Design System Consistency

**النتيجة: PASS مع Validation تنفيذية لاحقة.** تمت مراجعة **208 Component Instances** عبر Frames الـHigh-Fi الإحدى عشرة ضمن النطاق.

### الأكثر استخدامًا

- Navigation items: ستة عناصر ثابتة في كل Frame رئيسي.
- Shell/App Header وReading Layers: ثابتان عبر الرحلات.
- Metric Card وSection Card: أساس عرض الأدلة والفروق.
- Filter Control: مستخدم في Market فقط، كما تقتضي IA.
- Field: مستخدم في Deal/Comparison inputs، وليس بدل Market filters.
- Data Message: مستخدم لنقص العينة والبيع والنطاق والجغرافيا.
- Badge/Evidence: Raw/Calculated/Estimated/Inference حسب موضعه.
- View Switch: List/Map داخل Market فقط.

### غير المستخدمة في Core High-Fi أو المستخدمة فقط كحالات نظام

- Forecast badge وForecast Error لا يظهران في الرحلات الأساسية، وهو صحيح لأن Forecast ليس Primary KPI.
- حالات Hover/Focus/Disabled/Error موجودة في Phase 2 لكنها لا تظهر كلها في الـstatic candidates.
- Visualization Loading لم تُعرض داخل Core High-Fi.

### الاتساق المرصود

- `get_variable_defs` على Home وDeal Result وMarket Overview وComparison Result أكد استخدام Semantic Variables، Text Styles، وEffect Styles المشتركة.
- الخط المرصود في الأنماط المشتركة Cairo بأوزان Regular/SemiBold/Bold فقط.
- RTL ثابت بصريًا، والـ4px spacing rhythm واضح في القيم 4/8/12/16/20/24/32/48.
- Button hierarchy واضح: Primary للمهمة الأساسية وSecondary للاستكشاف/التعديل/العودة.
- لا توجد broken instances أو overlaps ظاهرة في الصور المراجعة.

### Workaround المرصود

- Charts مرسومة كطبقات محلية داخل Market بدل Instance صريح من Visualization Container. هذا لا يفسد المرشح، لكنه يحتاج عقد تطبيق موحد قبل الإنتاج.

لا يمكن من screenshot/metadata وحدهما إثبات صفر direct fills أو صفر unstyled text لكل descendant؛ يلزم فحص تصديري/برمجي شامل قبل Implementation. لا توجد إشارة بصرية إلى انحراف، وPhase 1/2 المجمدتان تبقيان مرجع النظام.

## 11. Navigation and IA Consistency

**النتيجة: PASS.** الترتيب ثابت عبر الشاشات:

1. الرئيسية
2. تحليل صفقة
3. استكشاف السوق
4. المقارنة
5. التقارير
6. البيانات والمنهج

الخريطة View داخل Market، التقارير وجهة واحدة، والمقارنة أداة واحدة. Market filters منفصلة عن Deal inputs. لا يوجد دليل على أن Role يغير أسماء التنقل.

الانحراف الوحيد في الاسم هو اختصار Nav إلى «البيانات والمنهج» مقابل «البيانات والمنهجية» في الأزرار والـIA. لا يسبب ضياعًا حاليًا، لكنه يستحق توحيدًا لاحقًا.

## 12. Responsive Readiness

**النتيجة: READY للتخصيص أثناء Responsive Implementation، دون إعادة بناء IA.** البنية الحالية قابلة للتحويل لأن كل رحلة مقسمة إلى أقسام مستقلة، والتنقل ثابت، والخريطة لها بديل قائمة.

### Must solve before implementation

- تعريف ترتيب stacking في Comparison: بديل A → الفارق → بديل B، مع إبقاء التعريف والفترة مرئيين.
- تحديد أولويات أعمدة Market List بدل تصغير الجدول كاملًا.
- تثبيت ترتيب Decision → Reasons → Market Evidence → Sufficiency في Deal mobile.

### Can solve during responsive implementation

- تحويل KPI groups من ثلاثة أعمدة إلى عمود/صف قابل للتمرير المنضبط.
- إعادة تدفق الفلاتر إلى صفوف مع Scope summary ثابت.
- ضبط ارتفاع Charts وعناوين المحاور على الشاشات الضيقة.
- نقل List/Map toggle إلى موضع قريب من عنوان العرض.

## 13. Accessibility Readiness

**Heuristic result: PASS مع Validation Needed.** العناوين واضحة، نصوص الحالات لا تعتمد على اللون، الحقول لها labels، الحد الأدنى المرصود للأزرار/الفلاتر 44px، والـRTL متسق. Phase 2 يتضمن Focus states.

لا يدعي هذا التقرير WCAG compliance. يجب أثناء Implementation اختبار:

- contrast على القيم الفعلية وفي حالات hover/focus/disabled.
- ترتيب keyboard وfocus visibility.
- Screen reader names ووصف Charts والحالات.
- اتجاه قراءة النصوص المختلطة عربي/إنجليزي/أرقام.
- touch targets الفعلية بعد الاستجابة.
- عدم الاعتماد على موضع اليمين/اليسار وحده في Comparison.

## 14. Supporting Destinations

### Reports — Recommendation B

يمكن بناء Reports لاحقًا باستخدام الأنماط والمكونات الحالية. Low-Fi يحدد مركزًا واحدًا وثلاثة أنواع مخرجات، ثم Setup يوضح النطاق والمحتوى والإجراء. لا توجد مشكلة قرار أو تنقل تحتاج High-Fidelity مستقلة قبل بدء Core Implementation، بشرط ألا تتحول Reports إلى مولد جديد أو Feature إضافية خارج القدرات الحالية.

### Data & Methodology — Recommendation A

تحتاج High-Fidelity مستقلة قبل Implementation. هذه الوجهة هي نهاية الثقة المشتركة التي ترتبط بها الشاشات الأربع، ويجب أن تحسم تعريف متوسط الإيجار، الفترة، الحبة، الأهلية، cohort، التغطية، المصدر، وقيود البيع/التوقع. التناقضان الرئيسيان في هذه البوابة يثبتان أن ترك هذه الوجهة إلى ما بعد التنفيذ سيضاعف احتمالات drift.

المطلوب ليس توسيع Feature؛ بل تحويل Low-Fi الحالي إلى مرجع تنفيذ واحد لتعريف المؤشرات والمصادر والقيود.

## 15. Prototype Readiness

**الحكم: READY.** يمكن بناء Prototype للاختبار دون Phase 7 أو شاشات جديدة.

### Flow A — Home → Deal → Result

| الخطوة | Node | Interaction | Context |
|---|---|---|---|
| Home | `21:3` | «حلّل صفقة» → Deal Input | الدور + نطاق افتراضي اختياري |
| Deal Input | `40:3` | تعبئة الحقول + «حلّل الصفقة» | المدينة، الحي، النوع، السعر، المساحة، الافتراضات |
| Deal Result | `40:4` | «تحرير بيانات الصفقة» → Input | جميع المدخلات كما هي |
| Deal Result | `40:4` | «البيانات والمنهجية» | metric/source context |

### Flow B — Home → Market → Segment → Comparison

| الخطوة | Node | Interaction | Context |
|---|---|---|---|
| Home | `21:3` | «استكشف السوق» → Market Overview | المدينة، النوع، الفترة |
| Market Overview | `58:39` | List/Map switch | نفس Scope |
| Market List | `58:108` | اختيار ثليم → Segment | الحي + Scope |
| Map | `58:177` | «عرض القائمة» | نفس Scope، بلا markers غير موثقة |
| Segment | `58:246` | «مقارنة بدائل متكافئة» → Selection | ثليم كبديل أول + Scope |
| Comparison Selection | `63:3` | اختيار البديل الثاني + «قارن البدائل» | البديلان + تعريف/نوع/فترة/حبة |
| Comparison Result | `63:72` | «تعديل البدائل» → Selection | البديلان كما هما |

### Prototype gaps

- تحديد hotspot واضح على صف Market List أو Action ثابت لفتح Segment.
- تحديد Action مقارنة لا يعتمد فقط على Missing Sale state.
- توثيق back behavior وحفظ Scope عبر List/Map/Segment/Comparison.
- ربط «البيانات والمنهجية» بوجهة مؤقتة واضحة؛ يفضل High-Fi المستقلة قبل Implementation، لكن غيابها لا يمنع اختبار Core task flow.

## 16. Implementation Readiness

### يمكن تطبيقه الآن في Streamlit بعد إغلاق P1

- Global shell والتنقل والـScope header.
- Home hierarchy وCTA split.
- Deal input/result hierarchy وفصل User input عن Market evidence.
- Market overview/list/segment دون markers.
- Comparison selection/result وحالات عدم الأهلية.
- Data messages وEvidence badges.

### يحتاج Data work أولًا

- Map markers: verified geography فقط.
- Sales metrics: matched coverage مؤهل فقط.
- Forecast: لا يُرقى إلى Primary output؛ يحتاج جودة backtest أفضل أو إفصاحًا صارمًا كسيناريو.

### يحتاج Interaction specification

- نقل Scope بين Home/Market/Segment/Comparison.
- حفظ Deal inputs عند التعديل والعودة.
- اختيار/إزالة بدائل المقارنة وقواعد التكافؤ.
- حالات loading/error/empty لكل عملية فعلية.

### يحتاج Responsive specification

- comparison bands، Market list columns، filter wrapping، chart labeling، وDeal result stacking.

### يجب ألا ينتقل للإنتاج بعد

- قيمة/تصنيف 28,400 لثليم قبل المصالحة مع 10,295.
- وصف +5.9% كنمو سنوي.
- أي Map marker من إحداثيات تقريبية أو عشوائية.
- Sales output خارج matched coverage.
- Forecast بصيغة يقين أو KPI أساسي؛ نتائج التدقيق الحالية تسجل MAPE يقارب 18.989% للإيجار و45.383% للطلب.

## 17. Findings Register

كل Finding أدناه يحمل تصنيفًا واحدًا فقط.

### P0 — Blocker (0)

لا يوجد Finding يمنع بناء Prototype آمن للرحلات الأساسية.

### P1 — Must Fix Before Implementation (4)

#### P1-01 — Metric value/classification drift: Thulaim average rent

Home وDeal يعرضان 28,400 ر.س `Calculated`، بينما Market Segment وComparison يعرضان 10,295 ر.س `Raw published aggregate` للنطاق الظاهر نفسه: الرياض · ثليم · استديو · 2026 Q1. يجب تحديد ما إذا كانا مقياسين مختلفين وإظهار الاسم/grain لكل منهما، أو توحيد القيمة والتصنيف.

#### P1-02 — Period baseline drift: +5.9%

Home وDeal يسميان +5.9% نموًا سنويًا/مقارنة سنوية، بينما Market وComparison يعرفانه كتغير ربعي من 2025 Q4 إلى 2026 Q1. Metric Registry يسمح بربعين متتاليين فقط ويقول صراحة إنه ليس نموًا سنويًا رسميًا.

#### P1-03 — Market-to-Comparison interaction/context contract

الوجهة موجودة ومتسقة، لكن Trigger السياقي العام واختيار البدائل المنقول من Market غير محددين بما يكفي. يجب تثبيت hotspot/action، نفس النوع والفترة والحبة، وسلوك الرجوع قبل كتابة الواجهة.

#### P1-04 — Chart state/component contract

Charts الحالية سليمة بصريًا، لكنها screen-level compositions. يجب قبل التنفيذ ربطها بعقد Phase 2 للـDefault/Loading/Insufficient، وتحديد التعامل مع missing periods ووصف بديل لغير المبصرين.

### P2 — Can Defer (3)

#### P2-01 — Data & Methodology naming drift

التنقل يستخدم «البيانات والمنهج»، بينما الأزرار والـIA تستخدم «البيانات والمنهجية». لا يمنع الفهم، ويمكن توحيده في Content pass لاحق.

#### P2-02 — Quarter label formatting

تظهر الفترة بصيغتي `Q1 2026` و`2026 Q1`. المعنى واحد، لكن توحيد اتجاه وترتيب العرض سيحسن قراءة RTL.

#### P2-03 — Technical evidence labels dominate some supporting copy

Raw/Calculated/Estimated/Inference ثابتة ومفيدة للحوكمة، لكن يمكن لاحقًا إضافة مقابل عربي أو شرح مختصر دون إزالة الاسم المعتمد، خصوصًا للمستخدم لأول مرة.

### Data Dependency (3)

#### DD-01 — Verified geography for Map

الإحداثيات الحالية التقريبية/العشوائية لا تصلح للإنتاج. Blocker للـMap markers فقط، وليس للمنتج كله.

#### DD-02 — Matched sales coverage

مخرجات التدقيق الحالية تغطي مدينة واحدة وثلاثة أحياء ونوع عقار واحد في بيانات البيع. يجب إبقاء Missing Sale Match خارج هذا التطابق.

#### DD-03 — Forecast validation quality

الاختبار الرجعي عالي الخطأ، خصوصًا الطلب. Forecast يبقى سيناريو ثانويًا ولا ينتقل كKPI أو ادعاء تنبؤي قبل تحسن الدليل.

### Validation Needed (5)

#### VN-01 — First-Visit user test

النتيجة الحالية Heuristic؛ يلزم اختبار فعلي لمهام فهم المنتج واختيار المسار الأول.

#### VN-02 — Prototype usability and context retention

يلزم اختبار أن المستخدم يلاحظ الانتقال ويحافظ على Scope والمدخلات والبدائل عند العودة.

#### VN-03 — Responsive behavior

يلزم اختبار Desktop→Tablet→Mobile فعلي للمقارنة والجداول والفلاتر والرسوم وDeal result.

#### VN-04 — Accessibility implementation

يلزم contrast/keyboard/focus/screen reader/touch testing؛ لا يمكن إثبات WCAG من Figma وحده.

#### VN-05 — Exhaustive design-token and instance integrity

يلزم فحص برمجي شامل قبل التسليم للتطوير للتأكد من عدم وجود direct/unbound colors أو unstyled text أو broken instances في جميع descendants، وليس العينات الأربع فقط.

## 18. Top Five Remaining Risks

1. **Metric trust risk:** اختلاف 28,400 عن 10,295 وتصنيفهما قد يجعل المستخدم يقرأ مقياسين كأنهما رقم واحد.
2. **Time-baseline risk:** وصف +5.9% كرقم سنوي وربعي في آن واحد يغير معنى القرار.
3. **Map integrity risk:** أي marker غير موثق سيحوّل حالة صادقة حاليًا إلى دقة زائفة.
4. **Journey handoff risk:** غموض نقل Scope والبدائل من Market إلى Comparison قد ينتج مقارنة غير متكافئة أو فقدان سياق.
5. **Implementation validation risk:** الاستجابة، الوصول، والـtoken/instance integrity لم تُختبر في تطبيق فعلي بعد.

## 19. Recommended Next Step

1. بناء Prototype فقط على Nodes المحددة أعلاه، دون بدء Phase 7 أو Implementation.
2. إجراء Prototype test لمساري Deal وMarket→Comparison مع قياس first click، فهم Scope، وفهم الفرق بين البيانات الرسمية والاستدلال.
3. بالتوازي قبل Implementation، إغلاق P1-01 وP1-02 عبر Metric Registry/Data & Methodology كمصدر حقيقة واحد.
4. تحويل Data & Methodology إلى High-Fidelity مستقلة قبل Implementation؛ إبقاء Reports ضمن Recommendation B.
5. بعد نجاح الاختبار وإغلاق P1، إجراء Implementation Readiness re-check قصير يشمل tokens، accessibility، responsive، وحواجز Map/Sales/Forecast.

## Final Gate Decision

**CONDITIONAL PASS**

الرحلات الأساسية متماسكة بما يكفي لبناء Prototype، ولا توجد P0. لا تبدأ Implementation بالقيم والنصوص الحالية قبل إصلاح P1 الأربعة، ولا تُعامل الخريطة أو البيع أو التوقع كقدرات Production-ready خارج حواجز البيانات الموثقة.

# Qareena — Prototype Click Defect Investigation #2

التاريخ: 2026-09-05  
النطاق: Core Interactive Prototype في Figma فقط  
الحالة: **FIX IMPLEMENTED — AWAITING USER RE-TEST**

## سياق التحقيق

أُعيد فتح UT-02 بعد أن أعاد المستخدم إنتاج سلوك النقر الخاطئ في Figma Present. اختبار المستخدم الفعلي هو مصدر الحقيقة؛ لذلك لا تُسجل هذه الوثيقة UT-02 بوصفها مغلقة.

تم فحص الـPrototype الفعلي على الصفحة `69:2`، ونقطة البداية `21:3`، والـFlow المسمى `Qareena — Core Prototype`. كان عدد التفاعلات الفعلي 18.

## السبب الجذري

لم تكن وجهات Navigation المخزنة خاطئة، ولم توجد Reactions موروثة من Components أو Variants، ولم توجد تفاعلات Parent وChild متزامنة، ولم تتداخل صناديق التفاعلات الثمانية عشر مع بعضها.

السبب هو **عدم تطابق مالك النقرة الهندسي مع CTA المرئي** في أربعة مواضع:

1. صف ثليم `59:380` كان مالكًا للتفاعل بكامل عرضه `1136×72` رغم أن CTA الدلالي هو اسم `ثليم`.
2. إجراء تغيير النطاق `I58:249;17:30` كان Reaction على Text child داخل App Header instance.
3. إجراء المقارنة `I60:398;17:138` كان Reaction على Text child عرضه الفعلي `552×20`، أكبر كثيرًا من العبارة الخضراء المرئية.
4. إجراء تعديل البدائل `I63:75;17:30` كان Reaction على Text child داخل App Header instance.

في Figma Present تُحتسب النقرة بحسب Bounding Box لطبقة مالك التفاعل، لا بحسب حدود الحروف المرئية. لذلك كان الضغط على مساحة تبدو مجاورة يفعّل Action صحيحًا لطبقة لم يقصدها المستخدم، فيظهر السلوك كأنه زر أو وجهة مختلفة.

## قرار الإصلاح

أُزيلت Reactions الثماني عشرة السابقة وأُعيد بناء wiring كاملًا باستخدام 18 طبقة `Prototype Hotspot` شفافة، علوية، وذات `layoutPositioning=ABSOLUTE`. كل Hotspot داخل Frame الشاشة نفسها ومقيد بحدود العنصر المرئي المقصود.

لم تُغيّر أي وجهة، أو IA، أو Component، أو نص، أو قيمة.

## Interaction Inventory — قبل وبعد

| الشاشة | CTA المرئي | المالك قبل | Bounds قبل | المالك بعد | Bounds بعد | الوجهة/السلوك |
|---|---|---|---|---|---|---|
| Home | استكشف السوق | `25:19` Instance | 160×44 | `96:440` | 160×44 | `58:39` |
| Home | حلّل صفقة | `25:17` Instance | 160×44 | `96:442` | 160×44 | `40:3` |
| Deal Input | حلّل الصفقة | `40:190` Instance | 160×44 | `96:444` | 160×44 | `40:4` |
| Deal Result | تعديل بيانات الصفقة | `40:251` Instance | 190×44 | `96:446` | 190×44 | Back |
| Market Overview | خريطة | `59:300` Instance | 120×44 | `96:448` | 120×44 | `58:177` |
| Market Overview | قائمة | `59:302` Instance | 120×44 | `96:450` | 120×44 | `58:108` |
| Market List | خريطة | `59:372` Instance | 120×44 | `96:452` | 120×44 | `58:177` |
| Market List | ثليم | `59:380` Frame | 1136×72 | `96:454` | 120×44 | `58:246` |
| Market List | استكشاف السوق | `58:158` Instance | 192×44 | `96:456` | 192×44 | `58:39` |
| Market Map | قائمة | `60:132` Instance | 120×44 | `96:458` | 120×44 | `58:108` |
| Market Map | عرض القائمة | `60:142` Instance | 160×44 | `96:460` | 160×44 | `58:108` |
| Thulaim Segment | تغيير النطاق | `I58:249;17:30` Text child | 70×20 | `96:462` | 120×44 | `58:108` |
| Thulaim Segment | مقارنة بدائل متكافئة | `I60:398;17:138` Text child | 552×20 | `96:464` | 200×44 | `63:3` |
| Comparison Selection | إلغاء | `63:575` Instance | 160×44 | `96:466` | 160×44 | Back |
| Comparison Selection | قارن البدائل | `63:577` Instance | 160×44 | `96:468` | 160×44 | `63:72` |
| Comparison Selection | استكشاف السوق | `63:53` Instance | 192×44 | `96:470` | 192×44 | `58:246` |
| Comparison Result | تعديل البدائل | `I63:75;17:30` Text child | 76×20 | `96:472` | 140×44 | Back |
| Comparison Result | استكشاف السوق | `63:122` Instance | 192×44 | `96:474` | 192×44 | `58:246` |

كل Hotspot هو child مباشر في Frame الشاشة، ومضاف بعد عناصر العرض ليكون أعلى منها في z-order. تعبئته شفافة تمامًا ولا يضيف أثرًا مرئيًا.

## Parent / Inherited / Nested Audit

- Parent interactions التي تغطي عدة CTAs: لا توجد بعد الإصلاح.
- Reactions موروثة من Main Components أو Variants: 0.
- Parent + Child reactions متزامنة: 0.
- Nested interactive elements: 0.
- Reactions قديمة متبقية: 0.
- Hotspot overlaps: 0.
- طبقات Prototype التفاعلية الحالية: 18، وجميعها Rectangles مسماة `Prototype Hotspot · …`.

## Click-Isolation Checks

تم فحص كل Hotspot في ثلاث فئات:

1. مركز CTA: يطابق مالك تفاعل واحدًا فقط — **18/18 PASS**.
2. نقطتان أفقيتان ونقطتان رأسيّتان مباشرة خارج الحد: لا تفعّل أي Hotspot — **72/72 PASS**.
3. النصوص والعناصر المجاورة: لا تقع مراكزها داخل Hotspot غير مقصود — **PASS**.

نتيجة عيوب ملكية النقرة: **4 → 0**.  
نتيجة أخطاء تعريف الوجهة نفسها: **0 → 0**.

## Journey Regression

### Journey A

Home → Deal Input → Deal Result → تعديل بيانات الصفقة/Back: **PASS**.

### Journey B

Home → Market Overview → Market List → ثليم → Comparison Selection → Comparison Result → Back/Market context: **PASS**.

### List / Map

Market List → Map → List وMarket Overview → List/Map: **PASS**. بقيت الخريطة بحالة عدم توفر مواقع موثقة.

## Regression Protection

- التفاعلات: **18 → 18**.
- النصوص الإنجليزية المرئية: 0.
- التغييرات النصية في هذه المهمة: 0.
- التغييرات البصرية: 0؛ أضيفت طبقات Prototype شفافة فقط.
- Broken instances: 0.
- Unbound visible colors: 0.
- Unstyled text: 0.
- Cairo فقط: Regular / SemiBold / Bold.
- `20,255`: محفوظ.
- ثليم `10,295 ر.س`: محفوظ.
- `+5.9%` والفترة الربعية: محفوظان.
- ثليم `84.5` والمرقب `83.7`: محفوظان.
- قيد البيع والخريطة والفترة المفقودة: محفوظ.
- Design System drift: 0 — 68 Variables، 10 Text Styles، 4 Effect Styles، 2 Grid Styles.
- Code/CSS/data/Metric Registry/analytics: لم تتغير.
- Low-Fi: لم يتغير.
- Commit/push: لم يُنفذ.

## القرار

الإصلاح منفذ واجتاز الفحص البنيوي واختبارات عزل النقرة. لا يُسجل UT-02 بوصفه CLOSED حتى يعيد المستخدم الاختبار بنفسه في Figma Present.

**FIX IMPLEMENTED — AWAITING USER RE-TEST**

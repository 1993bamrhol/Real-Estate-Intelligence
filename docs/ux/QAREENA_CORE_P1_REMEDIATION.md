# Qareena — Core High-Fidelity P1 Targeted Remediation

**التاريخ:** 2026-09-05  
**مصدر الحقيقة:** `docs/ux/QAREENA_CORE_P1_ROOT_CAUSE.md`  
**النطاق:** Home، Deal Analysis، Market Exploration، Comparison فقط  
**القرار النهائي:** **PASS — PROTOTYPE READY**

## 1. النتيجة التنفيذية

أُغلقت P1 الأربعة من خلال تعديلات محدودة على الـHigh-Fi والـspecification داخل Figma، دون تعديل البيانات أو Metric Registry أو Analytics أو كود المنتج، ودون إنشاء Prototype.

- فصلت Home بين مؤشرات السوق العامة وفرص الأحياء: الـHeader ومجموعة KPI يستخدمان نطاق `الرياض · كل الأحياء · استديو · 2026 Q1`، بينما Opportunity cards تصرح بأنها cohort أحياء الرياض/استديو/2026 Q1.
- استبدلت مؤشرات Home المختلطة بالقيم المحكومة لنطاق المدينة: `20,255 ر.س` متوسطًا مرجحًا، `11,713` عقدًا، و`+0.2%` تغيرًا ربعيًا.
- صححت Deal للنطاق الصريح `الرياض · ثليم · استديو · 2026 Q1`: `10,295 ر.س — Raw` و`+5.9% — Calculated — 2025 Q4 → 2026 Q1`.
- صححت Opportunity Score للمرقب من `83.9` إلى `83.7` مع بقاء Inference وداخل المقارنة الحالية.
- خُففت سلطة Deal inference لأن مدخلات السيناريو الكاملة غير ظاهرة؛ لم يُختلق أي input ولم يتغير الحساب.
- وُثق عقد Market → Comparison في Annotations والنسخ الظاهرة، بما في ذلك payload والأهلية وحفظ السياق وسلوك الإلغاء.
- رُبط الرسمان بعقد Visualization Container الحالي وحالات Default/Loading/Insufficient، مع الحفاظ على فجوة 2025 Q3 وإضافة شرط fallback من نفس data payload.

## 2. Gate outcome

| البند | قبل | بعد |
|---|---:|---:|
| P0 | 0 | 0 |
| P1 | 4 | 0 |
| P2 | 3 | 3 |
| Data Dependencies | 3 | 3 |
| Validation Needed | 5 | 5 |
| Core Gate | CONDITIONAL PASS | **PASS — PROTOTYPE READY** |

انخفاض P1 لا يعني أن Data Dependencies أو اختبارات المستخدم/الاستجابة/الوصول أُنجزت. تم إغلاق VN-05 الخاص بسلامة الـtokens والـinstances بفحص برمجي شامل، وأضيف بدلًا منه تحقق Deal scenario reproducibility الذي لا يمكن إغلاقه من Candidate ذي المدخلات الرمزية.

## 3. P1 closure

### P1-1 — Rent Binding: CLOSED

**Home market scope**

- Scope: `الرياض · كل الأحياء · استديو · 2026 Q1`
- Rent: `20,255 ر.س`
- Classification: `Calculated`
- Aggregation: `مرجّح بالعقود`
- Contracts: `11,713 — Raw`

**Deal/Thulaim segment scope**

- Scope: `الرياض · ثليم · استديو · 2026 Q1`
- Rent: `10,295 ر.س`
- Classification: `Raw`
- Label: `متوسط الإيجار المنشور`

لم يعد `28,400` ظاهرًا في أي Core High-Fi. الاختلاف بين `20,255` و`10,295` اختلاف صالح وواضح في geography/aggregation، وليس drift.

### P1-2 — Growth Semantics: CLOSED

- Home العام: `+0.2% — التغير الربعي — Calculated — 2025 Q4 → 2026 Q1`.
- Deal/Market Segment لثليم: `+5.9% — التغير الربعي — Calculated — 2025 Q4 → 2026 Q1`.
- Comparison: بقي تعريف QoQ الصحيح كما هو.
- لا يوجد أي ظهور لـ«سنوي» أو `YoY` مرتبط بهذه القيمة داخل Core High-Fi بعد المعالجة.

لم يتغير الحساب؛ تغيرت القيمة في Home لأن نطاق Home المعتمد هو city aggregate لا ثليم.

### P1-3 — Market → Comparison Contract: CLOSED

**المسار الموثق**

`Market Exploration → مراجعة ثليم → مقارنة بدائل متكافئة → Comparison Selection`

**Trigger**

- صف ثليم `59:380` يفتح Segment مع الحفاظ على scope.
- Action الموجودة داخل `60:398` هي trigger المقارنة إلى `63:3`.

**Context payload**

- `city=Riyadh`
- `propertyType=Studio`
- `period=2026 Q1`
- `geographicLevel=District`
- `selectedSegment=Thulaim`
- `opportunityCohort=Riyadh districts / Studio`

**Eligibility contract**

البديل الثاني يجب أن يطابق نوع العقار، المستوى الجغرافي، الفترة القابلة للمقارنة، grain، ومتطلبات cohort عند عرض Opportunity Score. عند الفشل تستخدم حالة عدم الأهلية الحالية. البديل الأول مثبّت من Market، والإلغاء يعيد إلى المصدر مع الحفاظ على payload.

لم تُنشأ interactions أو Prototype؛ تم توثيق specification فقط.

### P1-4 — Chart Contract: CLOSED

الرسمان الحاليان موسومان كحالة:

- `Visualization Container · Kind=Chart · State=Default · Riyadh rent trend`
- `Visualization Container · Kind=Chart · State=Default · Thulaim rent trend`

مصدر العقد هو Component Set `17:176`:

- Default: `17:152`
- Loading: `17:156`
- Insufficient: `17:160`

الفترة `2025 Q3` بقيت `غير متاح`، والخط مقطوع قبلها وبعدها، ولا توجد interpolation أو قيمة مخترعة. وتحدد الـAnnotation أن البديل القابل للوصول يجب أن يعرض الفترات والقيم المرصودة نفسها كنص أو جدول مختصر من data payload نفسه.

لم تُعدّل Component definitions ولم يُنشأ Chart System جديد.

## 4. Opportunity and Deal inference

### Opportunity Score

- ثليم: `84.5 — Inference`.
- المرقب: `83.7 — Inference` في Home وMarket وComparison.
- السياق: cohort أحياء الرياض/استديو، وداخل المقارنة الحالية.
- لغة Comparison تبقي الفارق `0.8` نقطة استدلالية ولا تعلن فائزًا مطلقًا.

**النتيجة:** CONSISTENT.

### Deal inference

القيمة `≈23/100` بقيت كما هي، لكنها أصبحت محاطة بنص واضح:

- `نتيجة توضيحية — لا تعتمد قبل استكمال مدخلات الصفقة.`
- `السيناريو غير مكتمل العرض؛ راجع السعر والتمويل والمصروفات قبل اتخاذ قرار.`
- `مدخلات ظاهرة فقط` و`غير نهائية` بجوار إشارة Inference.

توضح الـAnnotation أن مدخلات التمويل والمصروفات اللازمة لإعادة الحساب غير معروضة، وأن الإشارة ليست توصية.

**النتيجة:** `UNVERIFIABLE — CLAIM SAFELY CONSTRAINED`. لا يوجد تعارض Cross-Screen، لكن إعادة إنتاج الرقم تبقى Validation Needed عند توفر scenario payload كامل.

## 5. Cross-Screen Metric Re-Gate

| Metric | النتيجة بعد المعالجة | الحكم |
|---|---|---|
| Rent | Home تعرض city weighted aggregate؛ Deal/Segment/Comparison تعرض published segment value مع scope صريح | VALID DIFFERENCE — CONTEXT CLEAR |
| Contracts | `11,713` للمدينة و`437` لثليم و`536` للمرقب، وكل نطاق ظاهر | VALID DIFFERENCE — CONTEXT CLEAR |
| Growth | `+0.2%` للمدينة و`+5.9%` لثليم و`+4.2%` للمرقب؛ كلها QoQ وبفترتين ظاهرتين | VALID DIFFERENCE — CONTEXT CLEAR |
| Opportunity Score | `84.5` و`83.7` متسقتان، Inference وداخل cohort نفسه | CONSISTENT |
| Deal inference | غير قابل لإعادة الإنتاج من الشاشة، لكن claim أصبح غير نهائي ومقيدًا | UNVERIFIABLE — CLAIM CONSTRAINED |
| Data Sufficiency | ما زالت منفصلة صراحةً عن Confidence | CONSISTENT |
| Sale coverage | لا تعرض Sales indicator خارج matched coverage | CONSISTENT |

**التعارضات المتبقية:** 0  
**Valid differences ذات السياق غير الواضح:** 0

## 6. Nodes changed

**27 عقدة فريدة:**

- Home: `24:8`, `27:17`, `27:21`, `27:25`, `28:30`, `28:25`, `22:6`, `28:26`
- Deal: `40:273`, `40:281`, `40:242`, `40:243`, `40:248`, `40:250`, `40:245`
- Market → Comparison contract: `59:380`, `60:398`, `63:555`, `63:561`, `63:567`, `63:573`, `63:575`, `63:577`
- Chart contract: `59:279`, `59:295`, `60:366`, `60:382`

لا تعني القائمة أن كل عقدة تغيرت بصريًا؛ بعض العقد تلقت names/annotations توثيقية فقط.

## 7. QA results

تم فحص **573 عقدة** عبر 11 Core High-Fi frame:

- Home: `21:3`
- Deal: `40:3`, `40:4`
- Market: `58:39`, `58:108`, `58:177`, `58:246`, `58:315`
- Comparison: `63:3`, `63:72`, `63:141`

| الفحص | النتيجة |
|---|---:|
| Component Instances | 208 |
| Broken instances | 0 |
| Direct/unbound visible colors | 0 |
| Unstyled text | 0 |
| Non-Cairo text segments | 0 |
| `28,400` occurrences | 0 |
| Annual/YoY labels في Core High-Fi | 0 |
| `83.9` occurrences | 0 |
| Overlap/clipping في الصور المراجعة | 0 مرصود |
| RTL | PASS |
| Data Sufficiency ≠ Confidence | PASS |
| Missing period discontinuity | PASS |

تمت مراجعة صور Home وDeal Result وMarket Segment وComparison Selection وComparison Result بعد التغيير. لا يعتبر ذلك User Test أو WCAG audit.

## 8. Design System and frozen assets

### Design System snapshot

| الأصل | قبل المعالجة | بعد المعالجة | Drift |
|---|---:|---:|---:|
| Variables | 68 | 68 | 0 |
| Text Styles | 10 | 10 | 0 |
| Effect Styles | 4 | 4 | 0 |
| Grid Styles | 2 | 2 | 0 |
| Components/variants created | 0 | 0 | 0 |

أوزان النص المرصودة بقيت Cairo Regular/SemiBold/Bold، واستخدمت التعديلات Component properties والأنماط والـvariables الحالية.

### Frozen assets

- Low-Fi structure: unchanged
- Phase 1 Foundation: unchanged
- Phase 2 Component definitions: unchanged
- IA and navigation names: unchanged
- Reports: unchanged
- Data & Methodology: unchanged
- Prototype interactions: not created

## 9. Code/CSS/data status

- لم تُعدّل البيانات.
- لم يُعدّل Metric Registry أو Analytics.
- لم يُعدّل `app.py` أو CSS أو أي production code.
- لم يُنفذ commit أو push.
- التغييرات المحلية الموجودة مسبقًا في worktree لم تُلمس؛ الملف المحلي الوحيد المنشأ في هذه المهمة هو تقرير remediation هذا.

## 10. Remaining findings

### P0 — 0

لا يوجد Blocker للـPrototype.

### P1 — 0

P1-1 وP1-2 وP1-3 وP1-4 مغلقة وفق Acceptance Criteria.

### P2 — 3

1. تسمية «البيانات والمنهج» مقابل «البيانات والمنهجية».
2. تنسيق `Q1 2026` مقابل `2026 Q1`.
3. ثقل Evidence labels التقنية في بعض النصوص المساندة.

### Data Dependencies — 3

1. Verified geography للـMap markers.
2. Matched sales coverage.
3. Forecast validation quality.

### Validation Needed — 5

1. First-Visit user test الحقيقي.
2. Prototype usability وcontext retention.
3. Responsive behavior.
4. Accessibility implementation: contrast/keyboard/focus/screen reader/touch.
5. Deal scenario reproducibility بمدخلات السعر والتمويل والمصروفات الكاملة.

تم إغلاق التحقق السابق الخاص بسلامة الـtokens والـinstances: الفحص الشامل أعطى صفر broken instances وصفر direct/unbound visible colors وصفر unstyled text.

## 11. Core High-Fi Re-Gate Decision

**PASS — PROTOTYPE READY**

المبررات:

- P0=0 وP1=0.
- التعارضات الدلالية العابرة للشاشات أصبحت صفرًا.
- عقود Market → Comparison وVisualization موثقة دون توسيع Feature scope.
- Design System drift يساوي صفرًا.
- Data Dependencies الثلاثة ما تزال محمية بحالات النقص ولا تمنع اختبار الرحلات الأساسية.
- Deal inference لم يتحول إلى حقيقة؛ أصبح claim محدودًا بوضوح إلى أن تتوفر مدخلات قابلة لإعادة الإنتاج.

لا يبدأ Prototype قبل اعتماد هذه النتيجة.

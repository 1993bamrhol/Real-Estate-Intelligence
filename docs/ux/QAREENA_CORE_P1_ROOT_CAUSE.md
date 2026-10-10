# Qareena — Core High-Fidelity P1 Root-Cause Audit

**التاريخ:** 2026-09-05  
**النطاق:** تحقيق Read-Only في P1 الأربعة الناتجة عن Core High-Fidelity Gate  
**القرار:** `READY FOR TARGETED REMEDIATION`

## 1. الخلاصة التنفيذية

التحقيق لا يثبت وجود خطأ في بيانات الإيجار أو في حساب النمو الحالي. مصدر التعارض هو نقل قيم وتسميات إلى بعض شاشات High-Fi من دون ربطها الكامل بسياق المقياس المعتمد:

- القيمة `10,294.91` (المعروضة `10,295 ر.س`) هي **Raw** المنشورة لثليم، استوديو، سكني، 2026 Q1، وبعدد 437 عقدًا.
- القيمة `28,400 ر.س` لا يمكن إعادة إنتاجها لثليم من البيانات الحالية، ولا من تجميع صالح للنطاق الظاهر، ولا تظهر في الكود أو Metric Registry أو مخرجات التدقيق. ظهورها في Home ثم Deal هو **قيمة تصميم stale/placeholder غير موثقة**، وليس تعريفًا بديلًا صحيحًا للمقياس.
- `+5.9%` هو **تغير ربعي QoQ** محسوب بين 2025 Q4 و2026 Q1. الرقم صحيح، بينما وصفه في Home وDeal بأنه «نمو سنوي» غير صحيح.
- لا يتطلب أي P1 تعديل البيانات أو الحسابات، ولا إعادة فتح Metric Governance. المطلوب لاحقًا هو remediation محدود في binding/content/context، إضافة إلى إغلاق عقدتي interaction وchart-state الموجودتين أصلًا في IA وPhase 2.

## 2. مصادر التحقيق وطريقته

تمت المطابقة بين:

- `src/real_estate_intel/metric_registry.py`
- `src/real_estate_intel/data_prep.py`
- `src/real_estate_intel/analytics.py`
- `src/real_estate_intel/underwriting.py`
- `tests/test_metric_governance.py`
- `data/processed/rental_market.csv.gz`
- `data/processed/sale_market.csv.gz`
- `outputs/kpi_data_audit_after.json` ومخرجات المقارنة السابقة
- `docs/ux/QAREENA_CORE_HIGH_FI_GATE.md`
- Core High-Fi الحالية في Figma: Home، Deal Analysis، Market Exploration، Comparison

لم يُستخدم التشابه البصري لإثبات تطابق المقاييس. كل نتيجة أدناه تعتمد على grain وتعريف وفترة ومصدر وحساب قابل لإعادة الإنتاج، أو تصنَّف صراحةً `UNVERIFIABLE`.

## 3. الحسم الدلالي للتعارضين المعروفين

### 3.1 `28,400` مقابل `10,295`

#### Source of Truth لثليم

| الحقل | القيمة |
|---|---|
| Dataset | Rental indicators in Riyadh region 1st Q 2026 |
| dataset_id | `2dde7e8c-db79-4aec-be4e-37cef64c1d4d` |
| resource_id | `40783b1a-beff-4687-b863-4a101fdee3b1` |
| المقياس | `published_average_rent` |
| القيمة الدقيقة | `10,294.91 ر.س` |
| القيمة المعروضة | `10,295 ر.س` |
| التصنيف | Raw |
| التجميع | قيمة المصدر المنشورة؛ لا يعاد حسابها داخل سجل الكيان |
| geographic grain | المنطقة × المدينة × الحي |
| geography | الرياض × الرياض × ثليم |
| property grain | نوع العقار × التصنيف |
| property | استوديو × سكني |
| الفترة | 2026 Q1 |
| العقود | 437 |
| filters | المدينة=الرياض، الحي=ثليم، النوع=استوديو، التصنيف=سكني، الفترة=2026 Q1 |
| weighting | لا يوجد على مستوى السجل؛ الوزن بالعقود يستخدم فقط عند التجميع فوق أكثر من سجل |
| جودة المصدر | `source_overlap_count=1` و`source_measure_conflict=false` |

القيمة السابقة المقارنة هي `9,721.93 ر.س` و340 عقدًا في 2025 Q4، من dataset/resource مختلفين خاصين بذلك الربع.

#### فحص قابلية تفسير `28,400`

تم اختبار التجميعات الطبيعية في 2026 Q1:

| النطاق | الصفوف | العقود | المتوسط المرجح بالعقود | المتوسط البسيط |
|---|---:|---:|---:|---:|
| ثليم × استوديو | 1 | 437 | 10,294.91 | 10,294.91 |
| ثليم × جميع الأنواع | 4 | 1,372 | 14,174.19 | 16,726.34 |
| الرياض × جميع الأحياء × استوديو | 158 | 11,713 | 20,254.96 | 20,645.05 |
| الرياض × جميع الأحياء × جميع الأنواع | 798 | 207,946 | 34,539.88 | 47,428.03 |

لا ينتج أي نطاق منها `28,400`. توجد قيم خام مساوية عدديًا لـ`28,400` في صفوف أخرى غير مرتبطة بثليم وبأنواع/مدن/فترات مختلفة؛ التطابق العددي وحده ليس lineage.

**الحكم:** النطاقان الظاهران ليسا تعريفين صحيحين مختلفين يحتاجان توضيحًا فقط. `10,295` هو مقياس ثليم الصحيح؛ أما `28,400` في Home/Deal فهو literal غير قابل للتحقق، ويبدو أنه انتقل من Phase 3 إلى Phase 4. وفي Home توجد مشكلة إضافية: الـHeader يقول «كل الأحياء»، بينما 437 و`+5.9%` هما قيمتا ثليم، ولذلك يجب حسم scope المقصود قبل الاستبدال: إن كانت Home على مستوى المدينة فالقيمة المرجعية هي `20,255` Calculated، وإن كانت على ثليم فيجب إظهار ثليم واستخدام `10,295` Raw. في Deal، السياق صريح لثليم، لذلك المرجع الصحيح هو `10,295` Raw.

### 3.2 التعريف الصحيح لـ`+5.9%`

| العنصر | القيمة |
|---|---|
| metric_id | `quarterly_rent_growth` |
| current / numerator input | `10,294.91` في 2026 Q1 |
| prior / denominator | `9,721.93` في 2025 Q4 |
| formula | `(10,294.91 - 9,721.93) ÷ 9,721.93 × 100` |
| result | `5.8936857%` → `+5.9%` |
| period interval | ربع واحد متتالٍ؛ `period_gap=1` |
| geography/property | الرياض × ثليم × استوديو × سكني |
| aggregation | تغير بين قيمتي `published_average_rent` المتتاليتين لنفس الكيان |
| classification | Calculated |
| الصحيح | QoQ / تغير ربعي |
| غير الصحيح | YoY / نمو سنوي |

Metric Registry يمنع صراحةً وصف هذا المقياس كنمو سنوي، كما أن Analytics يبطل المقارنة عندما لا يكون `period_gap=1`. التسميات الصحيحة موجودة في Market Segment وComparison؛ التسميتان الخاطئتان موجودتان في Home وDeal Result.

## 4. تحقيق P1

### P1-01 — Metric value/classification drift: متوسط إيجار ثليم

1. **المشكلة:** Home/Deal تعرضان `28,400 ر.س — Calculated`، مقابل `10,295 ر.س — Raw` في Market/Comparison.
2. **الشاشات المتأثرة:** Home `21:3` وDeal Result `40:4`. Market Segment `58:246` وComparison Result `63:72` هما المرجع الصحيح ولا يحتاجان توحيدًا شكليًا.
3. **Root cause:** قيمة تصميم غير موثقة في Phase 3 نُسخت إلى Phase 4، مع غياب metric binding كامل وخلط scope في Home. ليست نتيجة Data Prep أو Analytics.
4. **Source of Truth:** `published_average_rent=10,294.91` Raw لثليم/استوديو/سكني/2026 Q1؛ أو `weighted_average_rent=20,254.96` Calculated فقط إذا كان scope Home فعلًا جميع أحياء الرياض/استوديو.
5. **نوع الإصلاح:** Content/value binding + label/classification + UX context. **ليس** Data ولا Metric definition.
6. **أقل إصلاح صحيح:** ربط Deal بالسجل الخام الصحيح؛ وفي Home تحديد scope المقصود أولًا ثم عرض قيمة وتعريف وتصنيف متوافقين معه، مع إزالة `28,400` من سياق ثليم.
7. **الملفات/Nodes لاحقًا:** Figma `24:8`, `27:25`, `40:281`، وربما نص scope المصاحب فقط. لا ملف بيانات أو كود يحتاج تعديلًا.
8. **Acceptance criterion:** كل Rent KPI يصرح بالمدينة/الحي والنوع والفترة، يعاد إنتاجه من Source of Truth، ويستخدم Raw للسجل المنشور وCalculated للتجميع المرجح؛ لا يظهر `28,400` كإيجار ثليم.

### P1-02 — Period baseline drift: `+5.9%`

1. **المشكلة:** Home/Deal تسميان الرقم نموًا سنويًا؛ Market/Comparison تسميانه تغيرًا ربعيًا 2025 Q4 → 2026 Q1.
2. **الشاشات المتأثرة:** Home `21:3` وDeal Result `40:4`.
3. **Root cause:** خطأ content/label عند نقل الرقم، وليس اختلافًا في الحساب.
4. **Source of Truth:** `quarterly_rent_growth` في Metric Registry و`entity_period_market`؛ النتيجة `5.8936857%` مع `period_gap=1`.
5. **نوع الإصلاح:** Content/label + UX context.
6. **أقل إصلاح صحيح:** تغيير «النمو السنوي/مقارنة سنوية» إلى «التغير الربعي» وإظهار `2025 Q4 → 2026 Q1`؛ توضيح scope Home في الوقت نفسه.
7. **الملفات/Nodes لاحقًا:** `27:17`, `40:273`. تبقى `60:349`, `63:616`, `63:623` مرجعًا صحيحًا.
8. **Acceptance criterion:** الاسم، الفترتان، grain والتصنيف Calculated متطابقة مع Registry، ولا يظهر YoY من دون مقارنة بنفس الربع من العام السابق.

### P1-03 — Market → Comparison interaction/context contract

1. **المشكلة:** انتقال المستخدم من Market إلى Comparison غير محدد كعقد تفاعل قابل للاختبار؛ رابط المقارنة يظهر داخل رسالة غياب بيانات البيع، وصف ثليم يبدو قابلًا للنقر بلا specification موثق.
2. **الشاشات المتأثرة:** Market List `58:108`، Market Segment `58:246`، Comparison Selection `63:3`، ثم Result `63:72`.
3. **Root cause:** IA تعرف contextual compare وComparison تحفظ grain، لكن High-Fi لم توثق trigger/prefill/context persistence وحالات mismatch.
4. **Source of Truth:** IA/UX Blueprint الحالي، وlocked context في `63:555` (المدينة/نوع العقار/الفترة)، لا قيمة Metric منفردة.
5. **نوع الإصلاح:** Interaction specification + UX context.
6. **أقل إصلاح صحيح:** تحديد hotspot/action موجود لإرسال ثليم كبديل أول، مع الحفاظ على المدينة والنوع والفترة، وإبقاء رسالة Missing Sale مخصصة لحدود بيانات البيع لا كبوابة المقارنة الوحيدة.
7. **الملفات/Nodes لاحقًا:** `59:380`, `60:398`, `63:555`, `63:561`, `63:567`, `63:575`, `63:577`، وprototype interaction لاحقًا فقط بعد الاعتماد.
8. **Acceptance criterion:** مسار واحد واضح وقابل للاختبار يفتح Comparison، يملأ ثليم، يقفل/يتحقق من grain، يمنع المقارنة غير المتكافئة، ويحفظ السياق عند الرجوع.

### P1-04 — Chart state/component contract

1. **المشكلة:** Charts في Market مبنية كإطارات شاشة، بينما Phase 2 تملك Visualization Container بحالات Default/Loading/Insufficient؛ الربط بينهما وحالات missing period غير موثق رسميًا.
2. **الشاشات المتأثرة:** Market Overview `58:39` وMarket Segment `58:246`.
3. **Root cause:** فجوة design/state mapping، لا مشكلة بيانات. الرسم الحالي يعرض الانقطاع عند 2025 Q3 بصدق، لكن لا يوجد contract موحد للحالات أو fallback.
4. **Source of Truth:** Phase 2 Visualization Container `17:176` وحالاته `17:152`, `17:156`, `17:160`؛ Registry/Analytics يحددان metric والفترات المتتالية.
5. **نوع الإصلاح:** Design + Interaction specification.
6. **أقل إصلاح صحيح:** استخدام/ربط الحاوية الحالية وتوثيق اختيار Default/Loading/Insufficient مع استمرار كسر الخط عند الفترة المفقودة وإظهار metric/unit/scope/period.
7. **الملفات/Nodes لاحقًا:** `59:279`, `59:295`, `60:366`, `60:382`؛ المكونات الحالية `17:152`, `17:156`, `17:160` مرجع وليست مطالبة بالتغيير.
8. **Acceptance criterion:** كل chart يستخدم عقد الحالة نفسه، لا يصل خطًا عبر missing period، يوضح الوحدة والسياق، وله loading/insufficient وبديل نصي/جدولي قابل للفهم؛ لا Component جديد ما لم تثبت فجوة فعلية.

## 5. Cross-Screen Metric Matrix

| Metric | الظهور عبر الرحلات: label / value / class | geography / property / period | aggregation / source / definition | Figma nodes | الحكم |
|---|---|---|---|---|---|
| Rent | Home وDeal: `متوسط الإيجار / 28,400 / Calculated`؛ Segment وComparison: `الإيجار المنشور / 10,295 / Raw`؛ Overview: `المتوسط المرجح / 20,255 / Calculated` | Home header: الرياض/كل الأحياء/2026Q1؛ Deal/Segment/Comparison: ثليم/استوديو/2026Q1؛ Overview: الرياض/كل الأحياء/استوديو/2026Q1 | Raw = قيمة المصدر المنشورة؛ Calculated = Σ(rent×deals)/Σ(deals). `28,400` بلا lineage | `24:8`, `27:25`, `40:281`, `59:270`, `60:351`, `63:591`–`63:599` | **INCONSISTENT** |
| Rental contracts | Home/Deal/Segment/Comparison: `437 / Raw`؛ Overview: `11,713 / Raw aggregate` | 437 = ثليم/استوديو/2026Q1؛ 11,713 = الرياض/كل الأحياء/استوديو/2026Q1؛ Home لا يصرح بثليم | قيمة المصدر على الصف وتُجمع بعد dedup عند توسيع النطاق | `27:21`, `40:277`, `59:266`, `60:350`, `63:603`–`63:611` | **VALID DIFFERENCE — CONTEXT UNCLEAR** |
| Rent growth | Home/Deal: `نمو سنوي / +5.9 / Calculated`؛ Segment/Comparison: `تغير ربعي / +5.9 / Calculated`؛ Overview: `تغير ربعي / +0.2 / Calculated` | +5.9 = ثليم/استوديو، 2025Q4→2026Q1؛ +0.2 = نطاق المدينة/استوديو للفترتين | QoQ بين ربعين متتاليين، لا YoY | `27:17`, `40:273`, `59:262`, `60:349`, `63:615`–`63:627` | **INCONSISTENT** |
| Opportunity Score | ثليم `84.5 / Inference` متسق؛ المرقب Home `83.9` مقابل Comparison `83.7` | cohort لنفس نوع العقار ومستوى الجغرافيا، 2026Q1 مع prior صالح | 40% liquidity + 35% growth + 25% affordability؛ current/prior deals ≥10. القيمة المحسوبة الحالية للمرقب `83.7387`→`83.7` | `25:11`, `28:30`, `28:34`, `60:389`, `63:631`–`63:639` | **INCONSISTENT** |
| Deal/Property inference | Deal Result يعرض قرارًا/إشارة صفقة تقارب `23/100 / Inference` | ثليم/استوديو، لكن مدخلات السعر والمساحة والتمويل غير ظاهرة في Result | `_deal_score`: yield، price gap، cash flow/DSCR، break-even occupancy، demand rank | `40:246`, `40:257`, `40:261`, `40:265` | **UNVERIFIABLE** |
| Data Sufficiency | Home/Deal/Market/Comparison تفرق بين كفاية البيانات والثقة وتعرض partial/missing sales | ثليم current=437 وprior=340 أعلى من حد score=10؛ sales exact match مفقود | Ordinal inference؛ ليست confidence probability | `33:41`, `40:293`, `59:331`, `60:392`, `63:645`, `63:648` | **CONSISTENT** |
| Matched Sale coverage | رسائل Missing Sale Match متوافقة، ولا تعرض Sales KPI بلا coverage | لا يوجد Riyadh/Thulaim/studio match؛ sale dataset المتاح محصور بأحياء أخرى ونوع قطعة أرض-سكني | exact matched coverage قبل العرض | `40:289`, `59:331`, `60:398`, `63:651` | **CONSISTENT** |
| City aggregate trend vs segment trend | Overview يصرح weighted city aggregate؛ Segment/Comparison يصرح published entity value | الرياض/كل الأحياء/استوديو مقابل ثليم/استوديو؛ 2025Q4→2026Q1 | تعريفان صالحان عند grain مختلف، والسياق ظاهر في Market | `59:262`–`59:295`, `60:349`–`60:382`, `63:591`–`63:627` | **VALID DIFFERENCE — CONTEXT CLEAR** |

### حصيلة المصفوفة

| التصنيف | العدد |
|---|---:|
| CONSISTENT | 2 |
| VALID DIFFERENCE — CONTEXT CLEAR | 1 |
| VALID DIFFERENCE — CONTEXT UNCLEAR | 1 |
| INCONSISTENT | 3 |
| UNVERIFIABLE | 1 |
| **الإجمالي** | **8** |

## 6. تحقق Data/Metric Governance

- Data Prep يزيل التكرار على grain الأعمال: السنة، الربع، المنطقة، المدينة، الحي، نوع العقار، التصنيف؛ ويحتفظ بأحدث مصدر مع flags للتداخل والتعارض.
- سجل ثليم 2026 Q1 لا يحمل source overlap أو measure conflict.
- Analytics يحسب `period_gap` ويرفض النمو عندما لا تكون الفترتان متتاليتين.
- Opportunity Score الحالي يشترط current/prior eligible، ويحسب ranks داخل cohort نوع العقار بدل خلط الأنواع.
- مخرجات KPI Audit بعد المعالجة تسجل صفر business-grain duplicates وصفر non-consecutive growth، وتثبت وجود prior مؤهل للدرجات.
- `28,400` غير موجود كقيمة مرجعية مرتبطة بثليم في Registry أو analytics أو audit أو snapshot البيانات الحالي/الملتزم؛ لذلك لا يوجد مبرر لتعديل البيانات كي توافق التصميم.

## 7. Figma nodes التي تحتاج تعديلًا لاحقًا

بعد اعتماد remediation فقط:

- **P1-01:** `24:8`, `27:25`, `40:281`
- **P1-02:** `27:17`, `40:273`
- **Opportunity Score collateral:** `28:30` لتحديث المرقب من `83.9` إلى القيمة المحكومة `83.7` أو إعادة ربطه بمصدره
- **P1-03:** `59:380`, `60:398`, `63:555`, `63:561`, `63:567`, `63:575`, `63:577`
- **P1-04:** `59:279`, `59:295`, `60:366`, `60:382`

العقد الصحيحة التي تُستخدم كمرجع ولا تعدّل لمجرد التوحيد: `60:349`, `60:350`, `60:351`, `63:591`–`63:627`, ومكونات Visualization في `17:152`, `17:156`, `17:160`.

## 8. ترتيب المعالجة المقترح

1. تثبيت scope Home: city-wide أم selected segment، لأنه يحكم Rent/Contracts/Growth معًا.
2. إصلاح P1-01 في Home وDeal وربط القيمة والتصنيف والسياق بالمقياس الصحيح.
3. إصلاح P1-02 بتسمية QoQ والفترتين، ثم تصحيح collateral drift للمرقب `83.9`→`83.7` وفق الحساب الحالي.
4. إغلاق P1-03 بعقد Market→Comparison مكتوب واختبار context preservation.
5. إغلاق P1-04 بربط charts بحالات Phase 2 الحالية واختبار missing/loading/insufficient.
6. إعادة تشغيل Cross-Screen Metric Matrix وGate Review؛ لا إعادة تشغيل data prep مطلوبة إلا كتحقق non-mutating.

## 9. قرار الاستعداد

**READY FOR TARGETED REMEDIATION**

الأسباب:

- جذور P1 الأربعة محددة ومصادر الحقيقة متاحة.
- لا P1 يتطلب تغييرًا في البيانات أو الحسابات.
- لا P1 يتطلب إعادة فتح Metric Governance.
- النقطة الوحيدة التي تحتاج قرار UX قبل التنفيذ هي scope Home، وليست Data Investigation جديدة.
- Deal inference يبقى `UNVERIFIABLE` حتى تتاح مدخلات السيناريو المستخدمة في Candidate؛ يجب عدم تقديم رقمه كقيمة قابلة لإعادة الإنتاج في Gate اللاحقة من دون تلك المدخلات.

## 10. سجل القيود

- لم تُعدّل Figma أو Low-Fi أو High-Fi أو Variables أو Styles أو Components.
- لم تُعدّل البيانات أو Metric Registry أو Analytics أو أي كود/CSS.
- لم يُنفذ commit أو push.
- التقرير نفسه هو الملف الوحيد المنشأ في هذه المرحلة.

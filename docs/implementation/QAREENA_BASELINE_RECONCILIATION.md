# Qareena — Git Baseline Reconciliation قبل Batch 0

**تاريخ الفحص:** 2026-09-06  
**النوع:** Audit + Baseline Preparation فقط  
**القرار:** **BASELINE NEEDS DECISIONS**

## 1. الخلاصة التقنية

التغييرات المحلية ليست مجموعة edits عشوائية؛ معظمها حزمة Metric/Data Governance مترابطة وصحيحة الاتجاه، وتحتاج أن تصبح جزءًا من baseline قبل تنفيذ الواجهة. لكنها **غير جاهزة للتجميد كما هي** لثلاثة أسباب:

1. `data/processed/rental_market.csv.gz` أصبح snapshot محكومًا من **44,455 صفًا** بلا business-grain duplicates، بينما `data/warehouse/real_estate.sqlite` المتتبع بقي عند **45,198 صفًا و743 duplicate group**. ومسار التشغيل المحلي/Cloud fallback يفضل SQLite على CSV، لذلك قد يعمل التطبيق فعليًا على النسخة القديمة رغم نجاح KPI Audit على CSV.
2. `metric_registry.py` يصف Forecast في الترجمة المرئية بأنه «توقع غير مختبر رجعيًا»، بينما `forecasting.py` أصبح يشغّل rolling backtest ويصنف الحالة `backtested_high_error`. التصنيف الأساسي Forecast صحيح، لكن النص التفصيلي stale.
3. `data_engine.build_market_signals()` ما زال يحسب النمو من previous available observation بلا `period_gap == 1`. هذا الجدول لا يستهلكه Core UI الحالي، لكن وجود مسار ثانٍ غير محكوم داخل warehouse يحتاج قرارًا: إصلاحه ضمن governance baseline أو إعلانه deprecated وغير صالح للاستهلاك.

بالتالي لا يجوز بدء Batch 0 من `HEAD` الحالي، ولا يجوز commit شامل لكل ما في worktree. التوصية هي **Option B — Split Baseline Commits** بعد حسم النقاط الثلاث وإعادة بناء/مزامنة SQLite بصورة مقصودة.

## 2. Worktree Inventory

### 2.1 Git state

| البند | القيمة |
|---|---|
| Current branch | `main` |
| Upstream | `origin/main` |
| HEAD SHA | `0caa1e535095abc9dc5ff393ab3e5f8a13fd0642` |
| HEAD subject | `Add neighborhood reports and Riyadh map explorer` |
| Tracked modified | 9 |
| Tracked deleted | 0 |
| Untracked قبل إنشاء هذا التقرير | 261 |
| Untracked بعد إنشاء هذا التقرير | 262 متوقعًا، لأن التقرير نفسه جديد |
| Tracked diff | 203 additions، 114 deletions، وbinary snapshot |

### 2.2 Tracked modified files

| File | ما تغير | المرحلة/الأصل | النوع | التصنيف |
|---|---|---|---|---|
| `app.py` | استبدال confidence بكفاية البيانات؛ period-gap وprior-volume eligibility لدرجات الرياض؛ cohort بحسب نوع العقار؛ وسم Inference؛ لغة Forecast/Reports أكثر تحفظًا | Metric Remediation & Governance | Production code | REQUIRED BASELINE |
| `data/processed/rental_market.csv.gz` | snapshot deduplicated: 45,198 → 44,455 صفًا | Data remediation | Processed data | REQUIRED BASELINE بعد مزامنة SQLite |
| `src/real_estate_intel/analytics.py` | `period_gap`؛ رفض non-consecutive growth؛ current/prior min-deals؛ no zero-fill؛ same-type cohort؛ Inference metadata | Metric Governance | Production analytics | REQUIRED BASELINE |
| `src/real_estate_intel/data_prep.py` | business key؛ deterministic source precedence؛ dedup؛ overlap/conflict metadata | Data remediation | Production data prep | REQUIRED BASELINE |
| `src/real_estate_intel/developer_ai.py` | data sufficiency بدل confidence؛ منع growth غير المتتالي؛ volume eligibility في الفترتين | Metric Governance | Production analytics | REQUIRED BASELINE |
| `src/real_estate_intel/forecasting.py` | history sufficiency منفصلة؛ rolling backtest؛ validation status؛ method disclosure | Metric Governance | Production analytics | REQUIRED BASELINE |
| `src/real_estate_intel/official_sources.py` | نقل lineage إلى Metric Registry؛ إزالة trust score من العرض؛ terminology محكومة | Metric Governance | Production code | REQUIRED BASELINE، ويتطلب `metric_registry.py` |
| `src/real_estate_intel/reporting.py` | «كفاية البيانات/التاريخ» بدل confidence في HTML/PDF | Metric Governance | Production code | REQUIRED BASELINE |
| `src/real_estate_intel/underwriting.py` | فصل data sufficiency مع compatibility alias | Metric Governance | Production analytics | REQUIRED BASELINE |

لا توجد tracked deletions أو edits تبدو accidental داخل diff. تحذيرات Git الحالية تخص LF→CRLF مستقبلًا؛ `git diff --check` لم يجد whitespace errors.

### 2.3 Untracked inventory

إجمالي 261 ملفًا وقت الجرد، موزعة إلى:

| Root | Count | المحتوى | التصنيف العام |
|---|---:|---|---|
| `docs/` | 13 | Audit، UX decisions، Implementation readiness | SUPPORTING DOCUMENTATION |
| `outputs/` | 244 | JSON audits، generated audit site، value assessment | مختلط؛ يفصل أدناه |
| `scripts/` | 2 | KPI audit + artifact updater | Test/Audit |
| `src/` | 1 | Metric Registry | REQUIRED BASELINE |
| `tests/` | 1 | Metric governance tests | REQUIRED BASELINE |

الملف الرابع عشر تحت `docs/implementation/` هو هذا التقرير، ويضاف إلى العدد بعد الجرد.

### 2.4 Ignored but relevant

يوجد 133 ملفًا ignored:

- `data/raw/` و`data/catalog/`: مدخلات جلب محلية، تبقى LOCAL ONLY وفق سياسة repo.
- `.streamlit/secrets.toml`: أسرار محلية، يجب ألا تدخل Git.
- `__pycache__/`, `.pytest_cache/` وPython cache داخل `src/scripts/tests`: Temporary state.
- generated `dist/` داخل audit site: Generated output.

لم تتغير `.gitignore`، ولا توجد Figma state/design-system JSON files داخل المشروع.

## 3. Review of Tracked Diffs

### 3.1 REQUIRED BASELINE

التسعة tracked files كلها تنتمي إلى remediation/governance معتمدة، ولا يوصى بفصل أجزاء من diff داخل الملف نفسه. العلاقات الجوهرية:

- `data_prep.py` + governed rental snapshot يحلان تضخيم grain.
- `analytics.py` + `app.py` + `developer_ai.py` يمنعون growth غير المتتالي وcohort drift.
- `forecasting.py` + `reporting.py` يفصلان كفاية التاريخ عن الدقة.
- `underwriting.py` + `app.py` + `reporting.py` يفصلون كفاية البيانات عن confidence.
- `official_sources.py` لا يعمل من clean checkout من دون `metric_registry.py` غير المتتبع.

### 3.2 SUPPORTING DOCUMENTATION

- `docs/audits/KPI_DATA_AUDIT.md`
- `docs/audits/KPI_AUDIT_BEFORE_AFTER.md`
- وثائق `docs/ux/` التسع.
- `docs/implementation/QAREENA_IMPLEMENTATION_READINESS.md`
- هذا التقرير.

هذه لا تؤثر في runtime، لكنها تحفظ أسباب القرارات والـacceptance gates ويجب فصلها عن production/data commits.

### 3.3 GENERATED / LOCAL ONLY

- `outputs/kpi-data-audit-report/`: 236 ملفًا لموقع/عارض generated كامل؛ لا يوضع تلقائيًا داخل production history. إن كان نشره مطلوبًا، الأفضل repository/artifact lifecycle مستقل.
- `outputs/qareena-value-assessment/`: أربعة ملفات من تقييم سابق مبني على analyst judgment؛ لا يعتمد عليها runtime أو baseline الحالي.
- ignored caches، raw/catalog downloads، secrets.

### 3.4 NEEDS REVIEW

- `data/warehouse/real_estate.sqlite`: ليس modified، لكنه stale دلاليًا ويجب مزامنته أو تغيير سياسة fallback قبل التجميد.
- `src/real_estate_intel/metric_registry.py`: REQUIRED ككل، لكن Forecast Arabic label في `investor_metric_lineage_frame()` يحتاج تصحيحًا قبل التجميد.
- `src/real_estate_intel/data_engine.py`: ليس modified، لكن `build_market_signals()` يولد نموًا بلا adjacent-period guard؛ يجب إصلاحه أو deprecate table صراحةً.
- `docs/audits/kpi_data_audit.ipynb`: مفيد وقابل للمراجعة، لكن generated من updater؛ قرار الفريق هل يتتبع notebooks generated.
- `scripts/update_kpi_audit_artifacts.py`: مفيد لإعادة إنتاج report/notebook، لكنه يعتمد على `nbformat` غير المعلن في dependencies؛ track فقط بعد توثيق dependency أو إبقائه tooling اختياريًا.
- `outputs/kpi_data_audit_before.json`, `after.json`, `comparison.json`: صغيرة ومفيدة كevidence، لكن تحتاج قرار retention. التوصية TRACK الثلاثة لأنها تحفظ baseline Before غير القابل لإعادة الإنتاج من الحالة الحالية.

### 3.5 DISCARD CANDIDATE

- `outputs/kpi_data_audit.json`: مطابق وظيفيًا لـ`kpi_data_audit_after.json` ومكرر بلا دور إضافي. لا يحذف في هذه المهمة.

لا يوجد discard candidate بين production code أو data files.

## 4. Metric Governance Protection

### 4.1 نتائج الحوكمة الحالية على CSV المحكوم

| Gate | النتيجة | الدليل |
|---|---|---|
| Business-grain duplicates | PASS | 0 rows / 0 groups بعد 1,486 rows / 743 groups في HEAD |
| Potential deal overcount | PASS | 0% بعد dedup |
| Non-consecutive growth | PASS | 0 من 19,474 comparisons؛ 8,611 candidates رُفضت بسبب gap |
| Missing growth zero-fill | PASS | 0 opportunity rows ناتجة عن fill للمفقود |
| Prior-period eligibility | PASS | 0 scores بلا prior؛ current/prior ≥ min-deals |
| Cohort stability | PASS | Opportunity rank shift median/max = 0/0 في sensitivity check |
| Opportunity — ثليم | PASS | 84.5495 → 84.5، Inference، studio/Riyadh cohort |
| Opportunity — المرقب | PASS | 83.7387 → 83.7، Inference، cohort نفسه |
| QoQ semantics | PASS | ثليم 2025 Q4 → 2026 Q1، `period_gap=1`، +5.8937% |
| Data Sufficiency ≠ Confidence | PASS في primary paths | registry + aliases + UI/report wording |
| Forecast treatment | PASS مع قيد | 8 folds؛ rent MAPE 18.989%؛ demand MAPE 45.383%؛ `backtested_high_error`، scenario only |
| Sales matched coverage | PASS | 44 rows، مدينة واحدة، 3 أحياء، نوع واحد؛ exact match guard يبقى |

### 4.2 تمييز Opportunity عن Property Score

الحساب المحكوم `analytics.opportunity_scores()` يعيد ثليم 84.5 والمرقب 83.7. توجد أيضًا صيغة منفصلة `Property Score` في `app.py` تعيد تقريبًا 84.5 و83.9 بسبب أوزان 35/30/20/15. هذا ليس نفس metric، ولا يجوز استعمال قيمة Property Score كبديل لـOpportunity. Core High-Fi المجمد يستخدم Opportunity 83.7؛ Batch 0 يجب أن يثبت الفصل، لكنه لا يبدأ قبل baseline.

### 4.3 الملفات المطلوبة في governance baseline

يجب أن تشمل حزمة runtime/data بعد حسم الموانع:

- `app.py`
- `src/real_estate_intel/analytics.py`
- `src/real_estate_intel/data_prep.py`
- `src/real_estate_intel/developer_ai.py`
- `src/real_estate_intel/forecasting.py`
- `src/real_estate_intel/official_sources.py`
- `src/real_estate_intel/reporting.py`
- `src/real_estate_intel/underwriting.py`
- `src/real_estate_intel/metric_registry.py`
- `data/processed/rental_market.csv.gz`
- `data/warehouse/real_estate.sqlite` بعد مزامنته، أو قرار معماري موثق بعدم استخدامه.

وحزمة tests/audit:

- `tests/test_metric_governance.py`
- `scripts/kpi_data_audit.py`
- audit JSON الثلاثة إن اعتمد retention المقترح.

## 5. Tests and Audit Assets

| Asset | القرار المقترح | السبب |
|---|---|---|
| `tests/test_metric_governance.py` | VERSION CONTROL / REQUIRED | يغطي dedup، period gap، cohort، registry، forecast separation |
| `scripts/kpi_data_audit.py` | VERSION CONTROL / REQUIRED | بوابة قابلة لإعادة التشغيل دون output argument |
| `scripts/update_kpi_audit_artifacts.py` | OPTIONAL TRACK | tooling مفيد، لكنه يكتب artifacts ويحتاج `nbformat` |
| `docs/audits/KPI_DATA_AUDIT.md` | TRACK | baseline finding وسبب remediation |
| `docs/audits/KPI_AUDIT_BEFORE_AFTER.md` | TRACK | قرار gate النهائي |
| `docs/audits/kpi_data_audit.ipynb` | OPTIONAL | generated companion، ليس مصدر الحقيقة الوحيد |
| `outputs/kpi_data_audit_before.json` | TRACK | baseline evidence غير قابل لإعادة البناء بعد remediation |
| `outputs/kpi_data_audit_after.json` | TRACK | audit evidence صغيرة ودقيقة |
| `outputs/kpi_data_audit_comparison.json` | TRACK | machine-readable gate |
| `outputs/kpi_data_audit.json` | DISCARD CANDIDATE | duplicate redundant |
| generated HTML audit site | LOCAL ONLY | 236 ملفًا وحزمة runtime منفصلة عن Production |
| Qareena value assessment | LOCAL ONLY / OPTIONAL archive | unrelated generated research artifact |

## 6. UX and Design Documentation

### TRACK

- `QAREENA_INFORMATION_ARCHITECTURE_UX_BLUEPRINT.md`
- `QAREENA_LOW_FI_FIRST_VISIT_TEST.md`
- `QAREENA_LOW_FI_GATE_REVIEW.md`
- `QAREENA_VISUAL_FOUNDATION_DISCOVERY.md`
- `QAREENA_CORE_HIGH_FI_GATE.md`
- `QAREENA_CORE_P1_ROOT_CAUSE.md`
- `QAREENA_CORE_P1_REMEDIATION.md`
- `QAREENA_PROTOTYPE_USER_TEST_REMEDIATION_01.md`
- `QAREENA_PROTOTYPE_CLICK_DEFECT_02.md`
- `QAREENA_IMPLEMENTATION_READINESS.md`
- `QAREENA_BASELINE_RECONCILIATION.md`

هذه سجلات قرار وليست generated UI exports. الأفضل commit توثيق مستقل بعد governance/tests.

### LOCAL ONLY

- كل source/runtime تحت `outputs/kpi-data-audit-report/`.
- `outputs/qareena-value-assessment/report.html` وبقية الحزمة ما لم يقرر الفريق أرشفة البحث في موقع مستقل.

### OPTIONAL

- Notebook generated.
- update script الخاص بالـartifact.
- canonical JSON outputs بحسب سياسة الاحتفاظ؛ التوصية العملية TRACK للثلاثة Before/After/Comparison.

لا يوجد Figma state file داخل worktree ليصنف أو يدخل baseline.

## 7. Data Snapshot Reconciliation

### 7.1 CSV: التغيير صحيح ومقصود

| Metric | HEAD snapshot | Worktree snapshot | Delta |
|---|---:|---:|---:|
| Rows | 45,198 | 44,455 | -743 |
| Duplicate affected rows | 1,486 | 0 | -1,486 |
| Duplicate groups | 743 | 0 | -743 |
| Total rental deals | 5,573,364 | 5,534,104 | -39,260 |
| Latest period | 2026 Q1 | 2026 Q1 | unchanged |
| Worktree retained overlap flags | — | 743 rows | audit metadata preserved |
| Worktree conflict flags | — | 3 rows | audit metadata preserved |

- SHA-256 HEAD: `f91e1b91d84578fea612fbcc94fe66650c41fc3969a2ed6d4f944c21faae0f64`
- SHA-256 worktree: `7412ffab3bc470d706026b38dbd0cb1868f1a44bc6479ddc0f2b305621799761`
- الحجم: 0.67 MiB، وهو مناسب تمامًا لسياسة repo الحالية؛ الملف كان tracked أصلًا.

الـ44,455 صفًا هي snapshot remediation المعتمدة، ويجب أن تصبح baseline.

### 7.2 SQLite: سليم بنيويًا لكنه stale دلاليًا

| Check | النتيجة |
|---|---|
| `PRAGMA integrity_check` | `ok` |
| Rental rows | 45,198 |
| Sale rows | 44 |
| Latest rental period | 2026 Q1 |
| Duplicate business-key groups | 743 |
| File size | 25.89 MiB |
| Git status | tracked، unchanged |

`load_local_fallback()` يقرأ SQLite أولًا، ثم CSV. لذلك integrity=ok لا يعني أن البيانات محكومة؛ runtime المحلي وfallback المنشور يمكن أن يعرضا counts/scores القديمة. أقل معالجة صحيحة قبل التجميد: إعادة بناء SQLite من snapshot المحكومة ثم فحص parity، أو قرار صريح بتغيير fallback precedence/إزالة SQLite من release. لا ينفذ أي منهما هنا.

## 8. Baseline Validation

### 8.1 Full test suite

```text
73 passed, 5 subtests passed in 21.78s
```

لا failures. الاختبارات تستخدم working code وتثبت primary governance rules، لكنها لا تختبر CSV↔SQLite parity أو warehouse signal period gaps.

### 8.2 KPI audit

تشغيل `python -B scripts/kpi_data_audit.py` بلا output arguments لم يكتب artifacts وأعاد:

- rental rows: 44,455
- latest: 2026 Q1
- business duplicates: 0
- non-consecutive growth comparisons: 0
- opportunity missing previous: 0
- opportunity zero-filled growth: 0
- registry: 9 unique metrics و5 classifications محكومة
- forecast: `backtested_high_error`، 8 folds، 18.989% rent MAPE، 45.383% demand MAPE
- sales: 44 rows، latest 2026 Q2

ظهرت Streamlit bare-mode warnings فقط بسبب import `app.py` من سكربت التدقيق؛ لا failure.

### 8.3 Release validator

**النتيجة التقنية:** `release_validation=ok`، exit code 0.

```text
rows=44,455
regions=13
locations=8,132
latest_period=2026 Q1
sale_rows=44
sale_latest_period=2026 Q2
```

Warnings:

- PostgreSQL غير متاح في بيئة الفحص، وتم fallback محليًا بنجاح.
- تحذيران `use_container_width` deprecated.
- Streamlit bare-mode warning غير مؤثر.

**القيد المهم:** validator يختبر `load_rental_data()` على CSV ويطبع 44,455، ثم AppTest قد يستخدم `load_market_data()` الذي يفضل SQLite؛ لكنه لا يؤكد parity أو duplicate count لمسار runtime. لذلك PASS الحالي لا يغلق mismatch المكتشف.

### 8.4 SQLite integrity

PASS بنيويًا، FAIL بالنسبة لـgoverned parity. هذا هو الفرق بين سلامة الملف وسلامة محتواه التحليلية.

## 9. Baseline Commit Plan

### الخيار الموصى به: Option B — Split Baseline Commits

لا أوصي بـOption A لأن الحزمة تجمع binary data، runtime behavior، tests/audit evidence، وUX decisions؛ فصلها يجعل المراجعة والrollback واضحين. ولا يصلح Option C لأن clean checkout من HEAD يفتقد Metric Registry ويحتوي snapshot غير محكومة.

الترتيب المقترح بعد حسم الموانع، من دون تنفيذه الآن:

1. **Data/Metric remediation runtime**  
   Production modules + Metric Registry + governed CSV + synchronized SQLite. يجب أن يثبت diff أن كلا fallback assetين على grain واحد.
2. **Metric governance tests and reproducible audit**  
   `test_metric_governance.py`, `kpi_data_audit.py`، وcanonical Before/After/Comparison JSON. يمكن ضم updater فقط إذا وثقت تبعية `nbformat`.
3. **Audit, UX, and implementation decision records**  
   Markdown docs؛ notebook optional. لا generated HTML site.

Acceptance قبل commit الأول:

- CSV وSQLite row count = 44,455 أو equivalence موثقة إذا تغيرت سياسة storage.
- duplicate groups = 0 في runtime source الفعلي.
- `metric_registry.py` Forecast label متسقة مع backtested status.
- warehouse signals إما adjacent-period-safe أو معلنة deprecated وغير مستهلكة.
- full tests + KPI audit + release validator تمر بعد التصحيح.

## 10. Branch Strategy

لا يبدأ implementation على `main`. بعد إتمام commits الثلاثة ومراجعتها يصبح آخر commit منها هو **Implementation Baseline**، ثم ينشأ branch جديد:

`feat/qareena-core-ui`

هذا الاسم يطابق طلب المستخدم؛ وإذا طبقت سياسة Codex الآلية لاحقًا يمكن استخدام `codex/qareena-core-ui`. الأهم هو أن يبدأ branch من baseline المتجمد لا من `0caa1e5` ولا من worktree متسخ.

كل Batch لاحقة تبقى commit/PR مستقلة. لا تخلط UX docs أو generated outputs مع تغييرات Production UI.

## 11. Blockers and Required Decisions Before Batch 0

### B-01 — Runtime data source mismatch — BLOCKER

- **فشل:** CSV محكومة، SQLite ليست كذلك.
- **الأثر:** runtime قد يعيد duplicate counts/scores رغم PASS في audit.
- **القرار المطلوب:** rebuild SQLite وتتبعه، أو تغيير storage/fallback policy.
- **أصغر معالجة:** rebuild SQLite من working governed snapshot وتشغيل parity assertion.

### B-02 — Forecast lineage wording — BLOCKER FOR FREEZE

- **فشل:** `Forecast` موسوم «غير مختبر رجعيًا» رغم وجود 8-fold backtest.
- **الأثر:** Data/Methodology قد يعرض lineage متناقضة.
- **القرار المطلوب:** جعل classification label محايدًا «توقع» وإبقاء validation status منفصلًا.
- **أصغر معالجة:** تعديل mapping واحد واختبار النص/الحقل.

### B-03 — Secondary warehouse growth path — BLOCKER FOR GOVERNANCE CLAIM

- **فشل:** `build_market_signals()` لا يتحقق من `period_gap`.
- **الأثر:** أي consumer مستقبلي للجدول قد يعيد non-consecutive growth.
- **القرار المطلوب:** تطبيق guard نفسه أو deprecate/عدم بناء الجدول.
- **أصغر معالجة:** إضافة previous period index + gap mask + test، إن بقي الجدول.

### B-04 — Artifact retention — NON-BLOCKING DECISION

- **السؤال:** هل تتتبع canonical JSON/notebook أم تحفظها خارج production history؟
- **التوصية:** TRACK JSON Before/After/Comparison، TRACK Markdown، OPTIONAL notebook، LOCAL ONLY generated website.

## 12. Further Questions

1. هل SQLite جزء مقصود من Streamlit Cloud release أم fallback محلي فقط؟ الكود والـGit الحاليان يعاملانه كجزء release.
2. هل `rental_market_signals` له consumer خارجي غير ظاهر في repo؟ إن لم يوجد، deprecation أبسط من توسيع مسار حساب ثانٍ.
3. هل تريدون حفظ audit website في repository منفصل/hosting artifact، أم اعتباره build output قابلًا لإعادة التوليد؟

## 13. Baseline Reconciliation Summary

- **Current branch:** `main`
- **HEAD SHA:** `0caa1e535095abc9dc5ff393ab3e5f8a13fd0642`
- **Tracked modified count:** 9
- **Tracked deleted count:** 0
- **Untracked count:** 261 وقت الجرد؛ 262 بعد إضافة هذا التقرير
- **REQUIRED BASELINE:** 9 tracked runtime/data files + `metric_registry.py` + governance test + KPI audit script؛ وSQLite بعد مزامنته
- **SUPPORTING DOCUMENTATION:** audit Markdown، 9 UX records، Implementation Readiness، هذا التقرير، وcanonical audit JSON المقترحة
- **GENERATED / LOCAL ONLY:** 236-file audit site، 4-file value assessment، ignored raw/catalog/secrets/caches
- **NEEDS REVIEW:** stale SQLite، Forecast lineage label، warehouse signal period-gap path، notebook/updater/JSON retention
- **DISCARD CANDIDATE:** redundant `outputs/kpi_data_audit.json` فقط
- **Metric Governance status:** primary CSV/analytics gates PASS؛ baseline-wide status CONDITIONAL بسبب SQLite ومسار signals/label
- **Data snapshot status:** governed CSV 44,455 PASS؛ runtime SQLite 45,198 with 743 duplicate groups NOT READY
- **Tests status:** 73 passed + 5 subtests passed
- **Release validation:** exit 0 / `release_validation=ok`، لكن لا يكتشف CSV↔SQLite mismatch
- **Recommended commit strategy:** **B — Split Baseline Commits**
- **Recommended branch:** `feat/qareena-core-ui` بعد baseline freeze، وليس implementation مباشرة على `main`
- **Blockers before Batch 0:** 3 blockers + artifact retention decision غير مانع

## Final Decision

**BASELINE NEEDS DECISIONS**

العمل المحلي ذو قيمة ويجب حمايته، لكن تجميده الآن سيحفظ runtime data source قديمًا مع حوكمة تقول العكس. أولوية الخطوة التالية هي حسم SQLite/fallback، ثم تصحيح وصف Forecast وحماية أو إيقاف warehouse signals، وبعدها إعادة البوابات وتجهيز commits المنفصلة. لم يبدأ Batch 0.


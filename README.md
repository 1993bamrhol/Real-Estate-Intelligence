# قرينة | QAREENA

[التطبيق المباشر](https://real-estate-intelligence-n7ibv43gwsfeuuew28wnht.streamlit.app/)

منصة رقمية لتحليل فرص الإيجار العقاري في المملكة اعتمادا على البيانات المفتوحة الرسمية من الهيئة العامة للعقار ومنصة البيانات المفتوحة الوطنية.

## الحالة الحالية

- لوحة Streamlit عربية جاهزة للتجربة.
- مساعد قرار عقاري مدمج داخل الصفحة.
- بيانات إيجار موحدة من `67` مجموعة بيانات مفتوحة.
- لقطة بيانات قابلة للنشر: `data/processed/rental_market.csv.gz`.
- التغطية الحالية: `45,198` سجل، `13` منطقة، و`8,132` موقع.
- آخر فترة متاحة في النسخة الحالية: `2026 Q1`.
- يجري فحص البيانات وتحديثها آليًا كل شهر عبر GitHub Actions، مع رفض أي نسخة أقدم أو ناقصة التغطية.

## التشغيل المحلي

```powershell
pip install -e .
streamlit run app.py --server.port 8504
```

ثم افتح:

```text
http://localhost:8504
```

## تحديث البيانات

التحديث الآلي موجود في `.github/workflows/refresh-market-data.yml` ويعمل في اليوم الأول من كل شهر، ويمكن تشغيله يدويًا من تبويب Actions. لتحديث Supabase أيضًا، أضف `DATABASE_URL` إلى GitHub repository secrets باسم مطابق. أسرار Streamlit مستقلة ولا تنتقل إلى GitHub Actions.

لجلب أحدث كتالوج متاح من بوابة البيانات المفتوحة:

```powershell
python scripts/fetch_rega_data.py --seed-only --crawl-pages 80 --page-size 100
```

لبناء لقطة مضغوطة قابلة للنشر بعد التحديث:

```powershell
python scripts/build_data_snapshot.py
```

التطبيق يفضل قراءة ملفات `data/raw/*.csv` عند وجودها، ويستخدم اللقطة `data/processed/rental_market.csv.gz` تلقائيا عند عدم وجود الملفات الخام. هذا يجعل النشر أخف وأسهل.

## فحص النسخة

قبل النشر أو المشاركة:

```powershell
python scripts/validate_release.py
```

الفحص يتأكد من:

- سلامة ملفات Python.
- تحميل بيانات الإيجار.
- وجود تغطية سوقية كافية.
- عدم وجود أخطاء في تشغيل Streamlit.

## النشر على Streamlit Cloud

ارفع الملفات التالية إلى GitHub:

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `src/`
- `scripts/`
- `data/processed/rental_market.csv.gz`

لا تحتاج إلى رفع `data/raw/*.csv` أو `data/catalog/*.json` لأنها ملفات تشغيل محلية كبيرة ومتغيرة.

إعدادات Streamlit Cloud:

- Main file path: `app.py`
- Python dependencies: `requirements.txt`
- أضف `DATABASE_URL` للحفظ الدائم في قاعدة البيانات.
- أضف `SUPABASE_URL` و`SUPABASE_PUBLISHABLE_KEY` لتفعيل حسابات البريد وOTP.

## تفعيل حسابات Supabase Auth

انسخ القيم من Supabase ثم أضفها في Streamlit Cloud من **App settings > Secrets**:

```toml
SUPABASE_URL = "https://PROJECT_REF.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_REPLACE_ME"
```

لا تستخدم `service_role` أو secret key في التطبيق. المفتاح المطلوب هنا هو **Publishable key**، ويمكن استخدام `SUPABASE_ANON_KEY` للمشاريع القديمة.

لإرسال رمز رقمي بدل رابط الدخول:

1. افتح Supabase ثم **Authentication > Email Templates**.
2. افتح قالب **Magic Link**.
3. اجعل محتوى الرسالة يتضمن `{{ .Token }}`، مثل: `<p>رمز دخول قرينة: {{ .Token }}</p>`.
4. احفظ القالب، ثم جرّب تسجيل الدخول من الشريط الجانبي للتطبيق.

الحساب المسجّل يحصل على مساحة شخصية تلقائيًا. يبقى رمز مساحة العمل متاحًا لاسترجاع المشاريع القديمة أو المساحات المشتركة. خدمة البريد الافتراضية في Supabase مناسبة للتجربة فقط؛ للإطلاق التجاري يلزم إعداد SMTP مخصص.

التوثيق الرسمي: [Passwordless email logins](https://supabase.com/docs/guides/auth/auth-email-passwordless) و[Custom SMTP](https://supabase.com/docs/guides/auth/auth-smtp).

## بنية المشروع

- `app.py`: واجهة Streamlit ولوحة القرار.
- `scripts/fetch_rega_data.py`: جلب بيانات الهيئة من بوابة البيانات المفتوحة.
- `scripts/build_data_snapshot.py`: بناء لقطة بيانات مضغوطة للنشر.
- `scripts/validate_release.py`: فحص جاهزية النسخة.
- `src/real_estate_intel/data_prep.py`: توحيد بيانات الإيجار.
- `src/real_estate_intel/analytics.py`: حساب المؤشرات والفرص.
- `src/real_estate_intel/rega_client.py`: عميل API للبيانات المفتوحة.
- `data/processed/rental_market.csv.gz`: لقطة البيانات المعتمدة للنشر.

## مصادر البيانات

- صفحة الهيئة العامة للعقار للبيانات المفتوحة: https://rega.gov.sa/البيانات-المفتوحة/
- منصة البيانات المفتوحة الوطنية: https://open.data.gov.sa/ar/home

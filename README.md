# Real Estate Intelligence

منصة رقمية لتحليل فرص الإيجار العقاري في المملكة اعتمادا على البيانات المفتوحة الرسمية من الهيئة العامة للعقار ومنصة البيانات المفتوحة الوطنية.

## الحالة الحالية

- لوحة Streamlit عربية جاهزة للتجربة.
- مساعد قرار عقاري مدمج داخل الصفحة.
- بيانات إيجار موحدة من `67` مجموعة بيانات مفتوحة.
- لقطة بيانات قابلة للنشر: `data/processed/rental_market.csv.gz`.
- التغطية الحالية: `45,198` سجل، `13` منطقة، و`8,132` موقع.
- آخر فترة متاحة في البيانات: `2026 Q1`.

## التشغيل المحلي

```powershell
pip install -r requirements.txt
streamlit run app.py --server.port 8504
```

ثم افتح:

```text
http://localhost:8504
```

## تحديث البيانات

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
- لا توجد أسرار مطلوبة حاليا.

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

# قائمة إطلاق Real Estate Intelligence

## النسخة الحالية

- رابط التطبيق: https://real-estate-intelligence-bygmdnnypwgfrnfuerekes.streamlit.app/
- المستودع: https://github.com/1993bamrhol/Real-Estate-Intelligence
- مصدر البيانات: الهيئة العامة للعقار ومنصة البيانات المفتوحة الوطنية.
- لقطة البيانات المنشورة: `data/processed/rental_market.csv.gz`.
- آخر فترة في البيانات: `2023 Q4`.

## فحص قبل المشاركة

```powershell
python scripts/validate_release.py
```

ينبغي أن يؤكد الفحص تحميل البيانات وتشغيل Streamlit بدون أخطاء.

## فحص الرابط العام

- افتح الرابط من نافذة خفية أو جهاز غير مسجل في Streamlit.
- تأكد أن الصفحة تظهر مباشرة بدون صفحة تسجيل دخول.
- جرّب الفلاتر الأساسية: المنطقة، المدينة، نوع العقار، وعدد الصفقات.
- جرّب سؤالا في مساعد القرار مثل: `أفضل أحياء الرياض للشقق السكنية`.

## تحديث البيانات

```powershell
python scripts/fetch_rega_data.py --seed-only --crawl-pages 80 --page-size 100
python scripts/build_data_snapshot.py
python scripts/validate_release.py
```

بعد نجاح الفحص، ادفع التحديث إلى GitHub حتى تعيد Streamlit Cloud بناء التطبيق.

## الخطوة التجارية التالية

- تجهيز وصف مختصر للمشروع في سطرين للمشاركة.
- تجهيز 3 لقطات شاشة: الملخص، أفضل الفرص، ومساعد القرار.
- تجربة الرابط مع 3 مستخدمين محتملين وجمع ملاحظاتهم.
- تحديد أول ميزة مدفوعة أو تقرير قابل للتصدير.

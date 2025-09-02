# دليل النشر على Render

## الخطوات:

### 1. إعداد GitHub
- ارفع الكود إلى مستودع GitHub جديد
- تأكد من رفع جميع الملفات بما في ذلك `render.yaml`

### 2. إنشاء حساب Render
- اذهب إلى [render.com](https://render.com)
- سجل حساب جديد أو سجل دخول

### 3. إنشاء قاعدة البيانات
- من Dashboard، اضغط "New +"
- اختر "PostgreSQL"
- أدخل اسم قاعدة البيانات: `musharaka-db`
- اختر الخطة المجانية
- اضغط "Create Database"

### 4. نشر التطبيق
- من Dashboard، اضغط "New +"
- اختر "Web Service"
- اربط حساب GitHub
- اختر المستودع الخاص بك
- Render سيكتشف `render.yaml` تلقائياً
- اضغط "Create Web Service"

### 5. متغيرات البيئة
سيتم إعدادها تلقائياً من `render.yaml`:
- `DATABASE_URL`: من قاعدة البيانات
- `SECRET_KEY`: سيتم توليده تلقائياً

### 6. الانتظار
- انتظر حتى ينتهي البناء والنشر (5-10 دقائق)
- ستحصل على رابط مثل: `https://musharaka-pro.onrender.com`

## النشر اليدوي (بدون render.yaml)

إذا أردت النشر يدوياً:

1. **إنشاء Web Service:**
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app.app:app`

2. **إضافة متغيرات البيئة:**
   ```
   DATABASE_URL=postgresql://...
   SECRET_KEY=your-secret-key-here
   ```

3. **إعدادات إضافية:**
   - Health Check Path: `/`
   - Auto-Deploy: Yes (للتحديث التلقائي من GitHub)

## ملاحظات مهمة:

- الخطة المجانية تتوقف بعد 15 دقيقة من عدم النشاط
- قاعدة البيانات المجانية محدودة بـ 1GB
- للإنتاج الحقيقي، يُنصح بالترقية للخطة المدفوعة

## استكشاف الأخطاء:

### إذا فشل البناء:
- تحقق من logs في Render Dashboard
- تأكد من وجود جميع الملفات المطلوبة
- تحقق من صحة `requirements.txt`

### إذا لم يعمل التطبيق:
- تحقق من DATABASE_URL
- تحقق من logs للأخطاء
- تأكد من تشغيل migrations

## الدعم:
- [Render Documentation](https://render.com/docs)
- [Flask Deployment Guide](https://render.com/docs/deploy-flask)
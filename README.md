# 🚀 مشاركة برو - نظام إدارة المشاريع المالية

نظام إدارة المشاريع المالية المتقدم باستخدام Flask + SQLAlchemy + HTMX + Tailwind CSS.

## ✨ المميزات

- 🏗️ **إدارة المشاريع** - إنشاء وإدارة المشاريع المالية
- 👥 **إدارة الشركاء** - ربط الشركاء بالمشاريع مع نسب المشاركة
- 💰 **محافظ الشركاء** - إيداع وسحب مع رصيد مباشر
- 📊 **المراحل والميزانيات** - تقسيم المشاريع لمراحل مع ميزانيات
- 🛒 **المشتريات والمخزون** - إدارة المشتريات وتتبع المخزون
- 📈 **توزيع التكاليف** - توزيع تكاليف المراحل على الشركاء
- 💼 **التسويات** - تسوية حسابات الشركاء مع المطالبات
- 📱 **واجهة تفاعلية** - HTMX للتفاعل السريع بدون إعادة تحميل

## 🛠️ التقنيات المستخدمة

- **Backend**: Flask + SQLAlchemy
- **Frontend**: HTMX + Tailwind CSS
- **Database**: SQLite (قابل للتبديل لـ PostgreSQL)
- **Styling**: Tailwind CSS مع دعم RTL
- **Interactions**: HTMX للتفاعل السريع

## 🚀 التثبيت والتشغيل

### 1. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 2. تشغيل التطبيق

```bash
python app/app.py
```

### 3. فتح المتصفح

```
http://localhost:5000
```

## 📁 هيكل المشروع

```
app/
├── app.py                 # التطبيق الرئيسي
├── models.py              # نماذج قاعدة البيانات
├── services.py            # منطق العمل التجاري
├── forms.py               # التحقق من النماذج
├── db.py                  # إعداد قاعدة البيانات
├── utils.py               # دوال مساعدة
└── templates/
    ├── layout.html        # القالب الأساسي
    ├── _partials/         # أجزاء HTMX
    └── projects/          # صفحات المشاريع
```

## 🎯 الاستخدام

### 1. إنشاء مشروع جديد
- اذهب للصفحة الرئيسية
- اضغط "إضافة مشروع جديد"
- أدخل كود المشروع والاسم والعملة

### 2. ربط الشركاء
- اذهب لصفحة المشروع
- اضغط "ربط شريك"
- اختر الشريك ونسبة المشاركة

### 3. إدارة المحافظ
- في صفحة المشروع > تبويب الشركاء
- استخدم أزرار الإيداع والسحب
- الرصيد يتحدث فوراً

### 4. إدارة المراحل
- في صفحة المشروع > تبويب المراحل
- أضف مراحل جديدة
- تابع التكلفة الفعلية

### 5. توزيع التكاليف
- في صفحة المراحل
- اضغط "توزيع بالنسب"
- التكلفة تُخصم من محافظ الشركاء

## 🔧 المتغيرات البيئية

```bash
DATABASE_URL=sqlite:///musharaka.db  # رابط قاعدة البيانات
SECRET_KEY=your-secret-key           # مفتاح التشفير
PORT=5000                           # منفذ التطبيق
```

## 📊 قاعدة البيانات

النظام يستخدم SQLite افتراضياً ويمكن تبديله لـ PostgreSQL:

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/musharaka
```

## 🎨 التخصيص

### الألوان
يمكن تخصيص الألوان في `templates/layout.html`:

```html
<script>
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#your-color'
            }
        }
    }
}
</script>
```

### الخطوط
النظام يدعم الخطوط العربية:
- Cairo
- Tajawal
- System fonts

## 🚀 النشر

### Render
```yaml
# render.yaml
services:
  - type: web
    name: musharaka-pro
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT app.app:app
```

### Heroku
```bash
# Procfile
web: gunicorn --bind 0.0.0.0:$PORT app.app:app
```

## 📝 التطوير

### إضافة ميزة جديدة

1. أضف النموذج في `models.py`
2. أضف الخدمة في `services.py`
3. أضف المسار في `app.py`
4. أضف القالب في `templates/`

### اختبار التطبيق

```bash
# تشغيل في وضع التطوير
python app/app.py

# اختبار APIs
curl http://localhost:5000/api/projects
```

## 🤝 المساهمة

1. Fork المشروع
2. أنشئ branch للميزة الجديدة
3. Commit التغييرات
4. Push للـ branch
5. أنشئ Pull Request

## 📄 الرخصة

هذا المشروع مرخص تحت رخصة MIT.

## 📞 الدعم

للدعم والاستفسارات:
- GitHub Issues
- Email: support@musharaka-pro.com

---

**مشاركة برو** - نظام إدارة المشاريع المالية المتقدم 🚀
# 🚀 Musharaka Pro API Endpoints

## ✅ **البرنامج يعمل بشكل صحيح!**

### **الرسالة التي تراها:**
```json
{"data":{"name":"Musharaka Pro (no auth)","version":1},"ok":true}
```
هذه رسالة تأكيد أن البرنامج يعمل! 🎉

---

## 📋 **جميع API Endpoints المتاحة:**

### **1. الصفحة الرئيسية:**
```
GET /
```
**الرد:** معلومات البرنامج

### **2. إدارة المشاريع:**
```
POST /api/projects          # إنشاء مشروع جديد
GET  /api/projects          # عرض جميع المشاريع
```

### **3. إدارة الشركاء:**
```
POST /api/partners                                    # إنشاء شريك جديد
POST /api/projects/{project_id}/partners             # إضافة شريك لمشروع
POST /api/projects/{project_id}/partners/{partner_id}/wallet/deposit   # إيداع في المحفظة
POST /api/projects/{project_id}/partners/{partner_id}/wallet/withdraw  # سحب من المحفظة
```

### **4. إدارة الموردين:**
```
POST /api/suppliers          # إنشاء مورد جديد
```

### **5. إدارة الأصناف:**
```
POST /api/items              # إنشاء صنف جديد
```

### **6. إدارة المستودعات:**
```
POST /api/projects/{project_id}/warehouses    # إنشاء مستودع لمشروع
```

### **7. إدارة المراحل:**
```
POST /api/projects/{project_id}/stages        # إنشاء مرحلة لمشروع
GET  /api/stages/{stage_id}/cost              # حساب تكلفة مرحلة
```

### **8. إدارة المصروفات:**
```
POST /api/expenses           # إنشاء مصروف جديد
```

---

## 🧪 **اختبار API:**

### **عرض المشاريع الموجودة:**
```bash
curl http://localhost:5000/api/projects
```

### **إنشاء مشروع جديد:**
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "code": "PROJ001",
    "name": "مشروع تجريبي",
    "base_currency": "EGP"
  }'
```

### **إنشاء شريك جديد:**
```bash
curl -X POST http://localhost:5000/api/partners \
  -H "Content-Type: application/json" \
  -d '{
    "name": "أحمد محمد",
    "email": "ahmed@example.com",
    "phone": "01234567890"
  }'
```

---

## 🎯 **البرنامج جاهز للاستخدام!**

- ✅ **الخادم يعمل** على `http://localhost:5000`
- ✅ **قاعدة البيانات** مُهيأة
- ✅ **جميع الـ APIs** متاحة
- ✅ **جاهز للنشر** على Render

**استخدم `/api/` قبل أي endpoint!** 🚀
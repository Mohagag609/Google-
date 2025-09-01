# 🚀 Musharaka Pro API Documentation

## ✅ **تم حذف الواجهة - التطبيق يعمل كـ API فقط**

### **🌐 الروابط:**
- **محلياً:** http://localhost:5000/
- **على Render:** https://googl-n9d3.onrender.com/

---

## 📋 **جميع API Endpoints:**

### **1. الصفحة الرئيسية:**
```bash
GET /
```
**الرد:**
```json
{"data":{"name":"Musharaka Pro (no auth)","version":1},"ok":true}
```

---

### **2. إدارة المشاريع:**

#### **إنشاء مشروع جديد:**
```bash
POST /api/projects
Content-Type: application/json

{
  "code": "PROJ001",
  "name": "مشروع تجريبي",
  "base_currency": "EGP"
}
```

#### **عرض جميع المشاريع:**
```bash
GET /api/projects
```

---

### **3. إدارة الشركاء:**

#### **إنشاء شريك جديد:**
```bash
POST /api/partners
Content-Type: application/json

{
  "name": "أحمد محمد",
  "email": "ahmed@example.com",
  "phone": "01234567890"
}
```

#### **عرض جميع الشركاء:**
```bash
GET /api/partners
```

#### **إضافة شريك لمشروع:**
```bash
POST /api/projects/{project_id}/partners
Content-Type: application/json

{
  "partner_id": "partner-uuid",
  "share_pct": 50.00
}
```

#### **إيداع في محفظة الشريك:**
```bash
POST /api/projects/{project_id}/partners/{partner_id}/wallet/deposit
Content-Type: application/json

{
  "amount": 1000.00
}
```

#### **سحب من محفظة الشريك:**
```bash
POST /api/projects/{project_id}/partners/{partner_id}/wallet/withdraw
Content-Type: application/json

{
  "amount": 500.00
}
```

---

### **4. إدارة الموردين:**

#### **إنشاء مورد جديد:**
```bash
POST /api/suppliers
Content-Type: application/json

{
  "name": "شركة المواد",
  "contact_person": "محمد أحمد",
  "phone": "01234567890"
}
```

#### **عرض جميع الموردين:**
```bash
GET /api/suppliers
```

---

### **5. إدارة الأصناف:**

#### **إنشاء صنف جديد:**
```bash
POST /api/items
Content-Type: application/json

{
  "sku": "ITEM001",
  "name": "أسمنت",
  "uom": "طن",
  "std_cost": 1000.00
}
```

#### **عرض جميع الأصناف:**
```bash
GET /api/items
```

---

### **6. إدارة المستودعات:**

#### **إنشاء مستودع لمشروع:**
```bash
POST /api/projects/{project_id}/warehouses
Content-Type: application/json

{
  "name": "المستودع الرئيسي"
}
```

---

### **7. إدارة المراحل:**

#### **إنشاء مرحلة لمشروع:**
```bash
POST /api/projects/{project_id}/stages
Content-Type: application/json

{
  "name": "المرحلة الأولى",
  "description": "وصف المرحلة"
}
```

#### **حساب تكلفة مرحلة:**
```bash
GET /api/stages/{stage_id}/cost
```

---

### **8. إدارة المصروفات:**

#### **إنشاء مصروف جديد:**
```bash
POST /api/expenses
Content-Type: application/json

{
  "project_id": "project-uuid",
  "description": "مصروف تجريبي",
  "amount": 500.00,
  "date": "2025-09-01"
}
```

---

## 🧪 **أمثلة للاستخدام:**

### **إنشاء مشروع جديد:**
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST001",
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

### **عرض المشاريع:**
```bash
curl http://localhost:5000/api/projects
```

### **عرض الشركاء:**
```bash
curl http://localhost:5000/api/partners
```

---

## 📊 **استجابة API:**

### **نجح العملية:**
```json
{
  "ok": true,
  "data": {
    "id": "uuid",
    "name": "الاسم",
    "created_at": "2025-09-01T15:00:00"
  }
}
```

### **فشل العملية:**
```json
{
  "ok": false,
  "error_code": "ERROR_CODE",
  "message": "رسالة الخطأ"
}
```

---

## 🎯 **الآن يمكنك:**

1. **استخدام APIs** مباشرة
2. **إنشاء مشاريع** وشركاء
3. **إدارة المحافظ** المالية
4. **تتبع المصروفات** والمراحل
5. **إدارة المستودعات** والأصناف

**التطبيق جاهز للاستخدام كـ API!** 🚀
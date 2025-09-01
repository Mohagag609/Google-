# 🔗 **الروابط الصحيحة للتطبيق**

## ❌ **الرابط الذي لا يعمل:**
```
https://googl-n9d3.onrender.com/api/
```
**السبب:** `/api/` ليس endpoint صحيح

---

## ✅ **الروابط الصحيحة:**

### **1. الصفحة الرئيسية:**
```
https://googl-n9d3.onrender.com/
```
**الرد:** معلومات التطبيق

### **2. المشاريع:**
```
https://googl-n9d3.onrender.com/api/projects
```
**الرد:** قائمة المشاريع

### **3. إنشاء مشروع جديد:**
```
POST https://googl-n9d3.onrender.com/api/projects
```

### **4. الشركاء:**
```
POST https://googl-n9d3.onrender.com/api/partners
```

### **5. الموردين:**
```
POST https://googl-n9d3.onrender.com/api/suppliers
```

### **6. الأصناف:**
```
POST https://googl-n9d3.onrender.com/api/items
```

---

## 🧪 **جرب هذه الروابط:**

### **في المتصفح:**
- ✅ `https://googl-n9d3.onrender.com/`
- ✅ `https://googl-n9d3.onrender.com/api/projects`

### **باستخدام curl:**
```bash
# الصفحة الرئيسية
curl https://googl-n9d3.onrender.com/

# عرض المشاريع
curl https://googl-n9d3.onrender.com/api/projects

# إنشاء مشروع جديد
curl -X POST https://googl-n9d3.onrender.com/api/projects \
  -H "Content-Type: application/json" \
  -d '{"code":"NEW001","name":"مشروع جديد","base_currency":"EGP"}'
```

---

## 📝 **ملاحظة مهمة:**
- `/api/` وحده لا يعمل
- يجب إضافة endpoint محدد مثل `/api/projects`
- جميع الـ APIs تحتاج `/api/` في البداية

**استخدم الروابط الصحيحة أعلاه!** 🚀
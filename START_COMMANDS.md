# 🚀 Start Commands for Render

## ✅ **Recommended Start Commands:**

### **1. Best for Production:**
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
```

### **2. Simple Python:**
```bash
python3 start.py
```

### **3. With Timeout:**
```bash
gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app
```

### **4. Single Worker (if memory issues):**
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 app:app
```

### **5. Using WSGI:**
```bash
gunicorn wsgi:app
```

## 🔧 **How to Use:**

### **In Render Dashboard:**
1. **Go to your service**
2. **Click "Settings"**
3. **Scroll to "Start Command"**
4. **Paste one of the commands above**
5. **Click "Save Changes"**
6. **Click "Manual Deploy"**

### **In render.yaml:**
```yaml
services:
  - type: web
    name: musharaka-pro
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
    envVars:
      - key: FLASK_ENV
        value: production
    healthCheckPath: /
```

## 🎯 **Which One to Choose:**

### **For Testing:**
```bash
python3 start.py
```

### **For Production:**
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
```

### **If Getting 502 Errors:**
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 1 app:app
```

### **If Memory Issues:**
```bash
python3 start.py
```

## 🧪 **Test Locally:**

```bash
# Test with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app

# Test with Python
python3 start.py

# Test health check
curl http://localhost:5000/
```

## 📱 **Expected Response:**
```json
{
  "data": {
    "name": "Musharaka Pro (no auth)",
    "version": 1
  },
  "ok": true
}
```

## 🚀 **Deploy Now:**

1. **Choose a start command**
2. **Update render.yaml**
3. **Push to GitHub**
4. **Deploy on Render**

---

*Try the simple Python command first, then upgrade to gunicorn for production.*
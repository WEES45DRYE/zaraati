# 🌿 زراعتي - متجر الأدوية الزراعية

## تشغيل المشروع على اللاب

### الخطوة 1: تثبيت المكتبات
```
pip install flask gunicorn
```

### الخطوة 2: تشغيل السيرفر
```
python app.py
```

### الخطوة 3: افتح المتصفح
- **التطبيق:** http://localhost:5000
- **لوحة التحكم:** http://localhost:5000/admin
  - المستخدم: `admin`
  - الباسورد: `admin123`

---

## رفع على النت (Render.com) - مجاني

1. روح على https://github.com وعمل حساب
2. عمل Repository جديد وارفع ملفات المشروع
3. روح على https://render.com وعمل حساب بنفس الإيميل
4. اضغط "New Web Service"
5. اختار الـ Repository بتاعك
6. في إعدادات البناء:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
7. اضغط "Deploy"

✅ بعد دقيقتين يبقى الموقع أونلاين!

---

## تغيير باسورد الأدمن
في ملف `app.py`، دور على هذا السطر:
```python
c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin','admin123')")
```
وغيّر `admin123` لأي باسورد تريده، ثم احذف ملف `zaraati.db` وأعد تشغيل البرنامج.

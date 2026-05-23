#!/bin/bash
# تشغيل المشروع محلياً

echo "📦 تثبيت المكتبات..."
pip install flask gunicorn

echo ""
echo "🚀 تشغيل السيرفر..."
echo "التطبيق: http://localhost:5000"
echo "لوحة التحكم: http://localhost:5000/admin"
echo "   اسم المستخدم: admin"
echo "   كلمة المرور: admin123"
echo ""
python app.py

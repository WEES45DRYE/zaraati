from flask import Flask, request, jsonify, redirect, session, make_response
from jinja2 import Environment
import sqlite3, os, json, re
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "zaraati_secret_2024"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

TEMPLATES = {
    "app": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>زراعتي — متجر الأدوية الزراعية</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --emerald:#00875a;
  --emerald-dark:#005c3d;
  --emerald-light:#00a36c;
  --mint:#e8faf3;
  --gold:#f5c842;
  --bg:#f4f7f5;
  --surface:#ffffff;
  --text:#111827;
  --muted:#6b7280;
  --border:#e5e7eb;
  --shadow:0 4px 24px rgba(0,135,90,.10);
  --radius:18px;
}
body{font-family:'Cairo',sans-serif;background:var(--bg);color:var(--text);max-width:430px;margin:0 auto;min-height:100vh;position:relative;overflow-x:hidden}

/* ── HEADER ── */
.header{
  background:linear-gradient(135deg,var(--emerald-dark) 0%,var(--emerald) 60%,var(--emerald-light) 100%);
  color:#fff;padding:0 16px;height:64px;
  display:flex;justify-content:space-between;align-items:center;
  position:sticky;top:0;z-index:100;
  box-shadow:0 4px 20px rgba(0,93,62,.30);
}
.header-logo{display:flex;align-items:center;gap:8px}
.header-logo .leaf{font-size:28px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.3))}
.header-logo h1{font-size:20px;font-weight:900;letter-spacing:-0.5px}
.header-logo small{display:block;font-size:9px;font-weight:400;opacity:.75;margin-top:-3px;letter-spacing:1px}
.cart-btn{
  background:rgba(255,255,255,.18);backdrop-filter:blur(8px);
  border:1.5px solid rgba(255,255,255,.3);
  color:#fff;padding:8px 14px;border-radius:24px;
  cursor:pointer;font-size:13px;font-family:'Cairo',sans-serif;font-weight:700;
  display:flex;align-items:center;gap:7px;transition:.2s;
}
.cart-btn:hover{background:rgba(255,255,255,.28)}
.cart-badge{
  background:var(--gold);color:#1a1a1a;
  border-radius:50%;min-width:20px;height:20px;
  font-size:11px;font-weight:900;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 6px rgba(0,0,0,.2);
}

/* ── NAV ── */
.bottom-nav{
  position:fixed;bottom:0;left:50%;transform:translateX(-50%);
  width:100%;max-width:430px;
  background:var(--surface);
  display:flex;border-top:1px solid var(--border);
  z-index:100;
  padding-bottom:env(safe-area-inset-bottom);
  box-shadow:0 -4px 20px rgba(0,0,0,.08);
}
.nav-btn{
  flex:1;padding:10px 0;border:none;background:none;
  cursor:pointer;color:var(--muted);
  display:flex;flex-direction:column;align-items:center;
  font-family:'Cairo',sans-serif;font-size:11px;font-weight:600;gap:3px;
  transition:.2s;position:relative;
}
.nav-btn .nav-icon{
  font-size:22px;transition:.2s;
  filter:grayscale(1);opacity:.5;
}
.nav-btn.active .nav-icon{filter:grayscale(0);opacity:1;transform:scale(1.15)}
.nav-btn.active{color:var(--emerald)}
.nav-btn.active::after{
  content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:36px;height:3px;background:var(--emerald);border-radius:0 0 4px 4px;
}

/* ── PAGES ── */
.page{display:none;padding:16px;padding-bottom:90px;animation:fadeUp .3s ease}
.page.active{display:block}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* ── HERO BANNER ── */
.hero{
  background:linear-gradient(135deg,var(--emerald-dark) 0%,var(--emerald) 70%);
  border-radius:var(--radius);
  padding:22px 20px;margin-bottom:20px;
  position:relative;overflow:hidden;
  box-shadow:var(--shadow);
}
.hero::before{
  content:'';position:absolute;inset:0;
  background:url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}
.hero-tag{
  display:inline-flex;align-items:center;gap:5px;
  background:var(--gold);color:#1a1a1a;
  border-radius:20px;padding:3px 12px;font-size:11px;font-weight:900;
  margin-bottom:10px;letter-spacing:.3px;
}
.hero h2{color:#fff;font-size:22px;font-weight:900;line-height:1.3;margin-bottom:6px}
.hero p{color:rgba(255,255,255,.8);font-size:13px;margin-bottom:18px}
.hero-btn{
  display:inline-flex;align-items:center;gap:6px;
  background:#fff;color:var(--emerald-dark);
  border:none;padding:10px 22px;border-radius:24px;
  font-weight:900;cursor:pointer;font-size:13px;font-family:'Cairo',sans-serif;
  box-shadow:0 4px 16px rgba(0,0,0,.15);transition:.2s;
}
.hero-btn:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(0,0,0,.2)}
.hero-emoji{
  position:absolute;left:-10px;top:50%;transform:translateY(-50%);
  font-size:90px;opacity:.12;filter:blur(1px);
}

/* ── SECTION ── */
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;margin-top:20px}
.section-title{font-size:16px;font-weight:900;color:var(--text)}
.section-more{font-size:12px;color:var(--emerald);font-weight:700;cursor:pointer;text-decoration:none}

/* ── CATEGORIES ── */
.cats{display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cat-pill{
  min-width:auto;white-space:nowrap;
  background:var(--surface);border-radius:30px;
  padding:8px 16px;
  display:flex;align-items:center;gap:6px;
  cursor:pointer;border:2px solid var(--border);
  transition:.2s;font-size:13px;font-weight:700;color:var(--muted);
  box-shadow:0 2px 8px rgba(0,0,0,.05);flex-shrink:0;
}
.cat-pill .cicon{font-size:18px}
.cat-pill.active,.cat-pill:hover{
  border-color:var(--emerald);background:var(--mint);color:var(--emerald);
  box-shadow:0 4px 14px rgba(0,135,90,.15);
}

/* ── PRODUCTS ── */
.products-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.product-card{
  background:var(--surface);border-radius:var(--radius);
  overflow:hidden;
  box-shadow:0 2px 12px rgba(0,0,0,.06);
  cursor:pointer;transition:.25s;
  border:1.5px solid transparent;
  position:relative;
}
.product-card:hover{
  transform:translateY(-4px);
  box-shadow:0 8px 28px rgba(0,135,90,.18);
  border-color:var(--emerald);
}
.product-img{
  height:130px;
  background:linear-gradient(135deg,#e8f8f0,#d0f0e0);
  display:flex;align-items:center;justify-content:center;
  font-size:52px;overflow:hidden;position:relative;
}
.product-img img{width:100%;height:100%;object-fit:contain;padding:12px;transition:.3s}
.product-card:hover .product-img img{transform:scale(1.08)}
.discount-tag{
  position:absolute;top:8px;right:8px;
  background:linear-gradient(135deg,#ff4757,#ff6b81);
  color:#fff;border-radius:8px;padding:2px 8px;
  font-size:10px;font-weight:900;
  box-shadow:0 2px 8px rgba(255,71,87,.35);
}
.product-info{padding:12px}
.product-name{font-size:13px;font-weight:800;color:var(--text);margin-bottom:3px;line-height:1.3}
.product-unit{font-size:11px;color:var(--muted);margin-bottom:8px;display:flex;align-items:center;gap:3px}
.product-unit::before{content:'📦';font-size:10px}
.product-footer{display:flex;align-items:center;justify-content:space-between}
.price-group{display:flex;flex-direction:column}
.price{color:var(--emerald);font-weight:900;font-size:16px}
.old-price{color:#d1d5db;font-size:11px;text-decoration:line-through}
.add-btn{
  width:34px;height:34px;background:var(--emerald);
  color:#fff;border:none;border-radius:10px;
  cursor:pointer;font-size:20px;font-weight:900;
  display:flex;align-items:center;justify-content:center;
  transition:.2s;box-shadow:0 3px 10px rgba(0,135,90,.35);
  flex-shrink:0;
}
.add-btn:hover{background:var(--emerald-dark);transform:scale(1.1)}
.add-btn:active{transform:scale(.9)}

/* ── CART ── */
.cart-item{
  background:var(--surface);border-radius:var(--radius);
  padding:14px;margin-bottom:12px;
  display:flex;gap:12px;align-items:center;
  box-shadow:0 2px 10px rgba(0,0,0,.06);
  border:1.5px solid var(--border);
  transition:.2s;
}
.cart-item-img{
  width:60px;height:60px;border-radius:12px;
  background:linear-gradient(135deg,#e8f8f0,#d0f0e0);
  display:flex;align-items:center;justify-content:center;
  font-size:28px;flex-shrink:0;overflow:hidden;
}
.cart-item-img img{width:100%;height:100%;object-fit:contain;padding:6px}
.cart-item-info{flex:1}
.cart-item-name{font-size:13px;font-weight:800;color:var(--text);margin-bottom:2px}
.cart-item-price{font-size:13px;color:var(--emerald);font-weight:700}
.qty-ctrl{display:flex;align-items:center;gap:10px;margin-top:8px}
.qty-btn{
  background:var(--mint);border:1.5px solid var(--emerald);
  color:var(--emerald);width:28px;height:28px;border-radius:8px;
  cursor:pointer;font-size:16px;font-weight:900;
  display:flex;align-items:center;justify-content:center;
  transition:.15s;
}
.qty-btn:hover{background:var(--emerald);color:#fff}
.qty-num{font-weight:900;font-size:15px;min-width:20px;text-align:center}
.del-btn{background:none;border:none;color:#ef4444;font-size:20px;cursor:pointer;transition:.2s;padding:4px}
.del-btn:hover{transform:scale(1.2)}

.cart-summary{
  background:var(--surface);border-radius:var(--radius);
  padding:18px;margin-top:12px;
  box-shadow:0 2px 12px rgba(0,0,0,.07);
}
.summary-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;font-size:14px;border-bottom:1px dashed var(--border)}
.summary-row:last-of-type{border-bottom:none}
.summary-row.total{font-weight:900;font-size:17px;color:var(--emerald);padding-top:14px;margin-top:4px;border-top:2px solid var(--emerald)}
.checkout-btn{
  width:100%;background:linear-gradient(135deg,var(--emerald-dark),var(--emerald));
  color:#fff;border:none;border-radius:14px;padding:16px;
  font-size:16px;font-weight:900;font-family:'Cairo',sans-serif;
  margin-top:16px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:8px;
  box-shadow:0 6px 20px rgba(0,135,90,.35);transition:.2s;
}
.checkout-btn:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,135,90,.45)}

/* ── EMPTY STATE ── */
.empty{text-align:center;padding:60px 20px}
.empty-icon{font-size:70px;margin-bottom:14px;opacity:.7}
.empty-title{font-size:18px;font-weight:900;color:var(--text);margin-bottom:6px}
.empty-sub{font-size:13px;color:var(--muted)}

/* ── MODAL ── */
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;align-items:flex-end;justify-content:center;backdrop-filter:blur(4px)}
.modal.open{display:flex}
.modal-sheet{
  background:var(--surface);width:100%;max-width:430px;
  border-radius:24px 24px 0 0;padding:28px 20px;
  max-height:90vh;overflow-y:auto;
  animation:slideUp .3s ease;
}
@keyframes slideUp{from{transform:translateY(60px);opacity:0}to{transform:translateY(0);opacity:1}}
.modal-handle{width:40px;height:4px;background:var(--border);border-radius:4px;margin:0 auto 22px}
.modal-title{font-size:18px;font-weight:900;text-align:center;margin-bottom:22px;color:var(--text)}

.form-group{margin-bottom:16px}
.form-group label{display:block;font-size:12px;font-weight:700;color:var(--muted);margin-bottom:7px;letter-spacing:.3px;text-transform:uppercase}
.form-group input,.form-group textarea{
  width:100%;border:2px solid var(--border);border-radius:12px;
  padding:12px 14px;font-size:14px;font-family:'Cairo',sans-serif;
  outline:none;transition:.2s;background:var(--bg);
}
.form-group input:focus,.form-group textarea:focus{border-color:var(--emerald);background:#fff;box-shadow:0 0 0 4px rgba(0,135,90,.08)}
.submit-btn{
  width:100%;
  background:linear-gradient(135deg,var(--emerald-dark),var(--emerald));
  color:#fff;border:none;border-radius:14px;padding:15px;
  font-size:16px;font-weight:900;font-family:'Cairo',sans-serif;
  cursor:pointer;margin-top:10px;
  box-shadow:0 6px 20px rgba(0,135,90,.35);transition:.2s;
}
.submit-btn:hover{transform:translateY(-1px)}
.cancel-btn{
  width:100%;background:var(--bg);border:2px solid var(--border);
  border-radius:14px;padding:12px;font-size:14px;font-weight:700;
  font-family:'Cairo',sans-serif;color:var(--muted);cursor:pointer;margin-top:8px;
}
.order-box{
  background:var(--mint);border-radius:12px;padding:14px;
  margin-bottom:16px;border:1.5px solid rgba(0,135,90,.2);
}
.order-box-item{display:flex;justify-content:space-between;font-size:13px;padding:3px 0;color:var(--text)}
.order-box hr{border:none;border-top:1.5px dashed rgba(0,135,90,.25);margin:10px 0}
.order-box .order-total{font-weight:900;font-size:15px;color:var(--emerald)}

/* ── ORDERS PAGE ── */
.order-card{
  background:var(--surface);border-radius:var(--radius);
  padding:16px;margin-bottom:12px;
  box-shadow:0 2px 10px rgba(0,0,0,.06);
  border:1.5px solid var(--border);
}
.order-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.order-num{font-weight:900;color:var(--emerald);font-size:15px}
.status-badge{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:900}
.status-جديد{background:#dbeafe;color:#1d4ed8}
.status-قيد.التنفيذ{background:#fef3c7;color:#d97706}
.status-تم.التوصيل{background:#d1fae5;color:#065f46}
.status-ملغي{background:#fee2e2;color:#b91c1c}
.order-date{font-size:12px;color:var(--muted)}
.order-total{font-size:15px;font-weight:900;color:var(--emerald);margin-top:8px;padding-top:8px;border-top:1px dashed var(--border)}

/* ── PROFILE ── */
.profile-hero{
  background:linear-gradient(135deg,var(--emerald-dark),var(--emerald));
  border-radius:var(--radius);padding:28px 20px;text-align:center;
  margin-bottom:20px;position:relative;overflow:hidden;
}
.profile-hero::before{content:'🌿';position:absolute;right:-20px;top:-20px;font-size:120px;opacity:.08}
.profile-avatar{
  width:80px;height:80px;background:rgba(255,255,255,.2);
  border-radius:50%;margin:0 auto 14px;
  display:flex;align-items:center;justify-content:center;font-size:38px;
  border:3px solid rgba(255,255,255,.4);
  backdrop-filter:blur(8px);
}
.profile-name{color:#fff;font-size:20px;font-weight:900;margin-bottom:4px}
.profile-sub{color:rgba(255,255,255,.7);font-size:13px}

.menu-item{
  background:var(--surface);border-radius:14px;
  padding:16px 18px;margin-bottom:10px;
  display:flex;align-items:center;gap:14px;
  cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.05);
  border:1.5px solid var(--border);transition:.2s;
}
.menu-item:hover{border-color:var(--emerald);transform:translateX(-3px)}
.menu-icon-wrap{
  width:42px;height:42px;background:var(--mint);border-radius:12px;
  display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;
}
.menu-label{flex:1;font-size:14px;font-weight:700;color:var(--text)}
.menu-arrow{color:var(--muted);font-size:18px;font-weight:900}

/* ── TOAST ── */
.toast{
  position:fixed;bottom:90px;left:50%;transform:translateX(-50%) translateY(10px);
  background:var(--text);color:#fff;
  padding:12px 24px;border-radius:30px;
  font-size:13px;font-weight:700;font-family:'Cairo',sans-serif;
  opacity:0;transition:.3s;z-index:400;
  pointer-events:none;white-space:nowrap;
  box-shadow:0 8px 24px rgba(0,0,0,.25);
  display:flex;align-items:center;gap:8px;
}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}

/* ── LOADING ── */
.spinner{
  width:36px;height:36px;
  border:3px solid var(--border);border-top-color:var(--emerald);
  border-radius:50%;animation:spin .7s linear infinite;margin:40px auto;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── SEARCH BAR ── */
.search-wrap{position:relative;margin-bottom:16px}
.search-icon{position:absolute;right:14px;top:50%;transform:translateY(-50%);font-size:16px;pointer-events:none}
.search-input{
  width:100%;padding:12px 42px 12px 16px;
  border:2px solid var(--border);border-radius:14px;
  font-size:14px;font-family:'Cairo',sans-serif;
  outline:none;background:var(--surface);transition:.2s;
}
.search-input:focus{border-color:var(--emerald);box-shadow:0 0 0 4px rgba(0,135,90,.08)}
</style>
</head>
<body>

<div class="header">
  <div class="header-logo">
    <div class="leaf">🌿</div>
    <div>
      <h1>زراعتي</h1>
      <small>متجر الأدوية الزراعية</small>
    </div>
  </div>
  <button class="cart-btn" onclick="showPage('cart')">
    🛒 السلة <span class="cart-badge" id="cart-count">0</span>
  </button>
</div>

<!-- HOME -->
<div class="page active" id="page-home">
  <div class="hero">
    <div class="hero-tag">🔥 عرض الأسبوع</div>
    <h2>خصم 20%<br>على كل الأسمدة</h2>
    <p>أفضل الأسمدة الزراعية بأسعار لا تُصدق</p>
    <button class="hero-btn" onclick="filterCat(2)">تسوق الآن ←</button>
    <div class="hero-emoji">🌱</div>
  </div>

  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input type="text" class="search-input" placeholder="ابحث عن منتج..." oninput="searchProducts(this.value)">
  </div>

  <div class="section-header">
    <span class="section-title">التصنيفات</span>
  </div>
  <div class="cats" id="cats-list"><div class="spinner"></div></div>

  <div class="section-header">
    <span class="section-title">المنتجات</span>
  </div>
  <div class="products-grid" id="products-grid"><div class="spinner"></div></div>
</div>

<!-- CART -->
<div class="page" id="page-cart">
  <div class="section-header" style="margin-top:0">
    <span class="section-title">🛒 سلة التسوق</span>
  </div>
  <div id="cart-list"></div>
  <div id="cart-total"></div>
</div>

<!-- ORDERS -->
<div class="page" id="page-orders">
  <div class="section-header" style="margin-top:0">
    <span class="section-title">📦 طلباتي</span>
  </div>
  <div id="orders-list">
    <div class="empty">
      <div class="empty-icon">📦</div>
      <div class="empty-title">لا توجد طلبات بعد</div>
      <div class="empty-sub">طلباتك ستظهر هنا بعد الشراء</div>
    </div>
  </div>
</div>

<!-- PROFILE -->
<div class="page" id="page-profile">
  <div class="profile-hero">
    <div class="profile-avatar">👨‍🌾</div>
    <div class="profile-name">مرحباً بك!</div>
    <div class="profile-sub">متجر الأدوية الزراعية المتميز</div>
  </div>
  <div class="menu-item"><div class="menu-icon-wrap">📦</div><div class="menu-label">طلباتي</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon-wrap">💬</div><div class="menu-label">استشارة زراعية</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon-wrap">⭐</div><div class="menu-label">المفضلة</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon-wrap">📞</div><div class="menu-label">تواصل معنا</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon-wrap">⚙️</div><div class="menu-label">الإعدادات</div><div class="menu-arrow">←</div></div>
</div>

<!-- ORDER MODAL -->
<div class="modal" id="order-modal">
  <div class="modal-sheet">
    <div class="modal-handle"></div>
    <div class="modal-title">إتمام الطلب 🛒</div>
    <div class="form-group">
      <label>الاسم الكريم</label>
      <input type="text" id="f-name" placeholder="محمد أحمد...">
    </div>
    <div class="form-group">
      <label>رقم الهاتف</label>
      <input type="tel" id="f-phone" placeholder="01xxxxxxxxx">
    </div>
    <div class="form-group">
      <label>عنوان التوصيل</label>
      <textarea id="f-address" rows="2" placeholder="المحافظة، المدينة، الشارع..." style="resize:none"></textarea>
    </div>
    <div class="order-box" id="order-summary"></div>
    <button class="submit-btn" onclick="submitOrder()">✅ تأكيد الطلب</button>
    <button class="cancel-btn" onclick="closeModal()">إلغاء</button>
  </div>
</div>

<div class="bottom-nav">
  <button class="nav-btn active" onclick="showPage('home')"><span class="nav-icon">🏠</span>الرئيسية</button>
  <button class="nav-btn" onclick="showPage('cart')"><span class="nav-icon">🛒</span>السلة</button>
  <button class="nav-btn" onclick="showPage('orders')"><span class="nav-icon">📦</span>طلباتي</button>
  <button class="nav-btn" onclick="showPage('profile')"><span class="nav-icon">👨‍🌾</span>حسابي</button>
</div>

<div class="toast" id="toast"></div>

<script>
const API = "";
let cart = JSON.parse(localStorage.getItem("zCart")||"[]");
let allProducts = [];
let activeCat = 0;

function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  const idx = {home:0,cart:1,orders:2,profile:3}[name];
  if(idx!==undefined) document.querySelectorAll('.nav-btn')[idx].classList.add('active');
  if(name==='cart') renderCart();
}

function toast(msg,type='default'){
  const t=document.getElementById('toast');
  t.innerHTML=msg; t.classList.add('show');
  t.style.background=type==='success'?'#00875a':type==='error'?'#ef4444':'#111827';
  setTimeout(()=>t.classList.remove('show'),2500);
}

async function loadCategories(){
  const res = await fetch('/api/categories');
  const cats = await res.json();
  const el = document.getElementById('cats-list');
  el.innerHTML = `<div class="cat-pill active" onclick="filterCat(0,this)"><span class="cicon">🌿</span>الكل</div>`;
  cats.forEach(c=>{
    el.innerHTML += `<div class="cat-pill" onclick="filterCat(${c.id},this)"><span class="cicon">${c.icon}</span>${c.name}</div>`;
  });
}

function filterCat(id, el){
  activeCat = id;
  document.querySelectorAll('.cat-pill').forEach(c=>c.classList.remove('active'));
  if(el) el.classList.add('active');
  renderProducts(id ? allProducts.filter(p=>p.category_id==id) : allProducts);
}

function searchProducts(q){
  const filtered = q ? allProducts.filter(p=>p.name.includes(q)) : allProducts;
  renderProducts(activeCat ? filtered.filter(p=>p.category_id==activeCat) : filtered);
}

const EMOJIS = {1:"🦟",2:"🌱",3:"🍄",4:"🌾"};

async function loadProducts(){
  const res = await fetch('/api/products');
  allProducts = await res.json();
  renderProducts(allProducts);
}

function calcDiscount(price, oldPrice){
  if(!oldPrice) return null;
  return Math.round((1-price/oldPrice)*100);
}

function renderProducts(products){
  const g = document.getElementById('products-grid');
  if(!products.length){g.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--muted)">لا توجد منتجات</div>';return;}
  g.innerHTML = products.map(p=>{
    const disc = calcDiscount(p.price, p.old_price);
    return `<div class="product-card">
      <div class="product-img">
        ${p.image_url ? `<img src="${p.image_url}" alt="${p.name}">` : (EMOJIS[p.category_id]||'🌿')}
        ${disc ? `<div class="discount-tag">-${disc}%</div>` : ''}
      </div>
      <div class="product-info">
        <div class="product-name">${p.name}</div>
        <div class="product-unit">${p.unit}</div>
        <div class="product-footer">
          <div class="price-group">
            <span class="price">${p.price} ج</span>
            ${p.old_price ? `<span class="old-price">${p.old_price} ج</span>` : ''}
          </div>
          <button class="add-btn" onclick="addToCart(${p.id},'${p.name.replace(/'/g,"\\'")}',${p.price},'${p.unit}',${p.category_id},'${p.image_url||''}')">+</button>
        </div>
      </div>
    </div>`;
  }).join('');
}

function addToCart(id,name,price,unit,catId,imageUrl){
  const ex = cart.find(i=>i.id==id);
  if(ex){ ex.qty++; } else { cart.push({id,name,price,unit,catId,imageUrl,qty:1}); }
  saveCart(); toast('✅ تم إضافة المنتج للسلة','success');
  const badge = document.getElementById('cart-count');
  badge.style.transform='scale(1.4)';
  setTimeout(()=>badge.style.transform='scale(1)',200);
}

function saveCart(){
  localStorage.setItem("zCart",JSON.stringify(cart));
  document.getElementById('cart-count').textContent = cart.reduce((s,i)=>s+i.qty,0);
}

function renderCart(){
  const el = document.getElementById('cart-list');
  const tot = document.getElementById('cart-total');
  if(!cart.length){
    el.innerHTML=`<div class="empty"><div class="empty-icon">🛒</div><div class="empty-title">السلة فارغة</div><div class="empty-sub">أضف منتجات من الصفحة الرئيسية</div></div>`;
    tot.innerHTML=''; return;
  }
  el.innerHTML = cart.map(i=>`
    <div class="cart-item">
      <div class="cart-item-img">
        ${i.imageUrl ? `<img src="${i.imageUrl}" alt="${i.name}">` : (EMOJIS[i.catId]||'🌿')}
      </div>
      <div class="cart-item-info">
        <div class="cart-item-name">${i.name}</div>
        <div class="cart-item-price">${i.price} ج / ${i.unit}</div>
        <div class="qty-ctrl">
          <button class="qty-btn" onclick="changeQty(${i.id},-1)">−</button>
          <span class="qty-num">${i.qty}</span>
          <button class="qty-btn" onclick="changeQty(${i.id},1)">+</button>
        </div>
      </div>
      <button class="del-btn" onclick="removeItem(${i.id})">🗑</button>
    </div>`).join('');
  const sub = cart.reduce((s,i)=>s+i.price*i.qty,0);
  tot.innerHTML=`
    <div class="cart-summary">
      <div class="summary-row"><span>المنتجات (${cart.reduce((s,i)=>s+i.qty,0)} عنصر)</span><span>${sub.toFixed(2)} ج</span></div>
      <div class="summary-row"><span>رسوم التوصيل 🚚</span><span>20.00 ج</span></div>
      <div class="summary-row total"><span>الإجمالي</span><span>${(sub+20).toFixed(2)} ج</span></div>
    </div>
    <button class="checkout-btn" onclick="openModal()">إتمام الطلب →</button>`;
}

function changeQty(id,d){
  const it=cart.find(i=>i.id==id);
  if(!it) return;
  it.qty+=d;
  if(it.qty<=0) cart=cart.filter(i=>i.id!=id);
  saveCart(); renderCart();
}
function removeItem(id){cart=cart.filter(i=>i.id!=id);saveCart();renderCart();}

function openModal(){
  if(!cart.length){toast('⚠️ السلة فارغة!','error');return;}
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  document.getElementById('order-summary').innerHTML=
    cart.map(i=>`<div class="order-box-item"><span>${i.name} × ${i.qty}</span><span>${(i.price*i.qty).toFixed(2)} ج</span></div>`).join('')+
    `<hr><div class="order-box-item order-total"><span>الإجمالي</span><span>${(sub+20).toFixed(2)} ج</span></div>`;
  document.getElementById('order-modal').classList.add('open');
}
function closeModal(){document.getElementById('order-modal').classList.remove('open');}

async function submitOrder(){
  const name=document.getElementById('f-name').value.trim();
  const phone=document.getElementById('f-phone').value.trim();
  const address=document.getElementById('f-address').value.trim();
  if(!name||!phone||!address){toast('⚠️ من فضلك أكمل جميع البيانات','error');return;}
  const total=cart.reduce((s,i)=>s+i.price*i.qty,0)+20;
  const btn=document.querySelector('.submit-btn');
  btn.disabled=true;btn.textContent='...جاري الإرسال';
  try{
    const res=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,phone,address,total,items:cart})});
    const data=await res.json();
    if(data.success){
      cart=[];saveCart();closeModal();
      toast('🎉 تم إرسال طلبك بنجاح! رقم الطلب: #'+data.order_id,'success');
    }
  }catch(e){toast('❌ خطأ في الاتصال','error');}
  btn.disabled=false;btn.textContent='✅ تأكيد الطلب';
}

saveCart();
loadCategories();
loadProducts();
</script>
</body>
</html>
""",

    # ── ADMIN TEMPLATES ──────────────────────────────────────

    "admin_login": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>دخول الإدارة — زراعتي</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Cairo',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:#0a2e1c;position:relative;overflow:hidden}
body::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 30% 50%,rgba(0,135,90,.35) 0%,transparent 60%),
             radial-gradient(ellipse at 70% 20%,rgba(0,163,108,.2) 0%,transparent 50%);
}
.grid-bg{position:absolute;inset:0;opacity:.06;
  background-image:linear-gradient(#00875a 1px,transparent 1px),linear-gradient(90deg,#00875a 1px,transparent 1px);
  background-size:40px 40px;}
.box{
  position:relative;z-index:1;
  background:rgba(255,255,255,.04);
  backdrop-filter:blur(20px);
  border:1.5px solid rgba(255,255,255,.1);
  border-radius:28px;padding:44px 36px;width:380px;
  box-shadow:0 32px 80px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.1);
  text-align:center;
}
.logo{font-size:56px;margin-bottom:6px;filter:drop-shadow(0 8px 20px rgba(0,135,90,.5))}
h2{font-size:22px;color:#fff;font-weight:900;margin-bottom:4px}
.sub{font-size:13px;color:rgba(255,255,255,.5);margin-bottom:32px}
.fg{margin-bottom:18px;text-align:right}
.fg label{display:block;font-size:12px;color:rgba(255,255,255,.6);margin-bottom:7px;font-weight:700;letter-spacing:.5px}
.fg input{
  width:100%;background:rgba(255,255,255,.08);
  border:1.5px solid rgba(255,255,255,.12);border-radius:14px;
  padding:13px 16px;font-size:14px;font-family:'Cairo',sans-serif;
  color:#fff;outline:none;transition:.2s;
}
.fg input::placeholder{color:rgba(255,255,255,.35)}
.fg input:focus{border-color:#00875a;background:rgba(0,135,90,.12);box-shadow:0 0 0 4px rgba(0,135,90,.15)}
.btn{
  width:100%;background:linear-gradient(135deg,#005c3d,#00875a);
  color:#fff;border:none;border-radius:14px;padding:14px;
  font-size:15px;font-weight:900;font-family:'Cairo',sans-serif;cursor:pointer;
  box-shadow:0 6px 24px rgba(0,135,90,.45);transition:.2s;margin-top:6px;
}
.btn:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(0,135,90,.6)}
.error{background:rgba(239,68,68,.15);border:1.5px solid rgba(239,68,68,.3);color:#fca5a5;border-radius:12px;padding:12px;font-size:13px;margin-bottom:18px}
</style>
</head>
<body>
<div class="grid-bg"></div>
<div class="box">
  <div class="logo">🌿</div>
  <h2>لوحة تحكم زراعتي</h2>
  <p class="sub">أدخل بياناتك للدخول</p>
  {% if error %}<div class="error">⚠️ {{ error }}</div>{% endif %}
  <form method="POST">
    <div class="fg"><label>اسم المستخدم</label><input type="text" name="username" placeholder="admin" required></div>
    <div class="fg"><label>كلمة المرور</label><input type="password" name="password" placeholder="••••••••" required></div>
    <button type="submit" class="btn">دخول →</button>
  </form>
</div>
</body>
</html>
""",

    "admin_base": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>لوحة تحكم زراعتي</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--g:#00875a;--gd:#005c3d;--gl:#00a36c;--bg:#f3f6f4;--sb:240px;--text:#111827;--muted:#6b7280;--border:#e5e7eb;--surface:#fff}
body{font-family:'Cairo',sans-serif;background:var(--bg);display:flex;min-height:100vh;color:var(--text)}

/* SIDEBAR */
.sidebar{width:var(--sb);background:linear-gradient(180deg,var(--gd) 0%,var(--g) 100%);color:#fff;position:fixed;height:100vh;overflow-y:auto;z-index:50;box-shadow:4px 0 24px rgba(0,0,0,.15)}
.sb-logo{padding:24px 20px;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(255,255,255,.12)}
.sb-logo .leaf{font-size:30px;filter:drop-shadow(0 3px 8px rgba(0,0,0,.3))}
.sb-logo-text h3{font-size:17px;font-weight:900;line-height:1}
.sb-logo-text small{font-size:10px;opacity:.6;letter-spacing:.5px}
.sb-section{padding:16px 12px 8px;font-size:10px;font-weight:700;letter-spacing:1.5px;opacity:.5;text-transform:uppercase}
.sidebar a{
  display:flex;align-items:center;gap:12px;padding:12px 16px;margin:2px 8px;
  color:rgba(255,255,255,.75);text-decoration:none;font-size:14px;font-weight:600;
  border-radius:12px;transition:.2s;
}
.sidebar a:hover,.sidebar a.active{background:rgba(255,255,255,.15);color:#fff}
.sidebar a.active{background:rgba(255,255,255,.2);box-shadow:inset 0 0 0 1px rgba(255,255,255,.15)}
.sidebar a .sicon{font-size:18px;width:24px;text-align:center;flex-shrink:0}
.sidebar a .badge{margin-right:auto;background:var(--gold,#f5c842);color:#1a1a1a;border-radius:20px;padding:2px 8px;font-size:10px;font-weight:900}
.sb-divider{height:1px;background:rgba(255,255,255,.1);margin:8px 16px}

/* MAIN */
.main{margin-right:var(--sb);flex:1;padding:28px;overflow-x:auto}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}
.topbar h2{font-size:22px;font-weight:900;color:var(--text)}
.topbar-actions{display:flex;align-items:center;gap:10px}
.greeting{font-size:13px;color:var(--muted);background:var(--surface);padding:8px 16px;border-radius:30px;border:1.5px solid var(--border)}

/* STAT CARDS */
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px}
.stat-card{
  background:var(--surface);border-radius:18px;padding:20px;
  box-shadow:0 2px 12px rgba(0,0,0,.06);border:1.5px solid var(--border);
  position:relative;overflow:hidden;
}
.stat-card::after{content:attr(data-icon);position:absolute;left:-8px;bottom:-12px;font-size:60px;opacity:.08}
.stat-icon{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:14px}
.stat-icon.green{background:#d1fae5}
.stat-icon.blue{background:#dbeafe}
.stat-icon.orange{background:#fef3c7}
.stat-icon.purple{background:#ede9fe}
.stat-val{font-size:26px;font-weight:900;color:var(--text);margin-bottom:4px}
.stat-label{font-size:12px;color:var(--muted);font-weight:600}

/* TABLE */
.card{background:var(--surface);border-radius:18px;padding:22px;box-shadow:0 2px 12px rgba(0,0,0,.06);border:1.5px solid var(--border);margin-bottom:20px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}
.card-title{font-size:16px;font-weight:900;color:var(--text)}
table{width:100%;border-collapse:collapse}
th{background:var(--bg);color:var(--muted);padding:11px 14px;font-size:12px;font-weight:700;text-align:right;letter-spacing:.3px;border-bottom:2px solid var(--border)}
th:first-child{border-radius:0 10px 10px 0}
th:last-child{border-radius:10px 0 0 10px}
td{padding:13px 14px;font-size:13px;border-bottom:1px solid #f3f4f6;vertical-align:middle;transition:.15s}
tr:hover td{background:#f9fdfb}
tr:last-child td{border-bottom:none}

/* BADGES */
.badge{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:800;display:inline-flex;align-items:center;gap:4px}
.badge-جديد{background:#dbeafe;color:#1d4ed8}
.badge-قيد\ التنفيذ,.badge-قيد.التنفيذ{background:#fef3c7;color:#d97706}
.badge-تم\ التوصيل,.badge-تم.التوصيل{background:#d1fae5;color:#065f46}
.badge-ملغي{background:#fee2e2;color:#b91c1c}

/* BUTTONS */
.btn{padding:9px 18px;border-radius:10px;border:none;cursor:pointer;font-size:13px;font-weight:700;font-family:'Cairo',sans-serif;text-decoration:none;display:inline-flex;align-items:center;gap:5px;transition:.2s}
.btn:hover{opacity:.88;transform:translateY(-1px)}
.btn-primary{background:linear-gradient(135deg,var(--gd),var(--g));color:#fff;box-shadow:0 4px 14px rgba(0,135,90,.3)}
.btn-warning{background:#f59e0b;color:#fff}
.btn-danger{background:#ef4444;color:#fff}
.btn-sm{padding:6px 12px;font-size:12px;border-radius:8px}
.btn-outline{background:none;border:1.5px solid var(--border);color:var(--muted)}

/* FORMS */
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fg{margin-bottom:16px}
.fg label{display:block;font-size:12px;font-weight:700;color:var(--muted);margin-bottom:7px;letter-spacing:.3px}
.fg input,.fg select,.fg textarea{
  width:100%;border:2px solid var(--border);border-radius:12px;
  padding:11px 14px;font-size:13px;font-family:'Cairo',sans-serif;
  outline:none;transition:.2s;background:#fff;
}
.fg input:focus,.fg select:focus,.fg textarea:focus{border-color:var(--g);box-shadow:0 0 0 4px rgba(0,135,90,.08)}

/* IMAGE UPLOAD */
.img-upload-zone{
  border:2px dashed var(--border);border-radius:14px;
  padding:24px;text-align:center;cursor:pointer;
  transition:.2s;position:relative;overflow:hidden;background:#fafafa;
}
.img-upload-zone:hover{border-color:var(--g);background:rgba(0,135,90,.03)}
.img-upload-zone.has-img{padding:0;border-style:solid;border-color:var(--g)}
.img-upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.upload-icon{font-size:32px;margin-bottom:8px}
.upload-text{font-size:13px;color:var(--muted);font-weight:600}
.upload-hint{font-size:11px;color:#d1d5db;margin-top:4px}
.img-preview{width:100%;max-height:200px;object-fit:contain;padding:12px;display:none;border-radius:14px}
.img-preview.show{display:block}
.img-remove{
  position:absolute;top:8px;left:8px;
  background:rgba(239,68,68,.9);color:#fff;
  border:none;border-radius:8px;padding:4px 10px;font-size:12px;
  cursor:pointer;font-family:'Cairo',sans-serif;display:none;z-index:2;
}
.img-remove.show{display:block}
.prod-thumb{width:52px;height:52px;border-radius:10px;object-fit:contain;background:#f0f9f5;border:1.5px solid var(--border);padding:3px}
.no-thumb{width:52px;height:52px;border-radius:10px;background:#e8f8f0;display:flex;align-items:center;justify-content:center;font-size:24px}

/* MODAL */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:200;justify-content:center;align-items:center;backdrop-filter:blur(4px)}
.modal-overlay.open{display:flex}
.modal-box{background:#fff;border-radius:20px;padding:28px;width:520px;max-height:88vh;overflow-y:auto;box-shadow:0 24px 60px rgba(0,0,0,.2)}
.modal-title{font-size:18px;font-weight:900;margin-bottom:22px;padding-bottom:14px;border-bottom:2px solid var(--border);display:flex;align-items:center;gap:8px}

@media(max-width:1000px){.stat-grid{grid-template-columns:1fr 1fr}}
@media(max-width:800px){.sidebar{display:none}.main{margin-right:0}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sb-logo">
    <div class="leaf">🌿</div>
    <div class="sb-logo-text"><h3>زراعتي</h3><small>ADMIN PANEL</small></div>
  </div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin" class="{% if page=='home' %}active{% endif %}"><span class="sicon">📊</span> لوحة التحكم</a>
  <a href="/admin/products" class="{% if page=='products' %}active{% endif %}"><span class="sicon">📦</span> المنتجات</a>
  <a href="/admin/orders" class="{% if page=='orders' %}active{% endif %}"><span class="sicon">🛒</span> الطلبات</a>
  <a href="/admin/categories" class="{% if page=='categories' %}active{% endif %}"><span class="sicon">🗂</span> التصنيفات</a>
  <div class="sb-divider"></div>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="sicon">🌐</span> عرض التطبيق</a>
  <a href="/admin/logout"><span class="sicon">🚪</span> تسجيل الخروج</a>
</div>
<div class="main">
{% block content %}{% endblock %}
</div>
</body>
</html>
""",

    "admin_index": """{% extends "admin_base.html" %}
{% set page = "home" %}
{% block content %}
<div class="topbar">
  <h2>📊 لوحة التحكم</h2>
  <div class="topbar-actions">
    <span class="greeting">👋 مرحباً، {{ session.admin }}</span>
  </div>
</div>

<div class="stat-grid">
  <div class="stat-card" data-icon="📦">
    <div class="stat-icon green">📦</div>
    <div class="stat-val">{{ stats.products }}</div>
    <div class="stat-label">إجمالي المنتجات</div>
  </div>
  <div class="stat-card" data-icon="🛒">
    <div class="stat-icon blue">🛒</div>
    <div class="stat-val">{{ stats.orders }}</div>
    <div class="stat-label">إجمالي الطلبات</div>
  </div>
  <div class="stat-card" data-icon="🔔">
    <div class="stat-icon orange">🔔</div>
    <div class="stat-val">{{ stats.new_orders }}</div>
    <div class="stat-label">طلبات جديدة</div>
  </div>
  <div class="stat-card" data-icon="💰">
    <div class="stat-icon purple">💰</div>
    <div class="stat-val">{{ "%.0f"|format(stats.revenue) }} ج</div>
    <div class="stat-label">إجمالي الإيرادات</div>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <span class="card-title">آخر الطلبات</span>
    <a href="/admin/orders" class="btn btn-outline btn-sm">عرض الكل</a>
  </div>
  <table>
    <thead><tr><th>رقم الطلب</th><th>العميل</th><th>الهاتف</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th></tr></thead>
    <tbody>
    {% for o in orders %}
    <tr>
      <td><strong style="color:var(--g)">#{{ o.id }}</strong></td>
      <td><strong>{{ o.customer_name }}</strong></td>
      <td>{{ o.customer_phone }}</td>
      <td><strong>{{ "%.2f"|format(o.total) }} ج</strong></td>
      <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
      <td style="color:var(--muted);font-size:12px">{{ o.created_at[:16] }}</td>
      <td><a href="/admin/orders/{{ o.id }}" class="btn btn-primary btn-sm">عرض</a></td>
    </tr>
    {% else %}
    <tr><td colspan="7" style="text-align:center;padding:40px;color:var(--muted)">لا توجد طلبات بعد</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
""",

    "admin_products": """{% extends "admin_base.html" %}
{% set page = "products" %}
{% block content %}
<div class="topbar">
  <h2>📦 إدارة المنتجات</h2>
  <button class="btn btn-primary" onclick="document.getElementById('add-modal').classList.add('open')">+ إضافة منتج</button>
</div>

<div class="card" style="padding:0;overflow:hidden">
  <table>
    <thead><tr>
      <th>#</th><th>الصورة</th><th>الاسم</th><th>التصنيف</th>
      <th>السعر</th><th>الخصم</th><th>المخزون</th><th>الوحدة</th><th>إجراءات</th>
    </tr></thead>
    <tbody>
    {% for p in products %}
    <tr>
      <td style="color:var(--muted);font-size:12px">{{ p.id }}</td>
      <td>
        {% if p.image_url %}
          <img src="{{ p.image_url }}" class="prod-thumb" alt="{{ p.name }}">
        {% else %}
          <div class="no-thumb">🌿</div>
        {% endif %}
      </td>
      <td><strong>{{ p.name }}</strong><br><span style="font-size:11px;color:var(--muted)">{{ p.description or '' }}</span></td>
      <td><span style="background:#e8f8f0;color:var(--g);padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700">{{ p.cat_name }}</span></td>
      <td><strong style="color:var(--g)">{{ p.price }} ج</strong></td>
      <td>{{ p.old_price or '—' }}</td>
      <td>
        <span style="color:{% if p.stock < 10 %}#ef4444{% else %}#059669{% endif %};font-weight:700">
          {% if p.stock < 10 %}⚠️ {% endif %}{{ p.stock }}
        </span>
      </td>
      <td>{{ p.unit }}</td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn-warning btn-sm" onclick="editProduct({{ p.id }},'{{ p.name }}','{{ p.description or '' }}',{{ p.price }},{{ p.old_price or 0 }},{{ p.stock }},{{ p.category_id }},'{{ p.unit }}','{{ p.image_url or '' }}')">✏️ تعديل</button>
          <a href="/admin/products/delete/{{ p.id }}" class="btn btn-danger btn-sm" onclick="return confirm('تأكيد حذف المنتج؟')">🗑</a>
        </div>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="9" style="text-align:center;padding:50px;color:var(--muted)">لا توجد منتجات — أضف منتجاً جديداً</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>

<!-- MODAL إضافة -->
<div class="modal-overlay" id="add-modal">
  <div class="modal-box">
    <div class="modal-title">➕ إضافة منتج جديد</div>
    <form method="POST" action="/admin/products/add" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>اسم المنتج *</label><input name="name" required placeholder="اسم المنتج"></div>
        <div class="fg"><label>التصنيف *</label>
          <select name="category_id" required>
            {% for c in categories %}<option value="{{ c.id }}">{{ c.icon }} {{ c.name }}</option>{% endfor %}
          </select>
        </div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description" placeholder="وصف مختصر للمنتج"></div>
      <div class="form-row">
        <div class="fg"><label>السعر (ج) *</label><input name="price" type="number" step="0.01" required placeholder="0.00"></div>
        <div class="fg"><label>السعر قبل الخصم</label><input name="old_price" type="number" step="0.01" placeholder="اختياري"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون *</label><input name="stock" type="number" value="0" required></div>
        <div class="fg"><label>وحدة البيع</label>
          <select name="unit"><option>علبة</option><option>كيلو</option><option>لتر</option><option>جرام</option><option>قطعة</option></select>
        </div>
      </div>
      <div class="fg">
        <label>📸 صورة المنتج</label>
        <div class="img-upload-zone" id="add-zone">
          <input type="file" name="image" accept="image/*" onchange="previewImg(this,'add-preview','add-zone','add-remove')">
          <div id="add-placeholder">
            <div class="upload-icon">📸</div>
            <div class="upload-text">انقر لرفع الصورة أو اسحب وأفلت</div>
            <div class="upload-hint">PNG، JPG، WEBP — الحد الأقصى 5 ميجا</div>
          </div>
          <img id="add-preview" class="img-preview" alt="معاينة">
          <button type="button" class="img-remove" id="add-remove" onclick="removeImg('add-preview','add-zone','add-remove','add-placeholder')">✕ إزالة</button>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:6px">
        <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">💾 حفظ المنتج</button>
        <button type="button" class="btn btn-outline" style="flex:1;justify-content:center" onclick="document.getElementById('add-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<!-- MODAL تعديل -->
<div class="modal-overlay" id="edit-modal">
  <div class="modal-box">
    <div class="modal-title">✏️ تعديل المنتج</div>
    <form method="POST" id="edit-form" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>اسم المنتج</label><input name="name" id="e-name" required></div>
        <div class="fg"><label>التصنيف</label>
          <select name="category_id" id="e-cat">
            {% for c in categories %}<option value="{{ c.id }}">{{ c.icon }} {{ c.name }}</option>{% endfor %}
          </select>
        </div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description" id="e-desc"></div>
      <div class="form-row">
        <div class="fg"><label>السعر (ج)</label><input name="price" id="e-price" type="number" step="0.01"></div>
        <div class="fg"><label>السعر قبل الخصم</label><input name="old_price" id="e-oprice" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون</label><input name="stock" id="e-stock" type="number"></div>
        <div class="fg"><label>وحدة البيع</label>
          <select name="unit" id="e-unit"><option>علبة</option><option>كيلو</option><option>لتر</option><option>جرام</option><option>قطعة</option></select>
        </div>
      </div>
      <div class="fg">
        <label>📸 صورة المنتج (اتركه فارغاً للإبقاء على الحالية)</label>
        <div class="img-upload-zone" id="edit-zone">
          <input type="file" name="image" accept="image/*" onchange="previewImg(this,'edit-preview','edit-zone','edit-remove')">
          <div id="edit-placeholder">
            <div class="upload-icon">📸</div>
            <div class="upload-text">انقر لتغيير الصورة</div>
            <div class="upload-hint">أو اتركه فارغاً للإبقاء على الصورة الحالية</div>
          </div>
          <img id="edit-preview" class="img-preview" alt="معاينة">
          <button type="button" class="img-remove" id="edit-remove" onclick="removeImg('edit-preview','edit-zone','edit-remove','edit-placeholder')">✕ إزالة</button>
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:6px">
        <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">💾 حفظ التعديلات</button>
        <button type="button" class="btn btn-outline" style="flex:1;justify-content:center" onclick="document.getElementById('edit-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<script>
function previewImg(input, prevId, zoneId, removeId){
  if(!input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    const prev = document.getElementById(prevId);
    const zone = document.getElementById(zoneId);
    const rem = document.getElementById(removeId);
    prev.src = e.target.result;
    prev.classList.add('show');
    zone.classList.add('has-img');
    rem.classList.add('show');
    zone.querySelector('[id$="-placeholder"]').style.display='none';
  };
  reader.readAsDataURL(input.files[0]);
}

function removeImg(prevId, zoneId, removeId, placeholderId){
  const prev = document.getElementById(prevId);
  const zone = document.getElementById(zoneId);
  const rem = document.getElementById(removeId);
  const ph = document.getElementById(placeholderId);
  prev.src=''; prev.classList.remove('show');
  zone.classList.remove('has-img');
  rem.classList.remove('show');
  ph.style.display='';
  zone.querySelector('input[type=file]').value='';
}

function editProduct(id,name,desc,price,oprice,stock,catId,unit,imageUrl){
  document.getElementById('edit-form').action='/admin/products/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-desc').value=desc;
  document.getElementById('e-price').value=price;
  document.getElementById('e-oprice').value=oprice||'';
  document.getElementById('e-stock').value=stock;
  document.getElementById('e-cat').value=catId;
  document.getElementById('e-unit').value=unit;
  const prev=document.getElementById('edit-preview');
  const zone=document.getElementById('edit-zone');
  const rem=document.getElementById('edit-remove');
  const ph=document.getElementById('edit-placeholder');
  if(imageUrl){
    prev.src=imageUrl; prev.classList.add('show');
    zone.classList.add('has-img'); rem.classList.add('show');
    ph.style.display='none';
  } else {
    prev.src=''; prev.classList.remove('show');
    zone.classList.remove('has-img'); rem.classList.remove('show');
    ph.style.display='';
  }
  document.getElementById('edit-modal').classList.add('open');
}

// Close modals on backdrop click
document.querySelectorAll('.modal-overlay').forEach(m=>{
  m.addEventListener('click',e=>{ if(e.target===m) m.classList.remove('open'); });
});
</script>
{% endblock %}
""",

    "admin_orders": """{% extends "admin_base.html" %}
{% set page = "orders" %}
{% block content %}
<div class="topbar"><h2>🛒 إدارة الطلبات</h2></div>
<div class="card" style="padding:0;overflow:hidden">
  <table>
    <thead><tr>
      <th>#</th><th>العميل</th><th>الهاتف</th><th>العنوان</th>
      <th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>تفاصيل</th>
    </tr></thead>
    <tbody>
    {% for o in orders %}
    <tr>
      <td><strong style="color:var(--g)">#{{ o.id }}</strong></td>
      <td><strong>{{ o.customer_name }}</strong></td>
      <td>{{ o.customer_phone }}</td>
      <td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ o.customer_address }}</td>
      <td><strong>{{ "%.2f"|format(o.total) }} ج</strong></td>
      <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
      <td style="font-size:12px;color:var(--muted)">{{ o.created_at[:16] }}</td>
      <td><a href="/admin/orders/{{ o.id }}" class="btn btn-primary btn-sm">عرض</a></td>
    </tr>
    {% else %}
    <tr><td colspan="8" style="text-align:center;padding:50px;color:var(--muted)">لا توجد طلبات بعد</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
""",

    "admin_order_detail": """{% extends "admin_base.html" %}
{% set page = "orders" %}
{% block content %}
<div class="topbar">
  <h2>📋 تفاصيل الطلب #{{ order.id }}</h2>
  <a href="/admin/orders" class="btn btn-outline">→ الرجوع</a>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
  <div class="card">
    <div class="card-title" style="margin-bottom:16px">👤 بيانات العميل</div>
    <div style="display:flex;flex-direction:column;gap:12px">
      <div><span style="font-size:12px;color:var(--muted);font-weight:700">الاسم</span><div style="font-weight:800;margin-top:3px">{{ order.customer_name }}</div></div>
      <div><span style="font-size:12px;color:var(--muted);font-weight:700">الهاتف</span><div style="font-weight:800;margin-top:3px">{{ order.customer_phone }}</div></div>
      <div><span style="font-size:12px;color:var(--muted);font-weight:700">العنوان</span><div style="font-weight:800;margin-top:3px">{{ order.customer_address }}</div></div>
      <div><span style="font-size:12px;color:var(--muted);font-weight:700">التاريخ</span><div style="margin-top:3px">{{ order.created_at[:16] }}</div></div>
    </div>
  </div>
  <div class="card">
    <div class="card-title" style="margin-bottom:16px">📊 حالة الطلب</div>
    <span class="badge badge-{{ order.status }}" style="font-size:14px;padding:8px 20px;margin-bottom:20px;display:inline-block">{{ order.status }}</span>
    <form method="POST" action="/admin/orders/status/{{ order.id }}">
      <div class="fg">
        <label>تغيير الحالة</label>
        <select name="status">
          <option {% if order.status=='جديد' %}selected{% endif %}>جديد</option>
          <option {% if order.status=='قيد التنفيذ' %}selected{% endif %}>قيد التنفيذ</option>
          <option {% if order.status=='تم التوصيل' %}selected{% endif %}>تم التوصيل</option>
          <option {% if order.status=='ملغي' %}selected{% endif %}>ملغي</option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">تحديث الحالة</button>
    </form>
  </div>
</div>
<div class="card">
  <div class="card-title" style="margin-bottom:18px">🛒 المنتجات المطلوبة</div>
  <table>
    <thead><tr><th>المنتج</th><th>الكمية</th><th>سعر الوحدة</th><th>الإجمالي</th></tr></thead>
    <tbody>
    {% for item in items %}
    <tr>
      <td><strong>{{ item.name }}</strong></td>
      <td>{{ item.qty }}</td>
      <td>{{ item.price }} ج</td>
      <td><strong>{{ "%.2f"|format(item.price * item.qty) }} ج</strong></td>
    </tr>
    {% endfor %}
    <tr style="background:#f0fdf4">
      <td colspan="3"><strong>الإجمالي الكلي</strong></td>
      <td><strong style="color:var(--g);font-size:16px">{{ "%.2f"|format(order.total) }} ج</strong></td>
    </tr>
    </tbody>
  </table>
</div>
{% endblock %}
""",

    "admin_categories": """{% extends "admin_base.html" %}
{% set page = "categories" %}
{% block content %}
<div class="topbar">
  <h2>🗂 إدارة التصنيفات</h2>
  <button class="btn btn-primary" onclick="document.getElementById('add-modal').classList.add('open')">+ إضافة تصنيف</button>
</div>
<div class="card" style="padding:0;overflow:hidden">
  <table>
    <thead><tr><th>#</th><th>الأيقونة</th><th>اسم التصنيف</th><th>عدد المنتجات</th></tr></thead>
    <tbody>
    {% for c in categories %}
    <tr>
      <td style="color:var(--muted);font-size:12px">{{ c.id }}</td>
      <td style="font-size:28px">{{ c.icon }}</td>
      <td><strong>{{ c.name }}</strong></td>
      <td>
        <span style="background:#e8f8f0;color:var(--g);padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700">
          {{ c.count }} منتج
        </span>
      </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
<div class="modal-overlay" id="add-modal">
  <div class="modal-box">
    <div class="modal-title">➕ إضافة تصنيف جديد</div>
    <form method="POST" action="/admin/categories/add">
      <div class="form-row">
        <div class="fg"><label>اسم التصنيف</label><input name="name" required placeholder="مبيدات حشرية..."></div>
        <div class="fg"><label>الأيقونة (Emoji)</label><input name="icon" value="🌿" maxlength="5" style="font-size:24px;text-align:center"></div>
      </div>
      <div style="display:flex;gap:10px">
        <button type="submit" class="btn btn-primary" style="flex:1;justify-content:center">إضافة التصنيف</button>
        <button type="button" class="btn btn-outline" style="flex:1;justify-content:center" onclick="document.getElementById('add-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>
<script>
document.querySelectorAll('.modal-overlay').forEach(m=>{
  m.addEventListener('click',e=>{ if(e.target===m) m.classList.remove('open'); });
});
</script>
{% endblock %}
""",
}


def render(name, **ctx):
    env = Environment()
    tmpl_str = TEMPLATES[name]
    extends_match = re.search(r'{%\s*extends\s*"([^"]+)"\s*%}', tmpl_str)
    if extends_match:
        base_name = extends_match.group(1).replace('.html', '')
        base_str = TEMPLATES[base_name]
        child_blocks = dict(re.findall(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', tmpl_str, re.DOTALL))
        def replace_block(m):
            bname = m.group(1)
            return child_blocks.get(bname, m.group(2))
        result = re.sub(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', replace_block, base_str, flags=re.DOTALL)
        tmpl_str = result
    tmpl = env.from_string(tmpl_str)
    ctx['session'] = session
    return make_response(tmpl.render(**ctx))


DB = "zaraati.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🌿'
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            old_price REAL,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            image_url TEXT DEFAULT '',
            unit TEXT DEFAULT 'علبة',
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            total REAL,
            status TEXT DEFAULT 'جديد',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            qty INTEGER,
            price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        );
    """)
    existing = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        c.executemany("INSERT INTO categories (name, icon) VALUES (?,?)", [
            ("مبيدات حشرية", "🦟"),
            ("أسمدة", "🌱"),
            ("مبيدات فطرية", "🍄"),
            ("مبيدات أعشاب", "🌾"),
        ])
        c.executemany("INSERT INTO products (name,description,price,old_price,stock,category_id,unit,image_url) VALUES (?,?,?,?,?,?,?,?)", [
            ("بيستيسايد برو", "مبيد حشري فعال ضد الآفات", 85, 100, 50, 1, "لتر", ""),
            ("كلورابيرفوس", "مبيد حشري للتربة والنبات", 65, None, 30, 1, "كيلو", ""),
            ("نيتروجين بلس", "سماد نيتروجيني عالي التركيز", 120, 150, 80, 2, "كيلو", ""),
            ("سوبر فوسفات", "سماد فوسفاتي لتحسين الجذور", 55, None, 60, 2, "كيلو", ""),
            ("ريدوميل جولد", "مبيد فطري واسع الطيف", 95, 110, 40, 3, "كيلو", ""),
            ("فيتافاكس", "معالجة بذور ضد الأمراض الفطرية", 75, None, 25, 3, "كيلو", ""),
            ("راوند اب", "مبيد أعشاب غير انتقائي", 110, 130, 35, 4, "لتر", ""),
            ("سيليكت سوبر", "مبيد أعشاب انتقائي", 88, None, 20, 4, "لتر", ""),
        ])
        c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin','admin123')")
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated


# ── API ──────────────────────────────────────────────────────

@app.route("/api/categories")
def api_categories():
    conn = get_db()
    cats = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return jsonify([dict(r) for r in cats])

@app.route("/api/products")
def api_products():
    cat = request.args.get("category")
    conn = get_db()
    if cat:
        rows = conn.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.category_id=?", (cat,)).fetchall()
    else:
        rows = conn.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/<int:pid>")
def api_product(pid):
    conn = get_db()
    row = conn.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?", (pid,)).fetchone()
    conn.close()
    return jsonify(dict(row)) if row else (jsonify({"error": "not found"}), 404)

@app.route("/api/orders", methods=["POST"])
def api_place_order():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO orders (customer_name,customer_phone,customer_address,total) VALUES (?,?,?,?)",
              (data["name"], data["phone"], data["address"], data["total"]))
    oid = c.lastrowid
    for item in data["items"]:
        c.execute("INSERT INTO order_items (order_id,product_id,qty,price) VALUES (?,?,?,?)",
                  (oid, item["id"], item["qty"], item["price"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "order_id": oid})


# ── Static uploads ───────────────────────────────────────────

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ── Admin ────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username=? AND password=?", (u, p)).fetchone()
        conn.close()
        if admin:
            session["admin"] = u
            return redirect("/admin")
        error = "اسم المستخدم أو كلمة المرور غلط"
    return render("admin_login", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")

@app.route("/admin")
@login_required
def admin_index():
    conn = get_db()
    stats = {
        "products": conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "new_orders": conn.execute("SELECT COUNT(*) FROM orders WHERE status='جديد'").fetchone()[0],
        "revenue": conn.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0],
    }
    recent_orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()
    return render("admin_index", stats=stats, orders=recent_orders)

@app.route("/admin/products")
@login_required
def admin_products():
    conn = get_db()
    products = conn.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC").fetchall()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render("admin_products", products=products, categories=categories)

@app.route("/admin/products/add", methods=["POST"])
@login_required
def admin_add_product():
    f = request.form
    image_url = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/static/uploads/{filename}'
    conn = get_db()
    conn.execute("INSERT INTO products (name,description,price,old_price,stock,category_id,unit,image_url) VALUES (?,?,?,?,?,?,?,?)",
        (f["name"], f.get("description", ""), float(f["price"]),
         float(f["old_price"]) if f.get("old_price") else None,
         int(f["stock"]), int(f["category_id"]), f["unit"], image_url))
    conn.commit()
    conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/edit/<int:pid>", methods=["POST"])
@login_required
def admin_edit_product(pid):
    f = request.form
    conn = get_db()
    new_image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_image_url = f'/static/uploads/{filename}'
    if new_image_url:
        conn.execute("UPDATE products SET name=?,description=?,price=?,old_price=?,stock=?,category_id=?,unit=?,image_url=? WHERE id=?",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"], new_image_url, pid))
    else:
        conn.execute("UPDATE products SET name=?,description=?,price=?,old_price=?,stock=?,category_id=?,unit=? WHERE id=?",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"], pid))
    conn.commit()
    conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/delete/<int:pid>")
@login_required
def admin_delete_product(pid):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return redirect("/admin/products")

@app.route("/admin/orders")
@login_required
def admin_orders():
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    conn.close()
    return render("admin_orders", orders=orders)

@app.route("/admin/orders/<int:oid>")
@login_required
def admin_order_detail(oid):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    items = conn.execute("SELECT oi.*,p.name FROM order_items oi LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?", (oid,)).fetchall()
    conn.close()
    return render("admin_order_detail", order=order, items=items)

@app.route("/admin/orders/status/<int:oid>", methods=["POST"])
@login_required
def admin_update_status(oid):
    status = request.form["status"]
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    conn.commit()
    conn.close()
    return redirect(f"/admin/orders/{oid}")

@app.route("/admin/categories")
@login_required
def admin_categories():
    conn = get_db()
    cats = conn.execute("SELECT c.*,(SELECT COUNT(*) FROM products WHERE category_id=c.id) as count FROM categories c").fetchall()
    conn.close()
    return render("admin_categories", categories=cats)

@app.route("/admin/categories/add", methods=["POST"])
@login_required
def admin_add_category():
    conn = get_db()
    conn.execute("INSERT INTO categories (name,icon) VALUES (?,?)", (request.form["name"], request.form["icon"]))
    conn.commit()
    conn.close()
    return redirect("/admin/categories")

@app.route("/")
def index():
    return render("app")


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

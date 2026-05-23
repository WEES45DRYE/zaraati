from flask import Flask, request, jsonify, redirect, url_for, session, make_response
from jinja2 import Environment
import sqlite3, os, json
from functools import wraps

app = Flask(__name__)
app.secret_key = "zaraati_secret_2024"

TEMPLATES = {
    "app": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>زراعتي - متجر الأدوية الزراعية</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--green:#2e7d32;--light-green:#4caf50;--bg:#f5f7f5;--card:#fff;--text:#1a1a1a;--gray:#666;--border:#e0e0e0}
body{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg);color:var(--text);max-width:430px;margin:0 auto;min-height:100vh;position:relative}
/* Header */
.header{background:var(--green);color:#fff;padding:16px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.header h1{font-size:20px;font-weight:700}
.cart-btn{background:rgba(255,255,255,.2);border:none;color:#fff;padding:8px 14px;border-radius:20px;cursor:pointer;font-size:14px;display:flex;align-items:center;gap:6px}
.cart-badge{background:#ff5722;color:#fff;border-radius:50%;padding:2px 7px;font-size:12px;font-weight:700}
/* Nav */
.bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:100%;max-width:430px;background:#fff;display:flex;border-top:1px solid var(--border);z-index:100}
.nav-btn{flex:1;padding:10px 0;border:none;background:none;cursor:pointer;font-size:22px;color:var(--gray);display:flex;flex-direction:column;align-items:center;font-size:11px;gap:2px}
.nav-btn span{font-size:22px}
.nav-btn.active{color:var(--green)}
.nav-btn.active span{filter:drop-shadow(0 0 3px var(--green))}
/* Pages */
.page{display:none;padding:16px;padding-bottom:80px}
.page.active{display:block}
/* Banner */
.banner{background:linear-gradient(135deg,var(--green),#1b5e20);color:#fff;border-radius:16px;padding:20px;margin-bottom:20px;position:relative;overflow:hidden}
.banner::after{content:'🌿';position:absolute;right:-10px;top:-10px;font-size:80px;opacity:.15}
.banner h2{font-size:18px;margin-bottom:6px}
.banner p{font-size:13px;opacity:.85;margin-bottom:14px}
.banner-btn{background:#fff;color:var(--green);border:none;padding:8px 20px;border-radius:20px;font-weight:700;cursor:pointer;font-size:13px}
/* Categories */
.section-title{font-size:16px;font-weight:700;margin-bottom:12px;color:var(--text)}
.cats{display:flex;gap:10px;overflow-x:auto;padding-bottom:6px;scrollbar-width:none}
.cats::-webkit-scrollbar{display:none}
.cat-card{min-width:80px;background:#fff;border-radius:12px;padding:12px 8px;text-align:center;cursor:pointer;border:2px solid transparent;transition:.2s;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.cat-card.active,.cat-card:hover{border-color:var(--light-green);background:#f1f8f1}
.cat-card .icon{font-size:26px}
.cat-card .name{font-size:11px;margin-top:4px;color:var(--gray)}
/* Products */
.products-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.product-card{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.08);cursor:pointer;transition:.2s}
.product-card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.12)}
.product-img{height:110px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);display:flex;align-items:center;justify-content:center;font-size:44px}
.product-info{padding:10px}
.product-name{font-size:13px;font-weight:600;margin-bottom:4px}
.product-unit{font-size:11px;color:var(--gray)}
.product-price{display:flex;align-items:center;gap:6px;margin-top:6px}
.price{color:var(--green);font-weight:700;font-size:15px}
.old-price{color:#aaa;font-size:12px;text-decoration:line-through}
.add-btn{width:100%;margin-top:8px;background:var(--green);color:#fff;border:none;border-radius:8px;padding:7px;cursor:pointer;font-size:13px}
/* Loading */
.loading{text-align:center;padding:40px;color:var(--gray)}
/* Cart Page */
.cart-item{background:#fff;border-radius:12px;padding:14px;margin-bottom:10px;display:flex;gap:12px;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.cart-item-img{width:56px;height:56px;border-radius:10px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0}
.cart-item-info{flex:1}
.cart-item-name{font-size:14px;font-weight:600}
.cart-item-price{font-size:13px;color:var(--green);font-weight:700;margin-top:2px}
.qty-ctrl{display:flex;align-items:center;gap:10px;margin-top:6px}
.qty-btn{background:var(--border);border:none;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}
.qty-num{font-weight:600}
.cart-total-box{background:#fff;border-radius:14px;padding:16px;margin-top:10px;box-shadow:0 1px 6px rgba(0,0,0,.08)}
.total-row{display:flex;justify-content:space-between;padding:6px 0;font-size:14px}
.total-row.final{font-weight:700;font-size:16px;border-top:1px solid var(--border);margin-top:6px;padding-top:12px;color:var(--green)}
.checkout-btn{width:100%;background:var(--green);color:#fff;border:none;border-radius:12px;padding:14px;font-size:16px;font-weight:700;margin-top:14px;cursor:pointer}
.empty{text-align:center;padding:50px 20px;color:var(--gray)}
.empty .icon{font-size:60px;margin-bottom:12px}
/* Order Modal */
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:200;justify-content:center;align-items:flex-end}
.modal.open{display:flex}
.modal-box{background:#fff;width:100%;max-width:430px;border-radius:20px 20px 0 0;padding:24px;max-height:85vh;overflow-y:auto}
.modal-title{font-size:18px;font-weight:700;margin-bottom:18px;text-align:center}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:13px;color:var(--gray);margin-bottom:5px}
.form-group input,.form-group textarea{width:100%;border:1px solid var(--border);border-radius:10px;padding:11px;font-size:14px;font-family:inherit;outline:none;transition:.2s}
.form-group input:focus,.form-group textarea:focus{border-color:var(--light-green)}
.submit-order-btn{width:100%;background:var(--green);color:#fff;border:none;border-radius:12px;padding:14px;font-size:16px;font-weight:700;cursor:pointer;margin-top:6px}
.close-modal{position:absolute;top:16px;left:16px;background:none;border:none;font-size:22px;cursor:pointer;color:var(--gray)}
/* Orders Page */
.order-card{background:#fff;border-radius:14px;padding:14px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.07)}
.order-header{display:flex;justify-content:space-between;margin-bottom:8px}
.order-num{font-weight:700;color:var(--green)}
.order-status{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600}
.status-جديد{background:#e3f2fd;color:#1565c0}
.status-قيد-التنفيذ,.status-قيد\\ التنفيذ{background:#fff3e0;color:#e65100}
.status-تم-التوصيل,.status-تم\\ التوصيل{background:#e8f5e9;color:#2e7d32}
.status-ملغي{background:#ffebee;color:#c62828}
.order-date{font-size:12px;color:var(--gray)}
.order-total{font-size:15px;font-weight:700;color:var(--green);margin-top:4px}
/* Profile */
.profile-header{background:linear-gradient(135deg,var(--green),#1b5e20);color:#fff;border-radius:16px;padding:24px;text-align:center;margin-bottom:16px}
.profile-avatar{width:70px;height:70px;background:rgba(255,255,255,.2);border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:32px}
.menu-item{background:#fff;border-radius:12px;padding:14px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.menu-icon{font-size:20px;width:36px;text-align:center}
.menu-text{flex:1;font-size:14px}
.menu-arrow{color:var(--gray)}
/* Toast */
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:var(--green);color:#fff;padding:10px 24px;border-radius:20px;font-size:14px;font-weight:600;opacity:0;transition:.3s;z-index:300;pointer-events:none;white-space:nowrap}
.toast.show{opacity:1}
/* Spinner */
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--green);border-radius:50%;animation:spin .8s linear infinite;margin:30px auto}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<div class="header">
  <h1>🌿 زراعتي</h1>
  <button class="cart-btn" onclick="showPage('cart')">
    🛒 السلة <span class="cart-badge" id="cart-count">0</span>
  </button>
</div>

<!-- ═══ صفحة الرئيسية ═══ -->
<div class="page active" id="page-home">
  <div class="banner">
    <h2>خصم 20% على الأسمدة</h2>
    <p>عروض هذا الأسبوع على جميع أنواع الأسمدة الزراعية</p>
    <button class="banner-btn" onclick="filterCat(2)">تسوق الآن</button>
  </div>
  <p class="section-title">التصنيفات</p>
  <div class="cats" id="cats-list"><div class="spinner"></div></div>
  <p class="section-title" style="margin-top:18px">المنتجات</p>
  <div class="products-grid" id="products-grid"><div class="spinner"></div></div>
</div>

<!-- ═══ صفحة السلة ═══ -->
<div class="page" id="page-cart">
  <p class="section-title">سلة التسوق</p>
  <div id="cart-list"></div>
  <div id="cart-total"></div>
</div>

<!-- ═══ صفحة الطلبات ═══ -->
<div class="page" id="page-orders">
  <p class="section-title">طلباتي</p>
  <div id="orders-list"><div class="spinner"></div></div>
</div>

<!-- ═══ صفحة الحساب ═══ -->
<div class="page" id="page-profile">
  <div class="profile-header">
    <div class="profile-avatar">👤</div>
    <div style="font-size:18px;font-weight:700">مرحباً بك!</div>
    <div style="font-size:13px;opacity:.8;margin-top:4px">متجر الأدوية الزراعية</div>
  </div>
  <div class="menu-item"><div class="menu-icon">📦</div><div class="menu-text">طلباتي</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon">💬</div><div class="menu-text">استشارة زراعية</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon">⭐</div><div class="menu-text">المفضلة</div><div class="menu-arrow">←</div></div>
  <div class="menu-item"><div class="menu-icon">📞</div><div class="menu-text">تواصل معنا</div><div class="menu-arrow">←</div></div>
</div>

<!-- ═══ نافذة الطلب ═══ -->
<div class="modal" id="order-modal">
  <div class="modal-box">
    <div class="modal-title">إتمام الطلب</div>
    <div class="form-group">
      <label>الاسم</label>
      <input type="text" id="f-name" placeholder="اسمك الكريم">
    </div>
    <div class="form-group">
      <label>رقم الهاتف</label>
      <input type="tel" id="f-phone" placeholder="01xxxxxxxxx">
    </div>
    <div class="form-group">
      <label>العنوان</label>
      <textarea id="f-address" rows="2" placeholder="عنوان التوصيل بالتفصيل" style="resize:none"></textarea>
    </div>
    <div id="order-summary" style="background:#f9f9f9;border-radius:10px;padding:12px;margin-bottom:12px;font-size:13px;color:#555"></div>
    <button class="submit-order-btn" onclick="submitOrder()">✅ تأكيد الطلب</button>
    <button style="width:100%;background:none;border:none;padding:10px;color:var(--gray);cursor:pointer;margin-top:4px" onclick="closeModal()">إلغاء</button>
  </div>
</div>

<!-- ═══ التنقل السفلي ═══ -->
<div class="bottom-nav">
  <button class="nav-btn active" onclick="showPage('home')"><span>🏠</span>الرئيسية</button>
  <button class="nav-btn" onclick="showPage('cart')"><span>🛒</span>السلة</button>
  <button class="nav-btn" onclick="showPage('orders');loadOrders()"><span>📦</span>طلباتي</button>
  <button class="nav-btn" onclick="showPage('profile')"><span>👤</span>حسابي</button>
</div>

<div class="toast" id="toast"></div>

<script>
const API = "";  // نفس السيرفر
let cart = JSON.parse(localStorage.getItem("cart")||"[]");
let allProducts = [];
let activeCat = 0;

// ─── Pages ────────────────────────────────────────────────
function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  const btns = document.querySelectorAll('.nav-btn');
  const idx = {home:0,cart:1,orders:2,profile:3}[name];
  if(idx!==undefined) btns[idx].classList.add('active');
  if(name==='cart') renderCart();
}

// ─── Toast ────────────────────────────────────────────────
function toast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2000);
}

// ─── Categories ──────────────────────────────────────────
async function loadCategories(){
  const res = await fetch(API+'/api/categories');
  const cats = await res.json();
  const el = document.getElementById('cats-list');
  el.innerHTML = `<div class="cat-card active" onclick="filterCat(0,this)"><div class="icon">🌿</div><div class="name">الكل</div></div>`;
  cats.forEach(c=>{
    el.innerHTML += `<div class="cat-card" onclick="filterCat(${c.id},this)"><div class="icon">${c.icon}</div><div class="name">${c.name}</div></div>`;
  });
}

function filterCat(id, el){
  activeCat = id;
  document.querySelectorAll('.cat-card').forEach(c=>c.classList.remove('active'));
  if(el) el.classList.add('active');
  renderProducts(id ? allProducts.filter(p=>p.category_id==id) : allProducts);
}

// ─── Products ─────────────────────────────────────────────
const EMOJIS = {1:"🦟",2:"🌱",3:"🍄",4:"🌾"};

async function loadProducts(){
  const res = await fetch(API+'/api/products');
  allProducts = await res.json();
  renderProducts(allProducts);
}

function renderProducts(products){
  const g = document.getElementById('products-grid');
  if(!products.length){g.innerHTML='<div class="loading">لا توجد منتجات</div>';return;}
  g.innerHTML = products.map(p=>`
    <div class="product-card">
      <div class="product-img">${EMOJIS[p.category_id]||'🌿'}</div>
      <div class="product-info">
        <div class="product-name">${p.name}</div>
        <div class="product-unit">${p.unit}</div>
        <div class="product-price">
          <span class="price">${p.price} ج</span>
          ${p.old_price?`<span class="old-price">${p.old_price} ج</span>`:''}
        </div>
        <button class="add-btn" onclick="addToCart(${p.id},'${p.name}',${p.price},'${p.unit}',${p.category_id})">+ أضف للسلة</button>
      </div>
    </div>`).join('');
}

// ─── Cart ─────────────────────────────────────────────────
function addToCart(id,name,price,unit,catId){
  const existing = cart.find(i=>i.id==id);
  if(existing){ existing.qty++; }
  else { cart.push({id,name,price,unit,catId,qty:1}); }
  saveCart(); toast('✅ تم الإضافة للسلة');
}

function saveCart(){
  localStorage.setItem("cart",JSON.stringify(cart));
  document.getElementById('cart-count').textContent = cart.reduce((s,i)=>s+i.qty,0);
}

function renderCart(){
  const el = document.getElementById('cart-list');
  const tot = document.getElementById('cart-total');
  if(!cart.length){
    el.innerHTML=`<div class="empty"><div class="icon">🛒</div><div>السلة فارغة</div></div>`;
    tot.innerHTML=''; return;
  }
  el.innerHTML = cart.map(i=>`
    <div class="cart-item">
      <div class="cart-item-img">${EMOJIS[i.catId]||'🌿'}</div>
      <div class="cart-item-info">
        <div class="cart-item-name">${i.name}</div>
        <div class="cart-item-price">${i.price} ج / ${i.unit}</div>
        <div class="qty-ctrl">
          <button class="qty-btn" onclick="changeQty(${i.id},-1)">−</button>
          <span class="qty-num">${i.qty}</span>
          <button class="qty-btn" onclick="changeQty(${i.id},1)">+</button>
        </div>
      </div>
      <button onclick="removeItem(${i.id})" style="background:none;border:none;color:#f44336;font-size:20px;cursor:pointer">🗑</button>
    </div>`).join('');
  const subtotal = cart.reduce((s,i)=>s+i.price*i.qty,0);
  tot.innerHTML=`
    <div class="cart-total-box">
      <div class="total-row"><span>المنتجات</span><span>${subtotal.toFixed(2)} ج</span></div>
      <div class="total-row"><span>الشحن</span><span>20 ج</span></div>
      <div class="total-row final"><span>الإجمالي</span><span>${(subtotal+20).toFixed(2)} ج</span></div>
      <button class="checkout-btn" onclick="openModal()">إتمام الطلب 🛒</button>
    </div>`;
}

function changeQty(id,delta){
  const item = cart.find(i=>i.id==id);
  if(!item) return;
  item.qty += delta;
  if(item.qty<=0) cart = cart.filter(i=>i.id!=id);
  saveCart(); renderCart();
}

function removeItem(id){
  cart = cart.filter(i=>i.id!=id);
  saveCart(); renderCart();
}

// ─── Order ────────────────────────────────────────────────
function openModal(){
  if(!cart.length){toast('السلة فارغة!');return;}
  const subtotal = cart.reduce((s,i)=>s+i.price*i.qty,0);
  document.getElementById('order-summary').innerHTML = cart.map(i=>`<div>${i.name} × ${i.qty} = ${(i.price*i.qty).toFixed(2)} ج</div>`).join('')+`<hr style="margin:8px 0"><strong>الإجمالي: ${(subtotal+20).toFixed(2)} ج</strong>`;
  document.getElementById('order-modal').classList.add('open');
}
function closeModal(){ document.getElementById('order-modal').classList.remove('open'); }

async function submitOrder(){
  const name=document.getElementById('f-name').value.trim();
  const phone=document.getElementById('f-phone').value.trim();
  const address=document.getElementById('f-address').value.trim();
  if(!name||!phone||!address){toast('من فضلك أكمل بياناتك');return;}
  const total = cart.reduce((s,i)=>s+i.price*i.qty,0)+20;
  const btn = document.querySelector('.submit-order-btn');
  btn.disabled=true; btn.textContent='...جاري الإرسال';
  try{
    const res = await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,phone,address,total,items:cart})});
    const data = await res.json();
    if(data.success){
      cart=[];saveCart();closeModal();
      toast('✅ تم إرسال طلبك بنجاح! رقم الطلب: '+data.order_id);
      showPage('orders');loadOrders();
    }
  }catch(e){toast('خطأ في الاتصال');}
  btn.disabled=false; btn.textContent='✅ تأكيد الطلب';
}

// ─── Orders ──────────────────────────────────────────────
async function loadOrders(){
  const el = document.getElementById('orders-list');
  el.innerHTML='<div class="spinner"></div>';
  // هنجيب الطلبات من localStorage (لإن مفيش login)
  el.innerHTML='<div class="empty"><div class="icon">📦</div><div>طلباتك ستظهر هنا بعد الشراء</div></div>';
}

// ─── Init ─────────────────────────────────────────────────
saveCart();
loadCategories();
loadProducts();
</script>
</body>
</html>
""",
    "admin_login": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>تسجيل الدخول - زراعتي</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#1b5e20,#2e7d32,#43a047);min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#fff;border-radius:20px;padding:36px 32px;width:360px;box-shadow:0 12px 40px rgba(0,0,0,.2);text-align:center}
.logo{font-size:48px;margin-bottom:8px}
h2{font-size:20px;color:#1a1a1a;margin-bottom:4px}
.sub{font-size:13px;color:#888;margin-bottom:28px}
.form-group{margin-bottom:16px;text-align:right}
label{display:block;font-size:13px;color:#555;margin-bottom:5px;font-weight:600}
input{width:100%;border:1.5px solid #ddd;border-radius:10px;padding:11px 14px;font-size:14px;font-family:inherit;outline:none;transition:.2s}
input:focus{border-color:#4caf50}
.btn{width:100%;background:#2e7d32;color:#fff;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:700;cursor:pointer;margin-top:6px}
.btn:hover{background:#1b5e20}
.error{background:#ffebee;color:#c62828;border-radius:8px;padding:10px;font-size:13px;margin-bottom:16px}
</style>
</head>
<body>
<div class="box">
  <div class="logo">🌿</div>
  <h2>لوحة تحكم زراعتي</h2>
  <p class="sub">سجّل دخولك للمتابعة</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="form-group">
      <label>اسم المستخدم</label>
      <input type="text" name="username" placeholder="admin" required>
    </div>
    <div class="form-group">
      <label>كلمة المرور</label>
      <input type="password" name="password" placeholder="••••••••" required>
    </div>
    <button type="submit" class="btn">دخول ←</button>
  </form>
</div>
</body>
</html>
""",
    "admin_base": """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>لوحة تحكم زراعتي</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--green:#2e7d32;--lg:#4caf50;--bg:#f0f4f0;--sidebar:220px}
body{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg);display:flex;min-height:100vh}
.sidebar{width:var(--sidebar);background:var(--green);color:#fff;position:fixed;height:100vh;overflow-y:auto;z-index:50}
.sidebar-logo{padding:22px 18px;font-size:18px;font-weight:700;border-bottom:1px solid rgba(255,255,255,.15)}
.sidebar-logo span{font-size:22px}
.sidebar a{display:flex;align-items:center;gap:10px;padding:13px 18px;color:rgba(255,255,255,.85);text-decoration:none;font-size:14px;transition:.15s}
.sidebar a:hover,.sidebar a.active{background:rgba(255,255,255,.15);color:#fff}
.sidebar a .icon{font-size:18px;width:22px}
.main{margin-right:var(--sidebar);flex:1;padding:24px}
.top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
.top-bar h2{font-size:20px;color:#1a1a1a}
.top-bar a{color:var(--green);font-size:13px;text-decoration:none}
.stat-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border-radius:14px;padding:18px;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.stat-icon{font-size:28px;margin-bottom:8px}
.stat-val{font-size:24px;font-weight:700;color:var(--green)}
.stat-label{font-size:12px;color:#888;margin-top:2px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07)}
th{background:var(--green);color:#fff;padding:12px 14px;font-size:13px;text-align:right}
td{padding:12px 14px;font-size:13px;border-bottom:1px solid #f0f0f0;vertical-align:middle}
tr:hover td{background:#f9fdf9}
.badge{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block}
.badge-جديد{background:#e3f2fd;color:#1565c0}
.badge-قيد\\ التنفيذ{background:#fff3e0;color:#e65100}
.badge-تم\\ التوصيل{background:#e8f5e9;color:#2e7d32}
.badge-ملغي{background:#ffebee;color:#c62828}
.btn{padding:8px 16px;border-radius:8px;border:none;cursor:pointer;font-size:13px;font-weight:600;text-decoration:none;display:inline-block}
.btn-green{background:var(--green);color:#fff}
.btn-red{background:#f44336;color:#fff}
.btn-orange{background:#ff9800;color:#fff}
.btn-sm{padding:5px 12px;font-size:12px}
.card{background:#fff;border-radius:14px;padding:20px;box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:18px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:13px;color:#555;margin-bottom:5px;font-weight:600}
.form-group input,.form-group select,.form-group textarea{width:100%;border:1px solid #ddd;border-radius:8px;padding:9px 12px;font-size:13px;font-family:inherit;outline:none;transition:.2s}
.form-group input:focus,.form-group select:focus{border-color:var(--lg)}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.4);z-index:200;justify-content:center;align-items:center}
.modal-overlay.open{display:flex}
.modal-box{background:#fff;border-radius:16px;padding:24px;width:500px;max-height:85vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.15)}
.modal-title{font-size:17px;font-weight:700;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #eee}
@media(max-width:900px){.stat-cards{grid-template-columns:1fr 1fr}.sidebar{display:none}.main{margin-right:0}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-logo"><span>🌿</span> زراعتي - الإدارة</div>
  <a href="/admin" class="{% if page=='home' %}active{% endif %}"><span class="icon">📊</span> الرئيسية</a>
  <a href="/admin/products" class="{% if page=='products' %}active{% endif %}"><span class="icon">📦</span> المنتجات</a>
  <a href="/admin/orders" class="{% if page=='orders' %}active{% endif %}"><span class="icon">🛒</span> الطلبات</a>
  <a href="/admin/categories" class="{% if page=='categories' %}active{% endif %}"><span class="icon">🗂</span> التصنيفات</a>
  <a href="/" target="_blank"><span class="icon">🌐</span> التطبيق</a>
  <a href="/admin/logout" style="margin-top:auto"><span class="icon">🚪</span> خروج</a>
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
<div class="top-bar">
  <h2>📊 لوحة التحكم</h2>
  <span style="color:#888;font-size:13px">مرحباً، {{ session.admin }} 👋</span>
</div>

<div class="stat-cards">
  <div class="stat-card">
    <div class="stat-icon">📦</div>
    <div class="stat-val">{{ stats.products }}</div>
    <div class="stat-label">إجمالي المنتجات</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon">🛒</div>
    <div class="stat-val">{{ stats.orders }}</div>
    <div class="stat-label">إجمالي الطلبات</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon">🔔</div>
    <div class="stat-val">{{ stats.new_orders }}</div>
    <div class="stat-label">طلبات جديدة</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon">💰</div>
    <div class="stat-val">{{ "%.0f"|format(stats.revenue) }} ج</div>
    <div class="stat-label">إجمالي الإيرادات</div>
  </div>
</div>

<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <strong>آخر الطلبات</strong>
    <a href="/admin/orders" style="color:var(--green);font-size:13px;text-decoration:none">عرض الكل ←</a>
  </div>
  <table>
    <thead><tr>
      <th>رقم الطلب</th><th>العميل</th><th>الهاتف</th>
      <th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th>
    </tr></thead>
    <tbody>
    {% for o in orders %}
    <tr>
      <td><strong>#{{ o.id }}</strong></td>
      <td>{{ o.customer_name }}</td>
      <td>{{ o.customer_phone }}</td>
      <td>{{ "%.2f"|format(o.total) }} ج</td>
      <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
      <td style="font-size:12px;color:#888">{{ o.created_at[:16] }}</td>
      <td><a href="/admin/orders/{{ o.id }}" class="btn btn-green btn-sm">عرض</a></td>
    </tr>
    {% else %}
    <tr><td colspan="7" style="text-align:center;color:#888;padding:30px">لا توجد طلبات بعد</td></tr>
    {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
""",
    "admin_products": """{% extends "admin_base.html" %}
{% set page = "products" %}
{% block content %}
<div class="top-bar">
  <h2>📦 المنتجات</h2>
  <button class="btn btn-green" onclick="document.getElementById('add-modal').classList.add('open')">+ إضافة منتج</button>
</div>

<table>
  <thead><tr>
    <th>#</th><th>الاسم</th><th>التصنيف</th>
    <th>السعر</th><th>السعر القديم</th><th>المخزون</th><th>الوحدة</th><th>إجراءات</th>
  </tr></thead>
  <tbody>
  {% for p in products %}
  <tr>
    <td>{{ p.id }}</td>
    <td><strong>{{ p.name }}</strong></td>
    <td>{{ p.cat_name }}</td>
    <td>{{ p.price }} ج</td>
    <td>{{ p.old_price or '—' }}</td>
    <td>
      <span style="color:{% if p.stock < 10 %}#f44336{% else %}#2e7d32{% endif %}">
        {{ p.stock }}
      </span>
    </td>
    <td>{{ p.unit }}</td>
    <td style="display:flex;gap:6px">
      <button class="btn btn-orange btn-sm" onclick="editProduct({{ p.id }},'{{ p.name }}','{{ p.description or '' }}',{{ p.price }},{{ p.old_price or 0 }},{{ p.stock }},{{ p.category_id }},'{{ p.unit }}')">تعديل</button>
      <a href="/admin/products/delete/{{ p.id }}" class="btn btn-red btn-sm" onclick="return confirm('حذف المنتج؟')">حذف</a>
    </td>
  </tr>
  {% else %}
  <tr><td colspan="8" style="text-align:center;color:#888;padding:30px">لا توجد منتجات</td></tr>
  {% endfor %}
  </tbody>
</table>

<!-- Modal إضافة -->
<div class="modal-overlay" id="add-modal">
  <div class="modal-box">
    <div class="modal-title">➕ إضافة منتج جديد</div>
    <form method="POST" action="/admin/products/add">
      <div class="form-row">
        <div class="form-group"><label>اسم المنتج *</label><input name="name" required></div>
        <div class="form-group"><label>التصنيف *</label>
          <select name="category_id" required>
            {% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
          </select>
        </div>
      </div>
      <div class="form-group"><label>الوصف</label><input name="description"></div>
      <div class="form-row">
        <div class="form-group"><label>السعر (ج) *</label><input name="price" type="number" step="0.01" required></div>
        <div class="form-group"><label>السعر القديم (اختياري)</label><input name="old_price" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>المخزون *</label><input name="stock" type="number" value="0" required></div>
        <div class="form-group"><label>الوحدة</label>
          <select name="unit">
            <option>علبة</option><option>كيلو</option><option>لتر</option>
            <option>جرام</option><option>قطعة</option>
          </select>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <button type="submit" class="btn btn-green" style="flex:1">حفظ المنتج</button>
        <button type="button" class="btn" style="flex:1;background:#eee;color:#333" onclick="document.getElementById('add-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<!-- Modal تعديل -->
<div class="modal-overlay" id="edit-modal">
  <div class="modal-box">
    <div class="modal-title">✏️ تعديل المنتج</div>
    <form method="POST" id="edit-form">
      <div class="form-row">
        <div class="form-group"><label>اسم المنتج</label><input name="name" id="e-name" required></div>
        <div class="form-group"><label>التصنيف</label>
          <select name="category_id" id="e-cat">
            {% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
          </select>
        </div>
      </div>
      <div class="form-group"><label>الوصف</label><input name="description" id="e-desc"></div>
      <div class="form-row">
        <div class="form-group"><label>السعر</label><input name="price" id="e-price" type="number" step="0.01"></div>
        <div class="form-group"><label>السعر القديم</label><input name="old_price" id="e-oprice" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>المخزون</label><input name="stock" id="e-stock" type="number"></div>
        <div class="form-group"><label>الوحدة</label>
          <select name="unit" id="e-unit">
            <option>علبة</option><option>كيلو</option><option>لتر</option>
            <option>جرام</option><option>قطعة</option>
          </select>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <button type="submit" class="btn btn-green" style="flex:1">حفظ التعديلات</button>
        <button type="button" class="btn" style="flex:1;background:#eee;color:#333" onclick="document.getElementById('edit-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<script>
function editProduct(id,name,desc,price,oprice,stock,catId,unit){
  document.getElementById('edit-form').action='/admin/products/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-desc').value=desc;
  document.getElementById('e-price').value=price;
  document.getElementById('e-oprice').value=oprice||'';
  document.getElementById('e-stock').value=stock;
  document.getElementById('e-cat').value=catId;
  document.getElementById('e-unit').value=unit;
  document.getElementById('edit-modal').classList.add('open');
}
</script>
{% endblock %}
""",
    "admin_orders": """{% extends "admin_base.html" %}
{% set page = "orders" %}
{% block content %}
<div class="top-bar"><h2>🛒 الطلبات</h2></div>
<table>
  <thead><tr>
    <th>#</th><th>العميل</th><th>الهاتف</th><th>العنوان</th>
    <th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>تفاصيل</th>
  </tr></thead>
  <tbody>
  {% for o in orders %}
  <tr>
    <td><strong>#{{ o.id }}</strong></td>
    <td>{{ o.customer_name }}</td>
    <td>{{ o.customer_phone }}</td>
    <td style="max-width:140px;overflow:hidden;text-overflow:ellipsis">{{ o.customer_address }}</td>
    <td><strong>{{ "%.2f"|format(o.total) }} ج</strong></td>
    <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
    <td style="font-size:12px;color:#888">{{ o.created_at[:16] }}</td>
    <td><a href="/admin/orders/{{ o.id }}" class="btn btn-green btn-sm">عرض</a></td>
  </tr>
  {% else %}
  <tr><td colspan="8" style="text-align:center;color:#888;padding:30px">لا توجد طلبات بعد</td></tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
""",
    "admin_order_detail": """{% extends "admin_base.html" %}
{% set page = "orders" %}
{% block content %}
<div class="top-bar">
  <h2>📋 تفاصيل الطلب #{{ order.id }}</h2>
  <a href="/admin/orders">← الرجوع</a>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
  <div class="card">
    <strong style="font-size:15px">👤 بيانات العميل</strong>
    <hr style="margin:12px 0">
    <p><b>الاسم:</b> {{ order.customer_name }}</p>
    <p style="margin-top:8px"><b>الهاتف:</b> {{ order.customer_phone }}</p>
    <p style="margin-top:8px"><b>العنوان:</b> {{ order.customer_address }}</p>
    <p style="margin-top:8px"><b>التاريخ:</b> {{ order.created_at[:16] }}</p>
  </div>
  <div class="card">
    <strong style="font-size:15px">📊 حالة الطلب</strong>
    <hr style="margin:12px 0">
    <span class="badge badge-{{ order.status }}" style="font-size:14px;padding:6px 16px">{{ order.status }}</span>
    <form method="POST" action="/admin/orders/status/{{ order.id }}" style="margin-top:16px">
      <div class="form-group">
        <label>تغيير الحالة</label>
        <select name="status">
          <option {% if order.status=='جديد' %}selected{% endif %}>جديد</option>
          <option {% if order.status=='قيد التنفيذ' %}selected{% endif %}>قيد التنفيذ</option>
          <option {% if order.status=='تم التوصيل' %}selected{% endif %}>تم التوصيل</option>
          <option {% if order.status=='ملغي' %}selected{% endif %}>ملغي</option>
        </select>
      </div>
      <button type="submit" class="btn btn-green">تحديث الحالة</button>
    </form>
  </div>
</div>

<div class="card">
  <strong style="font-size:15px">🛒 المنتجات المطلوبة</strong>
  <hr style="margin:12px 0">
  <table>
    <thead><tr><th>المنتج</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr></thead>
    <tbody>
    {% for item in items %}
    <tr>
      <td>{{ item.name }}</td>
      <td>{{ item.qty }}</td>
      <td>{{ item.price }} ج</td>
      <td><strong>{{ "%.2f"|format(item.price * item.qty) }} ج</strong></td>
    </tr>
    {% endfor %}
    <tr style="background:#f9fdf9">
      <td colspan="3"><strong>الإجمالي</strong></td>
      <td><strong style="color:var(--green);font-size:15px">{{ "%.2f"|format(order.total) }} ج</strong></td>
    </tr>
    </tbody>
  </table>
</div>
{% endblock %}
""",
    "admin_categories": """{% extends "admin_base.html" %}
{% set page = "categories" %}
{% block content %}
<div class="top-bar">
  <h2>🗂 التصنيفات</h2>
  <button class="btn btn-green" onclick="document.getElementById('add-modal').classList.add('open')">+ إضافة تصنيف</button>
</div>

<table>
  <thead><tr><th>#</th><th>الأيقونة</th><th>الاسم</th><th>عدد المنتجات</th></tr></thead>
  <tbody>
  {% for c in categories %}
  <tr>
    <td>{{ c.id }}</td>
    <td style="font-size:24px">{{ c.icon }}</td>
    <td><strong>{{ c.name }}</strong></td>
    <td>{{ c.count }} منتج</td>
  </tr>
  {% endfor %}
  </tbody>
</table>

<div class="modal-overlay" id="add-modal">
  <div class="modal-box">
    <div class="modal-title">➕ إضافة تصنيف</div>
    <form method="POST" action="/admin/categories/add">
      <div class="form-row">
        <div class="form-group"><label>اسم التصنيف</label><input name="name" required></div>
        <div class="form-group"><label>الأيقونة (emoji)</label><input name="icon" value="🌿" maxlength="5" style="font-size:20px"></div>
      </div>
      <div style="display:flex;gap:10px">
        <button type="submit" class="btn btn-green" style="flex:1">إضافة</button>
        <button type="button" class="btn" style="flex:1;background:#eee;color:#333" onclick="document.getElementById('add-modal').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}
""",
}

def render(name, **ctx):
    from jinja2 import Environment
    env = Environment()
    # handle extends
    tmpl_str = TEMPLATES[name]
    # simple extends handling
    import re
    extends_match = re.search(r'{%\s*extends\s*"([^"]+)"\s*%}', tmpl_str)
    if extends_match:
        base_name = extends_match.group(1).replace('.html','')
        base_str = TEMPLATES[base_name]
        # get blocks from child
        child_blocks = dict(re.findall(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', tmpl_str, re.DOTALL))
        # replace blocks in base
        def replace_block(m):
            bname = m.group(1)
            return child_blocks.get(bname, m.group(2))
        result = re.sub(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', replace_block, base_str, flags=re.DOTALL)
        tmpl_str = result
    tmpl = env.from_string(tmpl_str)
    ctx['session'] = session
    return make_response(tmpl.render(**ctx))

DB = "zaraati.db"

# ─── قاعدة البيانات ─────────────────────────────────────────
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
    # بيانات أولية
    existing = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing == 0:
        c.executemany("INSERT INTO categories (name, icon) VALUES (?,?)", [
            ("مبيدات حشرية","🦟"),("أسمدة","🌱"),("مبيدات فطرية","🍄"),("مبيدات أعشاب","🌾"),
        ])
        c.executemany("""INSERT INTO products (name,description,price,old_price,stock,category_id,unit) VALUES (?,?,?,?,?,?,?)""", [
            ("بيستيسايد برو","مبيد حشري فعال ضد الآفات",85,100,50,1,"لتر"),
            ("كلورابيرفوس","مبيد حشري للتربة والنبات",65,None,30,1,"كيلو"),
            ("نيتروجين بلس","سماد نيتروجيني عالي التركيز",120,150,80,2,"كيلو"),
            ("سوبر فوسفات","سماد فوسفاتي لتحسين الجذور",55,None,60,2,"كيلو"),
            ("ريدوميل جولد","مبيد فطري واسع الطيف",95,110,40,3,"كيلو"),
            ("فيتافاكس","معالجة بذور ضد الأمراض الفطرية",75,None,25,3,"كيلو"),
            ("راوند اب","مبيد أعشاب غير انتقائي",110,130,35,4,"لتر"),
            ("سيليكت سوبر","مبيد أعشاب انتقائي",88,None,20,4,"لتر"),
        ])
        c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin','admin123')")
    conn.commit()
    conn.close()

# ─── Admin Auth ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

# ─── API للتطبيق ─────────────────────────────────────────────
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
    return jsonify(dict(row)) if row else (jsonify({"error":"not found"}),404)

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

# ─── Admin Panel ──────────────────────────────────────────────
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username=? AND password=?", (u,p)).fetchone()
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
    conn = get_db()
    conn.execute("INSERT INTO products (name,description,price,old_price,stock,category_id,unit) VALUES (?,?,?,?,?,?,?)",
        (f["name"], f["description"], float(f["price"]),
         float(f["old_price"]) if f.get("old_price") else None,
         int(f["stock"]), int(f["category_id"]), f["unit"]))
    conn.commit(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/edit/<int:pid>", methods=["POST"])
@login_required
def admin_edit_product(pid):
    f = request.form
    conn = get_db()
    conn.execute("UPDATE products SET name=?,description=?,price=?,old_price=?,stock=?,category_id=?,unit=? WHERE id=?",
        (f["name"], f["description"], float(f["price"]),
         float(f["old_price"]) if f.get("old_price") else None,
         int(f["stock"]), int(f["category_id"]), f["unit"], pid))
    conn.commit(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/delete/<int:pid>")
@login_required
def admin_delete_product(pid):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit(); conn.close()
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
    items = conn.execute("""SELECT oi.*,p.name FROM order_items oi 
        LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""", (oid,)).fetchall()
    conn.close()
    return render("admin_order_detail", order=order, items=items)

@app.route("/admin/orders/status/<int:oid>", methods=["POST"])
@login_required
def admin_update_status(oid):
    status = request.form["status"]
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
    conn.commit(); conn.close()
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
    conn.commit(); conn.close()
    return redirect("/admin/categories")

# ─── التطبيق الرئيسي ──────────────────────────────────────────
@app.route("/")
def index():
    return render("app")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

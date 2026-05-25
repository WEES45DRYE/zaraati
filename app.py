from flask import Flask, request, jsonify, redirect, session, make_response
import os, re, base64
from functools import wraps
from jinja2 import Environment
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "zaraati_secret_2024"

DATABASE_URL = os.environ.get("DATABASE_URL", "")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def get_setting(key, default=''):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=%s", (key,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row['value'] if row else default
    except:
        return default

def set_setting(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value=%s",
                (key, value, value))
    conn.commit(); cur.close(); conn.close()

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '🌿',
            type TEXT DEFAULT 'main'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            old_price REAL,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            image_url TEXT DEFAULT '',
            unit TEXT DEFAULT 'علبة',
            featured INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_name TEXT,
            customer_phone TEXT,
            customer_address TEXT,
            total REAL,
            status TEXT DEFAULT 'جديد',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            qty INTEGER,
            price REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT UNIQUE,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed data only if empty
    cur.execute("SELECT COUNT(*) FROM categories")
    count = cur.fetchone()['count']
    if count == 0:
        cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)", ("المبيدات","🦟","main"))
        cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)", ("الأسمدة","🌱","main"))
        cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)", ("الأدوية الزراعية","💊","main"))
        cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)", ("العروض","🏷️","promo"))

        products = [
            ("إيميداكلوبريد SC 5%","مبيد حشري فعال ضد الآفات الماصة",450,500,50,1,"لتر",1),
            ("جليفوسات SL 48%","مبيد أعشاب غير انتقائي",320,None,30,1,"لتر",1),
            ("ريفوسول WP 72%","مبيد فطري واسع الطيف",280,320,40,1,"كيلو",1),
            ("نترات كالسيوم","سماد نيتروجيني عالي الجودة",220,None,60,2,"كيلو",1),
            ("هيوميك أسيد","محسن تربة عضوي",180,200,45,2,"كيلو",1),
            ("سوبر فوسفات","سماد فوسفاتي متكامل",150,None,55,2,"كيلو",0),
            ("ريدوميل جولد","مبيد فطري للتربة والنبات",350,400,25,3,"كيلو",1),
            ("فيتافاكس","معالجة بذور ضد الأمراض",190,None,30,3,"كيلو",0),
        ]
        for p in products:
            cur.execute("""INSERT INTO products (name,description,price,old_price,stock,category_id,unit,featured)
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", p)

        cur.execute("INSERT INTO admins (username,password) VALUES (%s,%s) ON CONFLICT DO NOTHING", ('admin','admin123'))

        defaults = [
            ('logo_type','emoji'),('logo_emoji','🌿'),('logo_image',''),
            ('banner_image',''),('site_name','الزراعة'),
        ]
        for k,v in defaults:
            cur.execute("INSERT INTO settings (key,value) VALUES (%s,%s) ON CONFLICT DO NOTHING", (k,v))

    conn.commit(); cur.close(); conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

jinja_env = Environment()

def render(tmpl_str, **ctx):
    ctx['session'] = session
    t = jinja_env.from_string(tmpl_str)
    return make_response(t.render(**ctx))

# ══════════════════════════════════════════════════════════════
# STATIC UPLOADS
# ══════════════════════════════════════════════════════════════
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ══════════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════════
@app.route("/api/categories")
def api_categories():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY id")
    cats = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in cats])

@app.route("/api/products")
def api_products():
    cat = request.args.get("category")
    search = request.args.get("search","")
    conn = get_db(); cur = conn.cursor()
    q = "SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id"
    params = []
    if cat:
        q += " WHERE p.category_id=%s"
        params.append(cat)
    if search:
        q += " AND p.name ILIKE %s" if cat else " WHERE p.name ILIKE %s"
        params.append(f"%{search}%")
    cur.execute(q, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/featured")
def api_featured():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.featured=1 LIMIT 8")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/orders", methods=["POST"])
def api_place_order():
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO orders (customer_name,customer_phone,customer_address,total) VALUES (%s,%s,%s,%s) RETURNING id",
                (data["name"], data["phone"], data["address"], data["total"]))
    oid = cur.fetchone()['id']
    for item in data["items"]:
        cur.execute("INSERT INTO order_items (order_id,product_id,qty,price) VALUES (%s,%s,%s,%s)",
                    (oid, item["id"], item["qty"], item["price"]))
    try:
        cur.execute("INSERT INTO customers (name,phone,address) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (data["name"], data["phone"], data["address"]))
    except: pass
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "order_id": oid})

# ══════════════════════════════════════════════════════════════
# ADMIN
# ══════════════════════════════════════════════════════════════
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (u,p))
        admin = cur.fetchone()
        cur.close(); conn.close()
        if admin:
            session["admin"] = u
            return redirect("/admin")
        error = "اسم المستخدم أو كلمة المرور غلط"
    return render(TMPL_LOGIN, error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")

@app.route("/admin")
@login_required
def admin_index():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products"); stats_p = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders"); stats_o = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='جديد'"); stats_n = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders"); stats_r = cur.fetchone()['coalesce']
    cur.execute("SELECT COUNT(*) FROM customers"); stats_c = cur.fetchone()['count']
    stats = {"products":stats_p,"orders":stats_o,"new_orders":stats_n,"revenue":stats_r,"customers":stats_c}
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 7")
    recent_orders = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_INDEX, stats=stats, orders=recent_orders)

@app.route("/admin/products")
@login_required
def admin_products():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC")
    products = cur.fetchall()
    cur.execute("SELECT * FROM categories ORDER BY id")
    categories = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_PRODUCTS, products=products, categories=categories)

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
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO products (name,description,price,old_price,stock,category_id,unit,featured,image_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (f["name"], f.get("description",""), float(f["price"]),
         float(f["old_price"]) if f.get("old_price") else None,
         int(f["stock"]), int(f["category_id"]), f["unit"],
         1 if f.get("featured") else 0, image_url))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/edit/<int:pid>", methods=["POST"])
@login_required
def admin_edit_product(pid):
    f = request.form
    new_image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_image_url = f'/static/uploads/{filename}'
    conn = get_db(); cur = conn.cursor()
    if new_image_url:
        cur.execute("UPDATE products SET name=%s,description=%s,price=%s,old_price=%s,stock=%s,category_id=%s,unit=%s,featured=%s,image_url=%s WHERE id=%s",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"],
             1 if f.get("featured") else 0, new_image_url, pid))
    else:
        cur.execute("UPDATE products SET name=%s,description=%s,price=%s,old_price=%s,stock=%s,category_id=%s,unit=%s,featured=%s WHERE id=%s",
            (f["name"], f.get("description",""), float(f["price"]),
             float(f["old_price"]) if f.get("old_price") else None,
             int(f["stock"]), int(f["category_id"]), f["unit"],
             1 if f.get("featured") else 0, pid))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/products/delete/<int:pid>")
@login_required
def admin_delete_product(pid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/products")

@app.route("/admin/categories")
@login_required
def admin_categories():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT c.*,(SELECT COUNT(*) FROM products WHERE category_id=c.id) as count FROM categories c ORDER BY c.id")
    cats = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_CATS, categories=cats)

@app.route("/admin/categories/add", methods=["POST"])
@login_required
def admin_add_category():
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s)",
        (request.form["name"], request.form["icon"], request.form.get("type","main")))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/categories/edit/<int:cid>", methods=["POST"])
@login_required
def admin_edit_category(cid):
    f = request.form
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE categories SET name=%s,icon=%s,type=%s WHERE id=%s",
        (f["name"], f["icon"], f.get("type","main"), cid))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/categories/delete/<int:cid>")
@login_required
def admin_delete_category(cid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE products SET category_id=NULL WHERE category_id=%s", (cid,))
    cur.execute("DELETE FROM categories WHERE id=%s", (cid,))
    conn.commit(); cur.close(); conn.close()
    return redirect("/admin/categories")

@app.route("/admin/orders")
@login_required
def admin_orders():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_ORDERS, orders=orders)

@app.route("/admin/orders/<int:oid>")
@login_required
def admin_order_detail(oid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=%s", (oid,))
    order = cur.fetchone()
    cur.execute("SELECT oi.*,p.name FROM order_items oi LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=%s", (oid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_ORDER_DETAIL, order=order, items=items)

@app.route("/admin/orders/status/<int:oid>", methods=["POST"])
@login_required
def admin_update_status(oid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (request.form["status"], oid))
    conn.commit(); cur.close(); conn.close()
    return redirect(f"/admin/orders/{oid}")

@app.route("/admin/customers")
@login_required
def admin_customers():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY created_at DESC")
    customers = cur.fetchall()
    cur.close(); conn.close()
    return render(TMPL_ADMIN_CUSTOMERS, customers=customers)

@app.route("/admin/settings")
@login_required
def admin_settings():
    settings = {
        'logo_type': get_setting('logo_type', 'emoji'),
        'logo_emoji': get_setting('logo_emoji', '🌿'),
        'logo_image': get_setting('logo_image', ''),
        'banner_image': get_setting('banner_image', ''),
        'site_name': get_setting('site_name', 'الزراعة'),
    }
    return render(TMPL_ADMIN_SETTINGS, settings=settings)

@app.route("/admin/settings/save", methods=["POST"])
@login_required
def admin_settings_save():
    f = request.form
    if f.get('site_name'):
        set_setting('site_name', f['site_name'])
    logo_type = f.get('logo_type', 'emoji')
    set_setting('logo_type', logo_type)
    if logo_type == 'emoji' and f.get('logo_emoji'):
        set_setting('logo_emoji', f['logo_emoji'])
    if logo_type == 'image' and 'logo_image' in request.files:
        file = request.files['logo_image']
        if file and file.filename and allowed_file(file.filename):
            filename = 'logo_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('logo_image', f'/static/uploads/{filename}')
    if 'banner_image' in request.files:
        file = request.files['banner_image']
        if file and file.filename and allowed_file(file.filename):
            filename = 'banner_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            set_setting('banner_image', f'/static/uploads/{filename}')
    if f.get('remove_banner'):
        set_setting('banner_image', '')
    if f.get('remove_logo_image'):
        set_setting('logo_image', '')
        set_setting('logo_type', 'emoji')
    return redirect("/admin/settings")

@app.route("/")
def index():
    settings = {
        'logo_type': get_setting('logo_type', 'emoji'),
        'logo_emoji': get_setting('logo_emoji', '🌿'),
        'logo_image': get_setting('logo_image', ''),
        'banner_image': get_setting('banner_image', ''),
        'site_name': get_setting('site_name', 'الزراعة'),
    }
    return render(TMPL_APP, **settings)

@app.before_request
def setup():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

_db_initialized = False

# ══════════════════════════════════════════════════════════════
# TEMPLATES
# ══════════════════════════════════════════════════════════════

TMPL_APP = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{{ site_name }} - للمبيدات والأسمدة والأدوية الزراعية</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--green:#1a5c2a;--lg:#2e7d32;--lgg:#4caf50;--bg:#f4f7f4;--white:#fff;--text:#1a1a1a;--gray:#666;--border:#e0e0e0;--red:#e53935}
body{font-family:'Cairo',sans-serif;background:var(--bg);color:var(--text)}
/* ── Header ── */
.header{background:var(--green);color:#fff;position:sticky;top:0;z-index:200;box-shadow:0 2px 12px rgba(0,0,0,.3)}
.header-top{display:flex;align-items:center;gap:12px;padding:10px 16px}
.logo{display:flex;align-items:center;gap:8px;text-decoration:none;color:#fff;flex-shrink:0}
.logo-icon{width:40px;height:40px;background:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;overflow:hidden;flex-shrink:0}
.logo-icon img{width:100%;height:100%;object-fit:contain;padding:3px}
.logo-text{font-size:15px;font-weight:900;line-height:1.1}
.logo-sub{font-size:9px;opacity:.8;font-weight:400}
.search-bar{flex:1;display:flex;gap:0;max-width:500px;margin:0 auto}
.search-bar input{flex:1;border:none;padding:9px 14px;font-family:'Cairo',sans-serif;font-size:13px;border-radius:6px 0 0 6px;outline:none}
.search-bar button{background:var(--lgg);color:#fff;border:none;padding:9px 16px;border-radius:0 6px 6px 0;cursor:pointer;font-size:16px}
.header-actions{display:flex;gap:8px;flex-shrink:0}
.hbtn{background:rgba(255,255,255,.15);border:none;color:#fff;padding:8px 12px;border-radius:8px;cursor:pointer;font-size:12px;font-family:'Cairo',sans-serif;display:flex;align-items:center;gap:5px;position:relative}
.badge{background:var(--red);color:#fff;border-radius:50%;width:18px;height:18px;font-size:10px;display:flex;align-items:center;justify-content:center;position:absolute;top:-5px;right:-5px;font-weight:700}
/* ── Mobile search bar (hidden by default, shown when search icon clicked) ── */
.mobile-search-bar{display:none;padding:0 12px 10px;animation:slideDown .2s ease}
.mobile-search-bar input{width:100%;border:none;padding:9px 14px;font-family:'Cairo',sans-serif;font-size:13px;border-radius:10px;outline:none;background:rgba(255,255,255,.95)}
@keyframes slideDown{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
.mobile-search-bar.open{display:block}
/* ── Nav ── */
.nav{background:var(--lg);display:flex;overflow-x:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a{color:rgba(255,255,255,.85);text-decoration:none;padding:10px 16px;font-size:13px;white-space:nowrap;border-bottom:2px solid transparent;transition:.2s}
.nav a:hover,.nav a.active{color:#fff;border-bottom-color:#fff;background:rgba(255,255,255,.1)}
/* ══ MOBILE HEADER ══ */
@media(max-width:600px){
  .header-top{padding:8px 12px;gap:8px}
  /* اللوجو أصغر */
  .logo-icon{width:32px;height:32px;font-size:18px;border-radius:8px}
  .logo-text{font-size:13px}
  .logo-sub{font-size:8px}
  /* إخفاء شريط البحث الكبير */
  .search-bar{display:none}
  /* أزرار الهيدر أصغر */
  .hbtn{padding:6px 10px;font-size:11px;border-radius:6px}
  /* زر البحث على الموبايل */
  .search-icon-btn{display:flex !important}
  /* Nav أصغر */
  .nav a{padding:8px 12px;font-size:12px}
}
@media(min-width:601px){
  .search-icon-btn{display:none !important}
}
/* ── Banner ── */
.banner{background:linear-gradient(135deg,#1a5c2a 0%,#2e7d32 40%,#388e3c 100%);color:#fff;padding:32px 20px;position:relative;overflow:hidden;min-height:200px;display:flex;align-items:center}
.banner-content{position:relative;z-index:1;flex:1}
.banner h1{font-size:22px;font-weight:900;margin-bottom:6px;line-height:1.3}
.banner p{font-size:13px;opacity:.85;margin-bottom:16px;line-height:1.6}
.banner-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.banner-tag{background:rgba(255,255,255,.2);padding:3px 10px;border-radius:20px;font-size:11px}
.banner-btn{background:#fff;color:var(--green);border:none;padding:10px 24px;border-radius:25px;font-weight:700;font-size:14px;cursor:pointer;font-family:'Cairo',sans-serif}
/* صورة البانر - تغطي كل البانر كـ background */
.banner-bg-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.35;z-index:0}
.banner-emoji-side{font-size:100px;opacity:.15;position:absolute;left:-10px;top:50%;transform:translateY(-50%);z-index:0}
/* ── Sections ── */
.section{padding:16px}
.sec-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.sec-title{font-size:16px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px}
.sec-title::before{content:'';width:4px;height:18px;background:var(--lgg);border-radius:2px;display:inline-block}
.view-all{color:var(--lgg);font-size:13px;text-decoration:none;font-weight:600}
/* ── Cat Cards ── */
.cats-scroll{display:flex;gap:10px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}
.cats-scroll::-webkit-scrollbar{display:none}
.cat-card{min-width:90px;background:#fff;border-radius:12px;padding:14px 10px;text-align:center;cursor:pointer;border:2px solid transparent;transition:.2s;box-shadow:0 1px 6px rgba(0,0,0,.07);flex-shrink:0}
.cat-card:hover,.cat-card.active{border-color:var(--lgg);background:#f1f8e9}
.cat-icon{font-size:28px;margin-bottom:6px}
.cat-name{font-size:12px;color:var(--gray);font-weight:600}
/* ── Products Grid ── */
.products-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.prod-card{background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,.08);cursor:pointer;transition:.2s;position:relative}
.prod-card:hover{transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.12)}
.prod-badge{position:absolute;top:8px;right:8px;background:var(--red);color:#fff;padding:3px 8px;border-radius:20px;font-size:10px;font-weight:700}
.prod-img{height:120px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);display:flex;align-items:center;justify-content:center;font-size:50px;overflow:hidden}
.prod-img img{width:100%;height:100%;object-fit:contain;padding:10px}
.prod-info{padding:10px}
.prod-name{font-size:13px;font-weight:700;margin-bottom:2px;line-height:1.3}
.prod-desc{font-size:11px;color:var(--gray);margin-bottom:6px;line-height:1.4}
.prod-unit{font-size:11px;color:#888;margin-bottom:6px}
.prod-footer{display:flex;justify-content:space-between;align-items:center}
.prod-prices{display:flex;flex-direction:column}
.prod-price{color:var(--lgg);font-weight:900;font-size:15px}
.prod-old{color:#aaa;font-size:11px;text-decoration:line-through}
.add-cart-btn{background:var(--green);color:#fff;border:none;width:32px;height:32px;border-radius:50%;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.2s}
.add-cart-btn:hover{background:var(--lgg);transform:scale(1.1)}
/* ── Features ── */
.features{background:#fff;margin:0 16px 16px;border-radius:14px;padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.feat-item{display:flex;align-items:flex-start;gap:10px}
.feat-icon{font-size:24px;flex-shrink:0}
.feat-title{font-size:12px;font-weight:700;margin-bottom:2px}
.feat-sub{font-size:11px;color:var(--gray);line-height:1.4}
/* ── Bottom Nav ── */
.bottom-nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:1px solid var(--border);display:flex;z-index:200;box-shadow:0 -2px 12px rgba(0,0,0,.08)}
.bnav-btn{flex:1;padding:8px 4px;border:none;background:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:2px;color:var(--gray);font-family:'Cairo',sans-serif;font-size:10px;transition:.2s}
.bnav-btn span{font-size:22px}
.bnav-btn.active{color:var(--green)}
/* ── Pages ── */
.page{display:none;padding-bottom:70px}
.page.active{display:block}
/* ── Cart ── */
.cart-item{background:#fff;border-radius:12px;margin:0 16px 10px;padding:12px;display:flex;gap:10px;align-items:center;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.cart-img{width:56px;height:56px;border-radius:10px;background:linear-gradient(135deg,#e8f5e9,#c8e6c9);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;overflow:hidden}
.cart-img img{width:100%;height:100%;object-fit:contain;padding:4px}
.cart-info{flex:1}
.cart-name{font-size:13px;font-weight:700}
.cart-price{font-size:13px;color:var(--lgg);font-weight:700;margin-top:2px}
.qty-row{display:flex;align-items:center;gap:10px;margin-top:6px}
.qty-btn{background:var(--border);border:none;width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;font-weight:700}
.cart-del{background:none;border:none;color:var(--red);font-size:20px;cursor:pointer;padding:4px}
.cart-summary{background:#fff;margin:0 16px 10px;border-radius:14px;padding:16px;box-shadow:0 1px 6px rgba(0,0,0,.07)}
.sum-row{display:flex;justify-content:space-between;padding:5px 0;font-size:13px}
.sum-row.total{font-weight:700;font-size:16px;color:var(--green);border-top:1px solid var(--border);margin-top:8px;padding-top:12px}
.checkout-btn{width:100%;background:var(--green);color:#fff;border:none;border-radius:12px;padding:14px;font-size:15px;font-weight:700;margin-top:12px;cursor:pointer;font-family:'Cairo',sans-serif}
.empty-state{text-align:center;padding:60px 20px;color:var(--gray)}
.empty-icon{font-size:64px;margin-bottom:12px}
/* ── Modal ── */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:300;justify-content:flex-end;flex-direction:column}
.overlay.open{display:flex}
.modal{background:#fff;border-radius:20px 20px 0 0;padding:24px;max-height:85vh;overflow-y:auto}
.modal-title{font-size:17px;font-weight:700;margin-bottom:18px;text-align:center}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:12px;color:var(--gray);margin-bottom:5px;font-weight:600}
.form-group input,.form-group textarea{width:100%;border:1.5px solid var(--border);border-radius:10px;padding:10px 13px;font-size:14px;font-family:'Cairo',sans-serif;outline:none;transition:.2s}
.form-group input:focus{border-color:var(--lgg)}
.order-summary-box{background:#f9f9f9;border-radius:10px;padding:12px;margin-bottom:14px;font-size:12px;color:#555;line-height:1.8}
.submit-btn{width:100%;background:var(--green);color:#fff;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:700;cursor:pointer;font-family:'Cairo',sans-serif}
.cancel-btn{width:100%;background:none;border:none;padding:10px;color:var(--gray);cursor:pointer;font-family:'Cairo',sans-serif;margin-top:4px}
/* ── Toast ── */
.toast{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:var(--green);color:#fff;padding:10px 24px;border-radius:24px;font-size:13px;font-weight:700;opacity:0;transition:.3s;z-index:400;pointer-events:none;white-space:nowrap}
.toast.show{opacity:1}
/* ── Spinner ── */
.spinner{width:36px;height:36px;border:3px solid #e0e0e0;border-top-color:var(--lgg);border-radius:50%;animation:spin .7s linear infinite;margin:40px auto}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-top">
    <a href="#" class="logo" onclick="showPage('home')">
      <div class="logo-icon">
        {% if logo_type == 'image' and logo_image %}
          <img src="{{ logo_image }}" alt="logo">
        {% else %}
          {{ logo_emoji or '🌿' }}
        {% endif %}
      </div>
      <div>
        <div class="logo-text">{{ site_name }}</div>
        <div class="logo-sub">للمبيدات والأسمدة والأدوية الزراعية</div>
      </div>
    </a>
    <!-- شريط بحث الديسكتوب -->
    <div class="search-bar">
      <input type="text" id="search-input-desk" placeholder="ابحث عن منتج..." oninput="searchProducts(this.value)">
      <button onclick="searchProducts(document.getElementById('search-input-desk').value)">🔍</button>
    </div>
    <div class="header-actions">
      <!-- زر بحث الموبايل -->
      <button class="hbtn search-icon-btn" onclick="toggleMobileSearch()" style="display:none">🔍</button>
      <button class="hbtn" onclick="showPage('cart')">
        🛒 <span id="cart-count">0</span>
        <div class="badge" id="cart-badge" style="display:none"></div>
      </button>
      <button class="hbtn" onclick="showPage('profile')">👤</button>
    </div>
  </div>
  <!-- شريط بحث الموبايل (يظهر عند الضغط على 🔍) -->
  <div class="mobile-search-bar" id="mobile-search-bar">
    <input type="text" id="search-input-mob" placeholder="ابحث عن منتج..." oninput="searchProducts(this.value)" autofocus>
  </div>
  <nav class="nav" id="main-nav">
    <a href="#" class="active" onclick="filterCat(0,this)">الرئيسية</a>
  </nav>
</div>

<!-- Pages -->
<div class="page active" id="page-home">
  <!-- Banner -->
  <div class="banner">
    <div class="banner-content">
      <h1>كل ما يحتاجه المزارع لمحصول أفضل</h1>
      <p>مبيدات · أسمدة · أدوية زراعية بجودة عالية وأسعار منافسة</p>
      <div class="banner-tags">
        <span class="banner-tag">✅ منتجات أصلية</span>
        <span class="banner-tag">🚚 توصيل سريع</span>
        <span class="banner-tag">💬 دعم فني</span>
      </div>
      <button class="banner-btn" onclick="filterCat(0)">تسوق الآن</button>
    </div>
    {% if banner_image %}
    <img class="banner-bg-img" src="{{ banner_image }}" alt="banner">
    {% else %}
    <div class="banner-emoji-side">🌾</div>
    {% endif %}
  </div>

  <!-- Categories -->
  <div class="section">
    <div class="sec-header">
      <div class="sec-title">التصنيفات</div>
    </div>
    <div class="cats-scroll" id="cats-list"><div class="spinner"></div></div>
  </div>

  <!-- Features -->
  <div class="features">
    <div class="feat-item"><div class="feat-icon">🔍</div><div><div class="feat-title">بحث متقدم</div><div class="feat-sub">بحث برقم التسجيل أو اسم المنتج</div></div></div>
    <div class="feat-item"><div class="feat-icon">📋</div><div><div class="feat-title">تفاصيل شاملة</div><div class="feat-sub">جرعات واستخدامات وتحذيرات</div></div></div>
    <div class="feat-item"><div class="feat-icon">✅</div><div><div class="feat-title">منتجات أصلية</div><div class="feat-sub">جميع المنتجات من شركات موثقة</div></div></div>
    <div class="feat-item"><div class="feat-icon">💬</div><div><div class="feat-title">دعم فني</div><div class="feat-sub">استشارة زراعية قبل وبعد الشراء</div></div></div>
  </div>

  <!-- Products -->
  <div class="section">
    <div class="sec-header">
      <div class="sec-title" id="products-title">منتجات مميزة</div>
      <a href="#" class="view-all" onclick="filterCat(0)">عرض الكل</a>
    </div>
    <div class="products-grid" id="products-grid"><div class="spinner"></div></div>
  </div>
</div>

<!-- Cart Page -->
<div class="page" id="page-cart">
  <div style="padding:16px 16px 8px;font-size:16px;font-weight:700">🛒 سلة المشتريات</div>
  <div id="cart-list"></div>
  <div id="cart-total-box"></div>
</div>

<!-- Orders Page -->
<div class="page" id="page-orders">
  <div style="padding:16px 16px 8px;font-size:16px;font-weight:700">📦 طلباتي</div>
  <div class="empty-state"><div class="empty-icon">📦</div><div>طلباتك ستظهر هنا بعد الشراء</div></div>
</div>

<!-- Profile Page -->
<div class="page" id="page-profile">
  <div style="background:linear-gradient(135deg,var(--green),#388e3c);color:#fff;padding:30px 20px;text-align:center;margin-bottom:16px">
    <div style="font-size:50px;margin-bottom:8px">👤</div>
    <div style="font-size:18px;font-weight:700">مرحباً بك!</div>
    <div style="font-size:12px;opacity:.8;margin-top:4px">متجر الأدوية الزراعية</div>
  </div>
  <div style="padding:0 16px">
    <div style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07)">
      <div style="padding:14px 16px;border-bottom:1px solid var(--border);display:flex;gap:12px;align-items:center;cursor:pointer" onclick="showPage('orders')"><span style="font-size:20px">📦</span><span style="font-size:14px">طلباتي</span><span style="margin-right:auto">←</span></div>
      <div style="padding:14px 16px;border-bottom:1px solid var(--border);display:flex;gap:12px;align-items:center;cursor:pointer"><span style="font-size:20px">💬</span><span style="font-size:14px">استشارة زراعية</span><span style="margin-right:auto">←</span></div>
      <div style="padding:14px 16px;border-bottom:1px solid var(--border);display:flex;gap:12px;align-items:center;cursor:pointer"><span style="font-size:20px">⭐</span><span style="font-size:14px">المفضلة</span><span style="margin-right:auto">←</span></div>
      <div style="padding:14px 16px;display:flex;gap:12px;align-items:center;cursor:pointer"><span style="font-size:20px">📞</span><span style="font-size:14px">تواصل معنا</span><span style="margin-right:auto">←</span></div>
    </div>
  </div>
</div>

<!-- Order Modal -->
<div class="overlay" id="order-overlay">
  <div class="modal">
    <div class="modal-title">✅ إتمام الطلب</div>
    <div class="form-group"><label>الاسم الكريم</label><input id="f-name" type="text" placeholder="اسمك"></div>
    <div class="form-group"><label>رقم الهاتف</label><input id="f-phone" type="tel" placeholder="01xxxxxxxxx"></div>
    <div class="form-group"><label>عنوان التوصيل</label><textarea id="f-address" rows="2" style="resize:none;width:100%;border:1.5px solid var(--border);border-radius:10px;padding:10px;font-family:Cairo,sans-serif;font-size:14px;outline:none" placeholder="المحافظة - المدينة - التفاصيل"></textarea></div>
    <div class="order-summary-box" id="order-summary"></div>
    <button class="submit-btn" onclick="submitOrder()">تأكيد الطلب</button>
    <button class="cancel-btn" onclick="closeModal()">إلغاء</button>
  </div>
</div>

<!-- Bottom Nav -->
<div class="bottom-nav">
  <button class="bnav-btn active" onclick="showPage('home')"><span>🏠</span>الرئيسية</button>
  <button class="bnav-btn" onclick="showPage('cart')"><span>🛒</span>السلة</button>
  <button class="bnav-btn" onclick="showPage('orders')"><span>📦</span>طلباتي</button>
  <button class="bnav-btn" onclick="showPage('profile')"><span>👤</span>حسابي</button>
</div>

<div class="toast" id="toast"></div>

<script>
const EMOJIS={1:'🦟',2:'🌱',3:'💊',4:'🏷️',null:'🌿'};
let cart=JSON.parse(localStorage.getItem('cart')||'[]');
let allProducts=[];

function showPage(n){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.bnav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+n).classList.add('active');
  const idx={home:0,cart:1,orders:2,profile:3}[n];
  document.querySelectorAll('.bnav-btn')[idx]?.classList.add('active');
  if(n==='cart') renderCart();
}

function toast(msg){
  const t=document.getElementById('toast');
  t.textContent=msg;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2200);
}

function updateCartCount(){
  const n=cart.reduce((s,i)=>s+i.qty,0);
  document.getElementById('cart-count').textContent=n;
  const b=document.getElementById('cart-badge');
  if(n>0){b.style.display='flex';b.textContent=n;}else{b.style.display='none';}
}

async function loadCategories(){
  const res=await fetch('/api/categories');
  const cats=await res.json();
  const nav=document.getElementById('main-nav');
  const list=document.getElementById('cats-list');
  nav.innerHTML='<a href="#" class="active" onclick="filterCat(0,this);return false">الرئيسية</a>';
  cats.forEach(c=>{
    nav.innerHTML+=`<a href="#" onclick="filterCat(${c.id},this);return false">${c.icon} ${c.name}</a>`;
  });
  list.innerHTML=`<div class="cat-card active" onclick="filterCat(0,this)"><div class="cat-icon">🌿</div><div class="cat-name">الكل</div></div>`;
  cats.forEach(c=>{
    list.innerHTML+=`<div class="cat-card" onclick="filterCat(${c.id},this)"><div class="cat-icon">${c.icon}</div><div class="cat-name">${c.name}</div></div>`;
  });
}

async function loadProducts(){
  const res=await fetch('/api/products/featured');
  allProducts=await res.json();
  renderProducts(allProducts,'منتجات مميزة');
}

async function filterCat(id,el){
  document.querySelectorAll('.cat-card').forEach(c=>c.classList.remove('active'));
  document.querySelectorAll('.nav a').forEach(a=>a.classList.remove('active'));
  if(el){el.classList.add('active');}
  document.getElementById('products-grid').innerHTML='<div class="spinner"></div>';
  const url=id?`/api/products?category=${id}`:'/api/products';
  const res=await fetch(url);
  const prods=await res.json();
  allProducts=prods;
  const catName=id?(document.querySelector(`.cat-card.active .cat-name`)?.textContent||'المنتجات'):'جميع المنتجات';
  renderProducts(prods,catName);
}

function toggleMobileSearch(){
  const bar=document.getElementById('mobile-search-bar');
  bar.classList.toggle('open');
  if(bar.classList.contains('open')){
    document.getElementById('search-input-mob').focus();
  } else {
    document.getElementById('search-input-mob').value='';
    loadProducts();
  }
}

async function searchProducts(q){
  if(!q){loadProducts();return;}
  const res=await fetch(`/api/products?search=${encodeURIComponent(q)}`);
  const prods=await res.json();
  renderProducts(prods,`نتائج البحث: "${q}"`);
}

function renderProducts(products,title){
  document.getElementById('products-title').textContent=title||'المنتجات';
  const g=document.getElementById('products-grid');
  if(!products.length){g.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:40px;color:#888">لا توجد منتجات</div>';return;}
  g.innerHTML=products.map(p=>`
    <div class="prod-card">
      ${p.old_price?`<div class="prod-badge">خصم</div>`:''}
      <div class="prod-img">
        ${p.image_url ? `<img src="${p.image_url}" alt="${p.name}">` : (EMOJIS[p.category_id]||'🌿')}
      </div>
      <div class="prod-info">
        <div class="prod-name">${p.name}</div>
        <div class="prod-desc">${p.description||''}</div>
        <div class="prod-unit">${p.unit}</div>
        <div class="prod-footer">
          <div class="prod-prices">
            <div class="prod-price">${p.price} ج.م</div>
            ${p.old_price?`<div class="prod-old">${p.old_price} ج.م</div>`:''}
          </div>
          <button class="add-cart-btn" onclick="addToCart(${p.id},'${p.name.replace(/'/g,"\\'")}',${p.price},'${p.unit}',${p.category_id},'${p.image_url||''}')">+</button>
        </div>
      </div>
    </div>`).join('');
}

function addToCart(id,name,price,unit,catId,imageUrl){
  const ex=cart.find(i=>i.id==id);
  if(ex){ex.qty++;}else{cart.push({id,name,price,unit,catId,imageUrl,qty:1});}
  localStorage.setItem('cart',JSON.stringify(cart));
  updateCartCount();
  toast('✅ تم إضافة '+name+' للسلة');
}

function renderCart(){
  const el=document.getElementById('cart-list');
  const tot=document.getElementById('cart-total-box');
  if(!cart.length){
    el.innerHTML='<div class="empty-state"><div class="empty-icon">🛒</div><div>السلة فارغة</div></div>';
    tot.innerHTML='';return;
  }
  el.innerHTML=cart.map(i=>`
    <div class="cart-item">
      <div class="cart-img">
        ${i.imageUrl ? `<img src="${i.imageUrl}" alt="${i.name}">` : (EMOJIS[i.catId]||'🌿')}
      </div>
      <div class="cart-info">
        <div class="cart-name">${i.name}</div>
        <div class="cart-price">${i.price} ج.م / ${i.unit}</div>
        <div class="qty-row">
          <button class="qty-btn" onclick="changeQty(${i.id},-1)">−</button>
          <span style="font-weight:700">${i.qty}</span>
          <button class="qty-btn" onclick="changeQty(${i.id},1)">+</button>
        </div>
      </div>
      <button class="cart-del" onclick="removeItem(${i.id})">🗑</button>
    </div>`).join('');
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  tot.innerHTML=`
    <div class="cart-summary">
      <div class="sum-row"><span>المنتجات</span><span>${sub.toFixed(2)} ج.م</span></div>
      <div class="sum-row"><span>الشحن</span><span>20 ج.م</span></div>
      <div class="sum-row total"><span>الإجمالي</span><span>${(sub+20).toFixed(2)} ج.م</span></div>
      <button class="checkout-btn" onclick="openModal()">إتمام الطلب ←</button>
    </div>`;
}

function changeQty(id,d){
  const i=cart.find(x=>x.id==id);
  if(!i)return;
  i.qty+=d;
  if(i.qty<=0)cart=cart.filter(x=>x.id!=id);
  localStorage.setItem('cart',JSON.stringify(cart));
  updateCartCount();renderCart();
}

function removeItem(id){
  cart=cart.filter(x=>x.id!=id);
  localStorage.setItem('cart',JSON.stringify(cart));
  updateCartCount();renderCart();
}

function openModal(){
  if(!cart.length){toast('السلة فارغة!');return;}
  const sub=cart.reduce((s,i)=>s+i.price*i.qty,0);
  document.getElementById('order-summary').innerHTML=
    cart.map(i=>`${i.name} × ${i.qty} = ${(i.price*i.qty).toFixed(2)} ج.م`).join('<br>')+
    `<hr style="margin:8px 0"><strong>الإجمالي: ${(sub+20).toFixed(2)} ج.م</strong>`;
  document.getElementById('order-overlay').classList.add('open');
}

function closeModal(){document.getElementById('order-overlay').classList.remove('open');}

async function submitOrder(){
  const name=document.getElementById('f-name').value.trim();
  const phone=document.getElementById('f-phone').value.trim();
  const address=document.getElementById('f-address').value.trim();
  if(!name||!phone||!address){toast('من فضلك أكمل بياناتك');return;}
  const total=cart.reduce((s,i)=>s+i.price*i.qty,0)+20;
  const btn=document.querySelector('.submit-btn');
  btn.disabled=true;btn.textContent='...جاري الإرسال';
  try{
    const res=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,phone,address,total,items:cart})});
    const data=await res.json();
    if(data.success){
      cart=[];localStorage.setItem('cart',JSON.stringify(cart));
      updateCartCount();closeModal();
      toast('🎉 تم إرسال طلبك! رقم الطلب: #'+data.order_id);
    }
  }catch(e){toast('خطأ في الاتصال');}
  btn.disabled=false;btn.textContent='تأكيد الطلب';
}

updateCartCount();
loadCategories();
loadProducts();
</script>
</body>
</html>"""


TMPL_LOGIN = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>تسجيل الدخول - لوحة التحكم</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Cairo',sans-serif;background:linear-gradient(135deg,#1a5c2a,#2e7d32,#388e3c);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.box{background:#fff;border-radius:20px;padding:36px 28px;width:100%;max-width:380px;box-shadow:0 16px 48px rgba(0,0,0,.25);text-align:center}
.logo{font-size:52px;margin-bottom:8px}
h2{font-size:20px;font-weight:900;color:#1a1a1a;margin-bottom:4px}
.sub{font-size:13px;color:#888;margin-bottom:28px}
.fg{margin-bottom:16px;text-align:right}
label{display:block;font-size:12px;color:#555;margin-bottom:5px;font-weight:600}
input{width:100%;border:1.5px solid #e0e0e0;border-radius:10px;padding:11px 14px;font-size:14px;font-family:'Cairo',sans-serif;outline:none;transition:.2s}
input:focus{border-color:#4caf50}
.btn{width:100%;background:#1a5c2a;color:#fff;border:none;border-radius:12px;padding:13px;font-size:15px;font-weight:700;cursor:pointer;font-family:'Cairo',sans-serif;margin-top:6px}
.error{background:#ffebee;color:#c62828;border-radius:8px;padding:10px;font-size:13px;margin-bottom:16px}
</style>
</head>
<body>
<div class="box">
  <div class="logo">🌿</div>
  <h2>لوحة تحكم الزراعة</h2>
  <p class="sub">سجّل دخولك للمتابعة</p>
  {% if error %}<div class="error">{{ error }}</div>{% endif %}
  <form method="POST">
    <div class="fg"><label>اسم المستخدم</label><input name="username" placeholder="admin" required></div>
    <div class="fg"><label>كلمة المرور</label><input type="password" name="password" placeholder="••••••••" required></div>
    <button type="submit" class="btn">دخول ←</button>
  </form>
</div>
</body>
</html>"""

ADMIN_BASE_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--green:#1a5c2a;--lg:#2e7d32;--lgg:#4caf50;--bg:#f0f4f0;--sw:230px}
body{font-family:'Cairo',sans-serif;background:var(--bg);display:flex;min-height:100vh;font-size:14px}
.sidebar{width:var(--sw);background:var(--green);color:#fff;position:fixed;height:100vh;overflow-y:auto;z-index:50;display:flex;flex-direction:column}
.sb-logo{padding:20px 18px;font-size:16px;font-weight:900;border-bottom:1px solid rgba(255,255,255,.15);display:flex;align-items:center;gap:10px}
.sb-logo span{font-size:24px}
.sb-section{padding:10px 14px 4px;font-size:10px;text-transform:uppercase;color:rgba(255,255,255,.4);letter-spacing:.05em;margin-top:8px}
.sidebar a{display:flex;align-items:center;gap:10px;padding:11px 18px;color:rgba(255,255,255,.8);text-decoration:none;font-size:13px;transition:.15s;border-right:3px solid transparent}
.sidebar a:hover,.sidebar a.act{background:rgba(255,255,255,.12);color:#fff;border-right-color:var(--lgg)}
.sidebar a .ic{font-size:17px;width:20px;text-align:center}
.main{margin-right:var(--sw);flex:1;padding:24px;min-width:0}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px}
.topbar h2{font-size:19px;font-weight:700;color:#1a1a1a}
.stat-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:22px}
.stat{background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 6px rgba(0,0,0,.07);border-bottom:3px solid var(--lgg)}
.stat-ic{font-size:26px;margin-bottom:6px}
.stat-val{font-size:22px;font-weight:900;color:var(--green)}
.stat-lbl{font-size:11px;color:#888;margin-top:2px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.07)}
th{background:var(--green);color:#fff;padding:11px 14px;font-size:12px;text-align:right;font-weight:600}
td{padding:11px 14px;font-size:13px;border-bottom:1px solid #f0f0f0;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#f9fdf9}
.badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;display:inline-block}
.badge-جديد{background:#e3f2fd;color:#1565c0}
.badge-قيد\ التنفيذ{background:#fff3e0;color:#e65100}
.badge-تم\ التوصيل{background:#e8f5e9;color:#2e7d32}
.badge-ملغي{background:#ffebee;color:#c62828}
.btn{padding:7px 16px;border-radius:8px;border:none;cursor:pointer;font-size:12px;font-weight:600;text-decoration:none;display:inline-block;font-family:'Cairo',sans-serif}
.btn-green{background:var(--green);color:#fff}
.btn-red{background:#f44336;color:#fff}
.btn-orange{background:#ff9800;color:#fff}
.btn-blue{background:#1565c0;color:#fff}
.card{background:#fff;border-radius:14px;padding:20px;box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:18px}
.card-title{font-size:15px;font-weight:700;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fg{margin-bottom:12px}
.fg label{display:block;font-size:12px;color:#555;margin-bottom:4px;font-weight:600}
.fg input,.fg select,.fg textarea{width:100%;border:1.5px solid #e0e0e0;border-radius:8px;padding:8px 12px;font-size:13px;font-family:'Cairo',sans-serif;outline:none;transition:.2s}
.fg input:focus,.fg select:focus{border-color:var(--lgg)}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;justify-content:center;align-items:center}
.overlay.open{display:flex}
.modal{background:#fff;border-radius:16px;padding:24px;width:520px;max-height:88vh;overflow-y:auto;box-shadow:0 8px 32px rgba(0,0,0,.15)}
.modal-title{font-size:16px;font-weight:700;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #eee}
/* Image Upload */
.upload-zone{border:2px dashed #e0e0e0;border-radius:12px;padding:20px;text-align:center;cursor:pointer;transition:.2s;position:relative;overflow:hidden;background:#fafafa}
.upload-zone:hover{border-color:var(--lgg);background:#f1f8e9}
.upload-zone.has-img{border-style:solid;border-color:var(--lgg);padding:0}
.upload-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer}
.upload-zone img{width:100%;max-height:180px;object-fit:contain;padding:10px;display:none;border-radius:12px}
.upload-zone.has-img img{display:block}
.upload-placeholder{pointer-events:none}
.upload-zone.has-img .upload-placeholder{display:none}
.remove-img-btn{position:absolute;top:8px;left:8px;background:rgba(244,67,54,.9);color:#fff;border:none;border-radius:6px;padding:3px 10px;font-size:12px;cursor:pointer;z-index:2;display:none;font-family:'Cairo',sans-serif}
.upload-zone.has-img .remove-img-btn{display:block}
.prod-thumb{width:46px;height:46px;border-radius:8px;object-fit:contain;border:1px solid #eee;background:#f9f9f9;padding:3px}
</style>
"""

TMPL_ADMIN_INDEX = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة التحكم - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin" class="act"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout" style="margin-top:auto"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>📊 لوحة التحكم</h2><span style="color:#888;font-size:13px">مرحباً، {{ session.admin }} 👋</span></div>
  <div class="stat-grid">
    <div class="stat"><div class="stat-ic">📦</div><div class="stat-val">{{ stats.products }}</div><div class="stat-lbl">المنتجات</div></div>
    <div class="stat"><div class="stat-ic">🛒</div><div class="stat-val">{{ stats.orders }}</div><div class="stat-lbl">الطلبات</div></div>
    <div class="stat"><div class="stat-ic">🔔</div><div class="stat-val">{{ stats.new_orders }}</div><div class="stat-lbl">طلبات جديدة</div></div>
    <div class="stat"><div class="stat-ic">👥</div><div class="stat-val">{{ stats.customers }}</div><div class="stat-lbl">العملاء</div></div>
    <div class="stat"><div class="stat-ic">💰</div><div class="stat-val">{{ "%.0f"|format(stats.revenue) }}</div><div class="stat-lbl">الإيرادات ج.م</div></div>
  </div>
  <div class="card">
    <div class="card-title">آخر الطلبات <a href="/admin/orders" class="btn btn-green">عرض الكل</a></div>
    <table><thead><tr><th>#</th><th>العميل</th><th>الهاتف</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>إجراء</th></tr></thead>
    <tbody>
    {% for o in orders %}
    <tr><td><b>#{{ o.id }}</b></td><td>{{ o.customer_name }}</td><td>{{ o.customer_phone }}</td>
    <td><b>{{ "%.2f"|format(o.total) }} ج.م</b></td>
    <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
    <td style="color:#888;font-size:12px">{{ o.created_at[:16] }}</td>
    <td><a href="/admin/orders/{{ o.id }}" class="btn btn-green">عرض</a></td></tr>
    {% else %}<tr><td colspan="7" style="text-align:center;padding:30px;color:#888">لا توجد طلبات بعد</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>
</body></html>"""

TMPL_ADMIN_SETTINGS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>إعدادات الموقع - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings" class="act"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>⚙️ إعدادات الموقع</h2><a href="/" target="_blank" class="btn btn-green">معاينة المتجر ←</a></div>

  <form method="POST" action="/admin/settings/save" enctype="multipart/form-data">

    <!-- اسم الموقع -->
    <div class="card">
      <div class="card-title">🏪 اسم الموقع</div>
      <div class="fg">
        <label>اسم المتجر (يظهر في الهيدر والتاب)</label>
        <input name="site_name" value="{{ settings.site_name }}" placeholder="الزراعة">
      </div>
    </div>

    <!-- اللوجو -->
    <div class="card">
      <div class="card-title">🖼️ أيقونة / لوجو الموقع</div>
      <p style="font-size:12px;color:#888;margin-bottom:14px">اختار إما إيموجي أو صورة تظهر في ركن الهيدر</p>

      <div class="fg">
        <label>نوع الأيقونة</label>
        <select name="logo_type" id="logo-type-sel" onchange="toggleLogoType(this.value)">
          <option value="emoji" {% if settings.logo_type == 'emoji' %}selected{% endif %}>إيموجي (emoji)</option>
          <option value="image" {% if settings.logo_type == 'image' %}selected{% endif %}>صورة مرفوعة</option>
        </select>
      </div>

      <!-- Emoji option -->
      <div id="logo-emoji-box" style="{% if settings.logo_type == 'image' %}display:none{% endif %}">
        <div class="fg">
          <label>الإيموجي</label>
          <input name="logo_emoji" value="{{ settings.logo_emoji or '🌿' }}" maxlength="5" style="font-size:28px;text-align:center;width:80px">
        </div>
        <div style="font-size:13px;color:#888">مثال: 🌿 🌱 🌾 🌻 🍃 🌲</div>
      </div>

      <!-- Image option -->
      <div id="logo-image-box" style="{% if settings.logo_type == 'emoji' %}display:none{% endif %}">
        {% if settings.logo_image %}
        <div style="margin-bottom:14px;padding:14px;background:#f1f8e9;border-radius:10px;display:flex;align-items:center;gap:14px">
          <img src="{{ settings.logo_image }}" style="width:60px;height:60px;object-fit:contain;border-radius:8px;border:1px solid #e0e0e0;background:#fff;padding:4px">
          <div>
            <div style="font-size:13px;font-weight:700;color:#1a5c2a">✅ اللوجو الحالي</div>
            <label style="display:flex;align-items:center;gap:6px;margin-top:6px;cursor:pointer;font-size:12px;color:#f44336">
              <input type="checkbox" name="remove_logo_image" style="width:auto"> حذف اللوجو والرجوع للإيموجي
            </label>
          </div>
        </div>
        {% endif %}
        <div class="fg">
          <label>رفع صورة لوجو جديدة</label>
          <div class="upload-zone" id="logo-zone">
            <input type="file" name="logo_image" accept="image/*" onchange="previewUpload(this,'logo-zone','logo-prev')">
            <div class="upload-placeholder">
              <div style="font-size:32px;margin-bottom:8px">🖼️</div>
              <div style="font-size:13px;color:#888;font-weight:600">انقر لرفع الصورة</div>
              <div style="font-size:11px;color:#bbb;margin-top:4px">PNG, JPG, SVG — يفضل خلفية شفافة</div>
            </div>
            <img id="logo-prev" alt="معاينة">
            <button type="button" class="remove-img-btn" onclick="removePreview('logo-zone','logo-prev')">✕ إزالة</button>
          </div>
        </div>
      </div>
    </div>

    <!-- صورة البانر -->
    <div class="card">
      <div class="card-title">🎨 صورة البانر الرئيسي</div>
      <p style="font-size:12px;color:#888;margin-bottom:14px">الصورة تظهر على يمين نص "كل ما يحتاجه المزارع لمحصول أفضل" — يفضل صورة بخلفية شفافة (PNG)</p>

      {% if settings.banner_image %}
      <div style="margin-bottom:14px;padding:14px;background:#f1f8e9;border-radius:10px;display:flex;align-items:center;gap:14px">
        <img src="{{ settings.banner_image }}" style="width:100px;height:80px;object-fit:contain;border-radius:8px;border:1px solid #e0e0e0;background:linear-gradient(135deg,#1a5c2a,#388e3c);padding:6px">
        <div>
          <div style="font-size:13px;font-weight:700;color:#1a5c2a">✅ صورة البانر الحالية</div>
          <label style="display:flex;align-items:center;gap:6px;margin-top:6px;cursor:pointer;font-size:12px;color:#f44336">
            <input type="checkbox" name="remove_banner" style="width:auto"> حذف صورة البانر
          </label>
        </div>
      </div>
      {% endif %}

      <div class="fg">
        <label>رفع صورة بانر جديدة</label>
        <div class="upload-zone" id="banner-zone">
          <input type="file" name="banner_image" accept="image/*" onchange="previewUpload(this,'banner-zone','banner-prev')">
          <div class="upload-placeholder">
            <div style="font-size:32px;margin-bottom:8px">🌾</div>
            <div style="font-size:13px;color:#888;font-weight:600">انقر لرفع صورة البانر</div>
            <div style="font-size:11px;color:#bbb;margin-top:4px">يفضل PNG بخلفية شفافة — مثل جرة مبيد، نبتة، جرار، إلخ</div>
          </div>
          <img id="banner-prev" alt="معاينة">
          <button type="button" class="remove-img-btn" onclick="removePreview('banner-zone','banner-prev')">✕ إزالة</button>
        </div>
      </div>
    </div>

    <button type="submit" class="btn btn-green" style="padding:13px 40px;font-size:15px">💾 حفظ الإعدادات</button>
  </form>
</div>

<script>
function toggleLogoType(v){
  document.getElementById('logo-emoji-box').style.display = v==='emoji' ? '' : 'none';
  document.getElementById('logo-image-box').style.display = v==='image' ? '' : 'none';
}

function previewUpload(input, zoneId, prevId){
  if(!input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    const zone = document.getElementById(zoneId);
    const prev = document.getElementById(prevId);
    prev.src = e.target.result;
    zone.classList.add('has-img');
  };
  reader.readAsDataURL(input.files[0]);
}

function removePreview(zoneId, prevId){
  const zone = document.getElementById(zoneId);
  const prev = document.getElementById(prevId);
  prev.src = '';
  zone.classList.remove('has-img');
  zone.querySelector('input[type=file]').value = '';
}
</script>
</body></html>"""

TMPL_ADMIN_CATS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>التصنيفات - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories" class="act"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>🗂 التصنيفات</h2><button class="btn btn-green" onclick="document.getElementById('add-m').classList.add('open')">+ إضافة تصنيف</button></div>
  <div class="card">
    <table><thead><tr><th>#</th><th>الأيقونة</th><th>الاسم</th><th>النوع</th><th>عدد المنتجات</th><th>إجراءات</th></tr></thead>
    <tbody>
    {% for c in categories %}
    <tr>
      <td>{{ c.id }}</td>
      <td style="font-size:24px">{{ c.icon }}</td>
      <td><b>{{ c.name }}</b></td>
      <td>{{ c.type }}</td>
      <td>{{ c.count }} منتج</td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-orange" onclick="editCat({{ c.id }},'{{ c.name }}','{{ c.icon }}','{{ c.type }}')">تعديل</button>
        <a href="/admin/categories/delete/{{ c.id }}" class="btn btn-red" onclick="return confirm('حذف التصنيف؟')">حذف</a>
      </td>
    </tr>
    {% else %}<tr><td colspan="6" style="text-align:center;padding:30px;color:#888">لا توجد تصنيفات</td></tr>{% endfor %}
    </tbody></table>
  </div>
</div>
<div class="overlay" id="add-m">
  <div class="modal">
    <div class="modal-title">➕ إضافة تصنيف جديد</div>
    <form method="POST" action="/admin/categories/add">
      <div class="form-row">
        <div class="fg"><label>اسم التصنيف *</label><input name="name" required placeholder="مثال: المبيدات"></div>
        <div class="fg"><label>الأيقونة (emoji)</label><input name="icon" value="🌿" maxlength="5" style="font-size:20px"></div>
      </div>
      <div class="fg"><label>النوع</label>
        <select name="type"><option value="main">رئيسي</option><option value="promo">عروض</option><option value="sub">فرعي</option></select>
      </div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-green" style="flex:1;padding:11px">إضافة</button>
        <button type="button" class="btn" style="flex:1;padding:11px;background:#eee;color:#333" onclick="document.getElementById('add-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>
<div class="overlay" id="edit-m">
  <div class="modal">
    <div class="modal-title">✏️ تعديل التصنيف</div>
    <form method="POST" id="edit-form">
      <div class="form-row">
        <div class="fg"><label>اسم التصنيف</label><input name="name" id="e-name" required></div>
        <div class="fg"><label>الأيقونة</label><input name="icon" id="e-icon" maxlength="5" style="font-size:20px"></div>
      </div>
      <div class="fg"><label>النوع</label>
        <select name="type" id="e-type"><option value="main">رئيسي</option><option value="promo">عروض</option><option value="sub">فرعي</option></select>
      </div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-green" style="flex:1;padding:11px">حفظ</button>
        <button type="button" class="btn" style="flex:1;padding:11px;background:#eee;color:#333" onclick="document.getElementById('edit-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>
<script>
function editCat(id,name,icon,type){
  document.getElementById('edit-form').action='/admin/categories/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-icon').value=icon;
  document.getElementById('e-type').value=type;
  document.getElementById('edit-m').classList.add('open');
}
</script>
</body></html>"""

TMPL_ADMIN_PRODUCTS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>المنتجات - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products" class="act"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>📦 المنتجات</h2><button class="btn btn-green" onclick="document.getElementById('add-m').classList.add('open')">+ إضافة منتج</button></div>
  <div class="card">
  <table><thead><tr><th>#</th><th>الصورة</th><th>الاسم</th><th>التصنيف</th><th>السعر</th><th>السعر القديم</th><th>المخزون</th><th>الوحدة</th><th>مميز</th><th>إجراءات</th></tr></thead>
  <tbody>
  {% for p in products %}
  <tr>
    <td>{{ p.id }}</td>
    <td>
      {% if p.image_url %}
        <img src="{{ p.image_url }}" class="prod-thumb" alt="{{ p.name }}">
      {% else %}
        <div style="width:46px;height:46px;border-radius:8px;background:#e8f5e9;display:flex;align-items:center;justify-content:center;font-size:22px">🌿</div>
      {% endif %}
    </td>
    <td><b>{{ p.name }}</b><br><span style="font-size:11px;color:#888">{{ p.description or '' }}</span></td>
    <td>{{ p.cat_name or '—' }}</td>
    <td>{{ p.price }} ج.م</td>
    <td>{{ p.old_price or '—' }}</td>
    <td style="color:{% if p.stock < 10 %}#f44336{% else %}#2e7d32{% endif %}"><b>{{ p.stock }}</b></td>
    <td>{{ p.unit }}</td>
    <td>{% if p.featured %}⭐{% else %}—{% endif %}</td>
    <td style="display:flex;gap:5px">
      <button class="btn btn-orange" onclick="editProd({{ p.id }},'{{ p.name|replace("'","\\'") }}','{{ (p.description or '')|replace("'","\\'") }}',{{ p.price }},{{ p.old_price or 0 }},{{ p.stock }},{{ p.category_id or 0 }},'{{ p.unit }}',{{ p.featured }},'{{ p.image_url or '' }}')">تعديل</button>
      <a href="/admin/products/delete/{{ p.id }}" class="btn btn-red" onclick="return confirm('حذف المنتج؟')">حذف</a>
    </td>
  </tr>
  {% else %}<tr><td colspan="10" style="text-align:center;padding:30px;color:#888">لا توجد منتجات</td></tr>{% endfor %}
  </tbody></table>
  </div>
</div>

<!-- Add Modal -->
<div class="overlay" id="add-m">
  <div class="modal">
    <div class="modal-title">➕ إضافة منتج جديد</div>
    <form method="POST" action="/admin/products/add" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>اسم المنتج *</label><input name="name" required></div>
        <div class="fg"><label>التصنيف *</label><select name="category_id" required>{% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description" placeholder="وصف مختصر للمنتج"></div>
      <div class="form-row">
        <div class="fg"><label>السعر (ج.م) *</label><input name="price" type="number" step="0.01" required></div>
        <div class="fg"><label>السعر القديم (اختياري)</label><input name="old_price" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون *</label><input name="stock" type="number" value="0" required></div>
        <div class="fg"><label>الوحدة</label><select name="unit"><option>علبة</option><option>كيلو</option><option>لتر</option><option>جرام</option><option>قطعة</option></select></div>
      </div>
      <div class="fg">
        <label>📸 صورة المنتج</label>
        <div class="upload-zone" id="add-img-zone">
          <input type="file" name="image" accept="image/*" onchange="previewUpload(this,'add-img-zone','add-img-prev')">
          <div class="upload-placeholder">
            <div style="font-size:28px;margin-bottom:6px">📸</div>
            <div style="font-size:12px;color:#888">انقر لرفع صورة المنتج</div>
            <div style="font-size:11px;color:#bbb;margin-top:3px">PNG, JPG, WEBP</div>
          </div>
          <img id="add-img-prev" alt="معاينة">
          <button type="button" class="remove-img-btn" onclick="removePreview('add-img-zone','add-img-prev')">✕</button>
        </div>
      </div>
      <div class="fg" style="display:flex;align-items:center;gap:8px"><input type="checkbox" name="featured" id="add-feat" style="width:auto"><label for="add-feat" style="font-size:13px">منتج مميز (يظهر في الصفحة الرئيسية)</label></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-green" style="flex:1;padding:11px">حفظ المنتج</button>
        <button type="button" class="btn" style="flex:1;padding:11px;background:#eee;color:#333" onclick="document.getElementById('add-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<!-- Edit Modal -->
<div class="overlay" id="edit-m">
  <div class="modal">
    <div class="modal-title">✏️ تعديل المنتج</div>
    <form method="POST" id="edit-form" enctype="multipart/form-data">
      <div class="form-row">
        <div class="fg"><label>اسم المنتج</label><input name="name" id="e-name" required></div>
        <div class="fg"><label>التصنيف</label><select name="category_id" id="e-cat">{% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}</select></div>
      </div>
      <div class="fg"><label>الوصف</label><input name="description" id="e-desc"></div>
      <div class="form-row">
        <div class="fg"><label>السعر</label><input name="price" id="e-price" type="number" step="0.01"></div>
        <div class="fg"><label>السعر القديم</label><input name="old_price" id="e-oprice" type="number" step="0.01"></div>
      </div>
      <div class="form-row">
        <div class="fg"><label>المخزون</label><input name="stock" id="e-stock" type="number"></div>
        <div class="fg"><label>الوحدة</label><select name="unit" id="e-unit"><option>علبة</option><option>كيلو</option><option>لتر</option><option>جرام</option><option>قطعة</option></select></div>
      </div>
      <div class="fg">
        <label>📸 صورة المنتج (اتركه فارغ للإبقاء على الصورة الحالية)</label>
        <div id="edit-current-img" style="display:none;margin-bottom:8px">
          <img id="edit-curr-img-el" style="width:60px;height:60px;object-fit:contain;border-radius:8px;border:1px solid #eee;padding:4px;background:#f9f9f9">
          <span style="font-size:11px;color:#888;margin-right:8px">الصورة الحالية</span>
        </div>
        <div class="upload-zone" id="edit-img-zone">
          <input type="file" name="image" accept="image/*" onchange="previewUpload(this,'edit-img-zone','edit-img-prev')">
          <div class="upload-placeholder">
            <div style="font-size:28px;margin-bottom:6px">📸</div>
            <div style="font-size:12px;color:#888">انقر لتغيير الصورة</div>
          </div>
          <img id="edit-img-prev" alt="معاينة">
          <button type="button" class="remove-img-btn" onclick="removePreview('edit-img-zone','edit-img-prev')">✕</button>
        </div>
      </div>
      <div class="fg" style="display:flex;align-items:center;gap:8px"><input type="checkbox" name="featured" id="e-feat" style="width:auto"><label for="e-feat" style="font-size:13px">منتج مميز</label></div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button type="submit" class="btn btn-green" style="flex:1;padding:11px">حفظ</button>
        <button type="button" class="btn" style="flex:1;padding:11px;background:#eee;color:#333" onclick="document.getElementById('edit-m').classList.remove('open')">إلغاء</button>
      </div>
    </form>
  </div>
</div>

<script>
function previewUpload(input, zoneId, prevId){
  if(!input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    const zone = document.getElementById(zoneId);
    const prev = document.getElementById(prevId);
    prev.src = e.target.result;
    zone.classList.add('has-img');
  };
  reader.readAsDataURL(input.files[0]);
}

function removePreview(zoneId, prevId){
  const zone = document.getElementById(zoneId);
  const prev = document.getElementById(prevId);
  prev.src = '';
  zone.classList.remove('has-img');
  zone.querySelector('input[type=file]').value = '';
}

function editProd(id,name,desc,price,oprice,stock,catId,unit,featured,imageUrl){
  document.getElementById('edit-form').action='/admin/products/edit/'+id;
  document.getElementById('e-name').value=name;
  document.getElementById('e-desc').value=desc;
  document.getElementById('e-price').value=price;
  document.getElementById('e-oprice').value=oprice||'';
  document.getElementById('e-stock').value=stock;
  document.getElementById('e-cat').value=catId;
  document.getElementById('e-unit').value=unit;
  document.getElementById('e-feat').checked=featured==1;
  // show current image
  const currBox = document.getElementById('edit-current-img');
  const currImg = document.getElementById('edit-curr-img-el');
  if(imageUrl){ currImg.src=imageUrl; currBox.style.display='flex'; currBox.style.alignItems='center'; }
  else { currBox.style.display='none'; }
  // reset upload zone
  removePreview('edit-img-zone','edit-img-prev');
  document.getElementById('edit-m').classList.add('open');
}
</script>
</body></html>"""

TMPL_ADMIN_ORDERS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>الطلبات - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders" class="act"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>🛒 الطلبات</h2></div>
  <div class="card">
  <table><thead><tr><th>#</th><th>العميل</th><th>الهاتف</th><th>العنوان</th><th>الإجمالي</th><th>الحالة</th><th>التاريخ</th><th>تفاصيل</th></tr></thead>
  <tbody>
  {% for o in orders %}
  <tr>
    <td><b>#{{ o.id }}</b></td><td>{{ o.customer_name }}</td><td>{{ o.customer_phone }}</td>
    <td style="max-width:130px;overflow:hidden;text-overflow:ellipsis">{{ o.customer_address }}</td>
    <td><b>{{ "%.2f"|format(o.total) }} ج.م</b></td>
    <td><span class="badge badge-{{ o.status }}">{{ o.status }}</span></td>
    <td style="color:#888;font-size:12px">{{ o.created_at[:16] }}</td>
    <td><a href="/admin/orders/{{ o.id }}" class="btn btn-green">عرض</a></td>
  </tr>
  {% else %}<tr><td colspan="8" style="text-align:center;padding:30px;color:#888">لا توجد طلبات بعد</td></tr>{% endfor %}
  </tbody></table>
  </div>
</div>
</body></html>"""

TMPL_ADMIN_ORDER_DETAIL = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>تفاصيل الطلب - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders" class="act"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>📋 تفاصيل الطلب #{{ order.id }}</h2><a href="/admin/orders" class="btn" style="background:#eee;color:#333">← رجوع</a></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px">
    <div class="card">
      <div class="card-title">👤 بيانات العميل</div>
      <p><b>الاسم:</b> {{ order.customer_name }}</p>
      <p style="margin-top:8px"><b>الهاتف:</b> {{ order.customer_phone }}</p>
      <p style="margin-top:8px"><b>العنوان:</b> {{ order.customer_address }}</p>
      <p style="margin-top:8px;color:#888;font-size:12px">{{ order.created_at[:16] }}</p>
    </div>
    <div class="card">
      <div class="card-title">📊 الحالة</div>
      <span class="badge badge-{{ order.status }}" style="font-size:14px;padding:6px 16px">{{ order.status }}</span>
      <form method="POST" action="/admin/orders/status/{{ order.id }}" style="margin-top:16px">
        <div class="fg"><label>تغيير الحالة</label>
          <select name="status">
            <option {% if order.status=='جديد' %}selected{% endif %}>جديد</option>
            <option {% if order.status=='قيد التنفيذ' %}selected{% endif %}>قيد التنفيذ</option>
            <option {% if order.status=='تم التوصيل' %}selected{% endif %}>تم التوصيل</option>
            <option {% if order.status=='ملغي' %}selected{% endif %}>ملغي</option>
          </select>
        </div>
        <button type="submit" class="btn btn-green">تحديث</button>
      </form>
    </div>
  </div>
  <div class="card">
    <div class="card-title">🛒 المنتجات المطلوبة</div>
    <table><thead><tr><th>المنتج</th><th>الكمية</th><th>السعر</th><th>الإجمالي</th></tr></thead>
    <tbody>
    {% for item in items %}
    <tr><td>{{ item.name }}</td><td>{{ item.qty }}</td><td>{{ item.price }} ج.م</td><td><b>{{ "%.2f"|format(item.price * item.qty) }} ج.م</b></td></tr>
    {% endfor %}
    <tr style="background:#f9fdf9"><td colspan="3"><b>الإجمالي</b></td><td><b style="color:#1a5c2a;font-size:15px">{{ "%.2f"|format(order.total) }} ج.م</b></td></tr>
    </tbody></table>
  </div>
</div>
</body></html>"""

TMPL_ADMIN_CUSTOMERS = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>العملاء - الزراعة</title>""" + ADMIN_BASE_STYLE + """</head>
<body>
<div class="sidebar">
  <div class="sb-logo"><span>🌿</span>الزراعة - إدارة</div>
  <div class="sb-section">القائمة الرئيسية</div>
  <a href="/admin"><span class="ic">📊</span>الرئيسية</a>
  <a href="/admin/products"><span class="ic">📦</span>المنتجات</a>
  <a href="/admin/categories"><span class="ic">🗂</span>التصنيفات</a>
  <a href="/admin/orders"><span class="ic">🛒</span>الطلبات</a>
  <a href="/admin/customers" class="act"><span class="ic">👥</span>العملاء</a>
  <a href="/admin/settings"><span class="ic">⚙️</span>إعدادات الموقع</a>
  <div class="sb-section">أخرى</div>
  <a href="/" target="_blank"><span class="ic">🌐</span>المتجر</a>
  <a href="/admin/logout"><span class="ic">🚪</span>خروج</a>
</div>
<div class="main">
  <div class="topbar"><h2>👥 العملاء</h2></div>
  <div class="card">
  <table><thead><tr><th>#</th><th>الاسم</th><th>الهاتف</th><th>العنوان</th><th>تاريخ التسجيل</th></tr></thead>
  <tbody>
  {% for c in customers %}
  <tr><td>{{ c.id }}</td><td><b>{{ c.name }}</b></td><td>{{ c.phone }}</td><td>{{ c.address }}</td><td style="color:#888;font-size:12px">{{ c.created_at[:16] }}</td></tr>
  {% else %}<tr><td colspan="5" style="text-align:center;padding:30px;color:#888">لا يوجد عملاء بعد</td></tr>{% endfor %}
  </tbody></table>
  </div>
</div>
</body></html>"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)

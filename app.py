from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3, os, json
from functools import wraps

app = Flask(__name__)
app.secret_key = "zaraati_secret_2024"
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
    return render_template("admin_login.html", error=error)

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
    return render_template("admin_index.html", stats=stats, orders=recent_orders)

@app.route("/admin/products")
@login_required
def admin_products():
    conn = get_db()
    products = conn.execute("SELECT p.*,c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC").fetchall()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("admin_products.html", products=products, categories=categories)

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
    return render_template("admin_orders.html", orders=orders)

@app.route("/admin/orders/<int:oid>")
@login_required
def admin_order_detail(oid):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    items = conn.execute("""SELECT oi.*,p.name FROM order_items oi 
        LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?""", (oid,)).fetchall()
    conn.close()
    return render_template("admin_order_detail.html", order=order, items=items)

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
    return render_template("admin_categories.html", categories=cats)

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
    return render_template("app.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

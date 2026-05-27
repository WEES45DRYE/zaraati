from app import app, get_db, login_required
from flask import request, jsonify

@app.route("/api/admin/stats")
@login_required
def api_admin_stats():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products"); stats_p = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders"); stats_o = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='جديد'"); stats_n = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total),0) FROM orders"); stats_r = cur.fetchone()['coalesce']
    cur.execute("SELECT COUNT(*) FROM customers"); stats_c = cur.fetchone()['count']
    cur.close(); conn.close()
    return jsonify({"products":stats_p,"orders":stats_o,"new_orders":stats_n,"revenue":float(stats_r),"customers":stats_c})

@app.route("/api/admin/orders")
@login_required
def api_admin_orders():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in orders])

@app.route("/api/admin/orders/<int:oid>")
@login_required
def api_admin_order_detail(oid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=%s", (oid,))
    order = cur.fetchone()
    if not order: return jsonify({"error": "مش موجود"}), 404
    cur.execute("SELECT oi.*,p.name as product_name FROM order_items oi LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=%s", (oid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"order": dict(order), "items": [dict(i) for i in items]})

@app.route("/api/admin/orders/<int:oid>/status", methods=["POST"])
@login_required
def api_admin_update_order_status(oid):
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (data["status"], oid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "order_id": oid, "status": data["status"]})

@app.route("/api/admin/customers")
@login_required
def api_admin_customers():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY created_at DESC")
    customers = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([dict(r) for r in customers])

@app.route("/api/admin/products", methods=["POST"])
@login_required
def api_admin_add_product():
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO products (name,description,price,old_price,stock,category_id,unit,featured) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (data["name"],data.get("description",""),float(data["price"]),
         float(data["old_price"]) if data.get("old_price") else None,
         int(data.get("stock",0)),int(data["category_id"]),data.get("unit","علبة"),1 if data.get("featured") else 0))
    new_id = cur.fetchone()['id']
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "product_id": new_id})

@app.route("/api/admin/products/<int:pid>", methods=["PUT"])
@login_required
def api_admin_update_product(pid):
    data = request.json
    conn = get_db(); cur = conn.cursor()
    fields, values = [], []
    for f in ["name","description","price","old_price","stock","category_id","unit","featured"]:
        if f in data:
            fields.append(f"{f}=%s")
            values.append(1 if f=="featured" and data[f] else (float(data[f]) if f in ["price","old_price"] and data[f] else (int(data[f]) if f in ["stock","category_id"] else data[f])))
    values.append(pid)
    cur.execute(f"UPDATE products SET {','.join(fields)} WHERE id=%s", values)
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "product_id": pid})

@app.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@login_required
def api_admin_delete_product_json(pid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (pid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "deleted_id": pid})

@app.route("/api/admin/products/<int:pid>/stock", methods=["PATCH"])
@login_required
def api_admin_update_stock(pid):
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE products SET stock=%s WHERE id=%s", (int(data["stock"]), pid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "product_id": pid, "stock": data["stock"]})

@app.route("/api/admin/categories", methods=["POST"])
@login_required
def api_admin_add_category():
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO categories (name,icon,type) VALUES (%s,%s,%s) RETURNING id",
        (data["name"],data.get("icon","🌿"),data.get("type","main")))
    new_id = cur.fetchone()['id']
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "category_id": new_id})

@app.route("/api/admin/categories/<int:cid>", methods=["PUT"])
@login_required
def api_admin_update_category(cid):
    data = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE categories SET name=%s,icon=%s,type=%s WHERE id=%s",
        (data["name"],data.get("icon","🌿"),data.get("type","main"),cid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "category_id": cid})

@app.route("/api/admin/categories/<int:cid>", methods=["DELETE"])
@login_required
def api_admin_delete_category_json(cid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE products SET category_id=NULL WHERE category_id=%s", (cid,))
    cur.execute("DELETE FROM categories WHERE id=%s", (cid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "deleted_id": cid})

@app.route("/api/admin/settings")
@login_required
def api_admin_settings():
    from app import get_setting
    return jsonify({"site_name":get_setting("site_name","الزراعة"),"logo_type":get_setting("logo_type","emoji"),"logo_emoji":get_setting("logo_emoji","🌿"),"logo_image":get_setting("logo_image",""),"banner_image":get_setting("banner_image","")})

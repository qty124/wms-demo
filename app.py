"""
仓储管理系统 - Flask 主程序
功能：
  1. 仪表盘（统计卡片 + 预警列表 + 近期流水）
  2. 商品增删改查（图书维度）
  3. 入库 / 出库（自动写流水、更新库存）
  4. 流水历史（按时间倒序）
"""
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from sqlalchemy import func

from models import db, Product, Transaction


# ==================== 示例数据 ====================
def seed_sample_data():
    """首次启动时填充图书示例数据 + 几条流水，方便演示"""
    samples = [
        # isbn, 书名, 作者, 出版社, 分类, 库存, 进价, 售价, 预警阈值, 货架
        ("9787111213826", "深入理解计算机系统",     "Randal E. Bryant",   "机械工业出版社", "计算机/网络",   25, 89.0,  139.0, 10, "A-01-03"),
        ("9787111544937", "计算机网络：自顶向下方法", "James F. Kurose",    "机械工业出版社", "计算机/网络",   18, 75.0,  99.0,  10, "A-01-05"),
        ("9787121362220", "TCP/IP 详解 卷1：协议",   "W. Richard Stevens","人民邮电出版社", "计算机/网络",   8,  68.0,  89.0,  10, "A-02-01"),
        ("9787508672069", "Python编程：从入门到实践","Eric Matthes",      "人民邮电出版社", "程序设计",       32, 59.0,  89.0,  10, "B-01-02"),
        ("9787115428028", "黑客与画家",              "Paul Graham",       "人民邮电出版社", "互联网/创业",    5,  42.0,  69.0,  8,   "C-03-04"),
        ("9787508668369", "代码大全",                "Steve McConnell",   "清华大学出版社", "软件工程",       12, 98.0,  148.0, 8,  "B-02-06"),
        ("9787111407010", "算法导论",                "Thomas H. Cormen",  "机械工业出版社", "算法/数据结构",  6,  108.0, 168.0, 5,  "A-03-01"),
        ("9787115296543", "Wireshark 数据包分析实战","Laura Chappell",    "人民邮电出版社", "网络安全",       14, 49.0,  79.0,  8,  "D-01-02"),
        ("9787121295085", "鸟哥的Linux私房菜",       "鸟哥",              "人民邮电出版社", "操作系统",       20, 88.0,  118.0, 10, "B-03-03"),
        ("9787115437495", "SQL必知必会",             "Ben Forta",         "人民邮电出版社", "数据库",         16, 29.0,  49.0,  10, "B-04-01"),
        ("9787508653440", "人月神话",                "Frederick P. Brooks","清华大学出版社", "软件工程",       0,  39.0,  59.0,  5,  "B-02-08"),
        ("9787111544938", "图解HTTP",                "上野 宣",           "人民邮电出版社", "计算机/网络",   22, 49.0,  69.0,  10, "A-01-08"),
    ]
    products = []
    for isbn, title, author, publisher, category, stock, cost, price, threshold, location in samples:
        p = Product(
            isbn=isbn, title=title, author=author, publisher=publisher,
            category=category, stock=stock, cost=cost, price=price,
            low_stock_threshold=threshold, location=location,
        )
        products.append(p)
        db.session.add(p)
    db.session.flush()  # 让 product 拿到 id

    # 生成几条流水，让首页"近期出入库"不那么空
    sample_tx = [
        (products[0], "in",  10, "新书到货",         "采购员-小李"),
        (products[3], "out", 3,  "客户订单 #A2025",   "仓管-王姐"),
        (products[6], "in",  6,  "出版社直供",        "采购员-小李"),
        (products[4], "out", 2,  "线下书店调拨",      "仓管-王姐"),
        (products[7], "in",  5,  "补货",              "采购员-小李"),
        (products[10],"out", 1,  "已售罄示例",        "仓管-王姐"),
        (products[1], "out", 4,  "高校批量采购",      "销售-张总"),
    ]
    # 让时间戳错开一点点，看起来像真实的近期记录
    base_time = datetime.utcnow() - timedelta(hours=6)
    for i, (p, t, q, note, op) in enumerate(sample_tx):
        db.session.add(Transaction(
            product_id=p.id, type=t, quantity=q,
            note=note, operator=op,
            created_at=base_time + timedelta(minutes=37 * i),
        ))

    db.session.commit()
    print(f"[seed] 已写入 {len(products)} 件商品 + {len(sample_tx)} 条流水")


def create_app():
    # 先创建空 Flask，再配置（避免循环依赖）
    app = Flask(__name__)
    # 生产环境从环境变量取 secret_key，本地开发用固定值
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "wms-demo-secret-key")
    # SQLite 数据库路径：放在 instance/ 目录下
    db_dir = os.path.join(app.instance_path)
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "wms.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        # 首次运行自动播种示例数据
        if Product.query.count() == 0:
            seed_sample_data()

    return app


# 关键：先创建 app 实例，再注册路由（@app.route 装饰器需要 app 已存在）
app = create_app()


# ==================== 路由 ====================
@app.route("/")
def dashboard():
    """仪表盘"""
    total_products = Product.query.count()
    total_stock = db.session.query(func.sum(Product.stock)).scalar() or 0
    total_value = db.session.query(func.sum(Product.stock * Product.cost)).scalar() or 0
    low_stock_items = Product.query.filter(
        Product.stock <= Product.low_stock_threshold,
        Product.stock > 0
    ).count()
    out_of_stock = Product.query.filter(Product.stock <= 0).count()

    # 分类分布（给仪表盘一个简单柱状图）
    category_rows = db.session.query(
        Product.category, func.sum(Product.stock)
    ).group_by(Product.category).all()
    categories = [{"name": c or "未分类", "stock": int(s)} for c, s in category_rows]

    # 近期流水
    recent_tx = Transaction.query.order_by(Transaction.created_at.desc()).limit(8).all()

    # 预警列表（库存非零但低于阈值）
    low_list = Product.query.filter(
        Product.stock > 0,
        Product.stock <= Product.low_stock_threshold
    ).order_by(Product.stock.asc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_stock=total_stock,
        total_value=total_value,
        low_stock_items=low_stock_items,
        out_of_stock=out_of_stock,
        categories=categories,
        recent_tx=recent_tx,
        low_list=low_list,
    )


@app.route("/products")
def product_list():
    """商品列表，支持搜索 + 分类筛选"""
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "").strip()

    query = Product.query
    if q:
        query = query.filter(
            db.or_(
                Product.title.contains(q),
                Product.author.contains(q),
                Product.isbn.contains(q),
            )
        )
    if cat:
        query = query.filter(Product.category == cat)

    products = query.order_by(Product.id.asc()).all()
    all_categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]
    return render_template("products.html", products=products, q=q, cat=cat, categories=all_categories)


@app.route("/products/new", methods=["GET", "POST"])
def product_create():
    """新增商品"""
    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        if not isbn:
            flash("ISBN 不能为空", "danger")
            return redirect(url_for("product_create"))
        if Product.query.filter_by(isbn=isbn).first():
            flash(f"ISBN {isbn} 已存在", "danger")
            return redirect(url_for("product_create"))

        p = Product(
            isbn=isbn,
            title=request.form.get("title", "").strip(),
            author=request.form.get("author", "").strip(),
            publisher=request.form.get("publisher", "").strip(),
            category=request.form.get("category", "").strip(),
            stock=int(request.form.get("stock", 0) or 0),
            cost=float(request.form.get("cost", 0) or 0),
            price=float(request.form.get("price", 0) or 0),
            low_stock_threshold=int(request.form.get("low_stock_threshold", 10) or 10),
            location=request.form.get("location", "").strip(),
        )
        db.session.add(p)
        db.session.commit()
        flash(f"已新增商品：{p.title}", "success")
        return redirect(url_for("product_list"))

    return render_template("product_form.html", product=None)


@app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
def product_edit(pid):
    """编辑商品"""
    p = Product.query.get_or_404(pid)
    if request.method == "POST":
        p.title = request.form.get("title", "").strip()
        p.author = request.form.get("author", "").strip()
        p.publisher = request.form.get("publisher", "").strip()
        p.category = request.form.get("category", "").strip()
        p.cost = float(request.form.get("cost", 0) or 0)
        p.price = float(request.form.get("price", 0) or 0)
        p.low_stock_threshold = int(request.form.get("low_stock_threshold", 10) or 10)
        p.location = request.form.get("location", "").strip()
        db.session.commit()
        flash(f"已更新：{p.title}", "success")
        return redirect(url_for("product_list"))

    return render_template("product_form.html", product=p)


@app.route("/products/<int:pid>/delete", methods=["POST"])
def product_delete(pid):
    """删除商品"""
    p = Product.query.get_or_404(pid)
    title = p.title
    db.session.delete(p)
    db.session.commit()
    flash(f"已删除：{title}", "warning")
    return redirect(url_for("product_list"))


@app.route("/stock/in", methods=["GET", "POST"])
def stock_in():
    """入库"""
    if request.method == "POST":
        pid = int(request.form.get("product_id"))
        qty = int(request.form.get("quantity", 0) or 0)
        note = request.form.get("note", "").strip()
        operator = request.form.get("operator", "管理员").strip()

        if qty <= 0:
            flash("入库数量必须 > 0", "danger")
            return redirect(url_for("stock_in"))

        p = Product.query.get_or_404(pid)
        p.stock += qty
        db.session.add(Transaction(
            product_id=p.id, type="in", quantity=qty, note=note, operator=operator
        ))
        db.session.commit()
        flash(f"入库成功：{p.title} +{qty}（现库存 {p.stock}）", "success")
        return redirect(url_for("dashboard"))

    products = Product.query.order_by(Product.title.asc()).all()
    return render_template("stock_in.html", products=products, mode="in")


@app.route("/stock/out", methods=["GET", "POST"])
def stock_out():
    """出库"""
    if request.method == "POST":
        pid = int(request.form.get("product_id"))
        qty = int(request.form.get("quantity", 0) or 0)
        note = request.form.get("note", "").strip()
        operator = request.form.get("operator", "管理员").strip()

        if qty <= 0:
            flash("出库数量必须 > 0", "danger")
            return redirect(url_for("stock_out"))

        p = Product.query.get_or_404(pid)
        if qty > p.stock:
            flash(f"出库失败：{p.title} 当前库存仅 {p.stock}", "danger")
            return redirect(url_for("stock_out"))

        p.stock -= qty
        db.session.add(Transaction(
            product_id=p.id, type="out", quantity=qty, note=note, operator=operator
        ))
        db.session.commit()
        flash(f"出库成功：{p.title} -{qty}（现库存 {p.stock}）", "success")
        return redirect(url_for("dashboard"))

    products = Product.query.order_by(Product.title.asc()).all()
    return render_template("stock_in.html", products=products, mode="out")


@app.route("/transactions")
def transaction_list():
    """流水历史"""
    txs = Transaction.query.order_by(Transaction.created_at.desc()).limit(200).all()
    return render_template("transactions.html", txs=txs)


@app.route("/about")
def about():
    """关于页"""
    return render_template("about.html")


@app.template_filter("money")
def money_filter(v):
    if v is None:
        return "¥0.00"
    return f"¥{v:,.2f}"


@app.template_filter("datetime_cn")
def datetime_cn_filter(dt):
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


# ==================== 模板上下文 ====================
@app.context_processor
def inject_globals():
    return {"now": datetime.utcnow()}


# ==================== 错误处理 ====================
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, msg="页面不存在"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, msg="服务器内部错误"), 500


if __name__ == "__main__":
    # 端口 5000；如果本机有冲突，可改成 5050/8000 等
    app.run(host="127.0.0.1", port=5000, debug=True)
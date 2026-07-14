"""
仓储管理系统 - 数据模型
用 SQLAlchemy ORM 描述两张表：商品表、出入库流水表
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    """商品（图书）表"""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, comment="ISBN 号")
    title = db.Column(db.String(120), nullable=False, comment="书名")
    author = db.Column(db.String(60), nullable=False, comment="作者")
    publisher = db.Column(db.String(60), nullable=True, comment="出版社")
    category = db.Column(db.String(30), nullable=True, comment="分类")
    stock = db.Column(db.Integer, default=0, nullable=False, comment="当前库存")
    cost = db.Column(db.Float, default=0.0, comment="进价")
    price = db.Column(db.Float, default=0.0, comment="售价")
    low_stock_threshold = db.Column(db.Integer, default=10, comment="库存预警阈值")
    location = db.Column(db.String(30), nullable=True, comment="货架位置，如 A-03-12")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联流水
    transactions = db.relationship("Transaction", backref="product", lazy=True, cascade="all, delete-orphan")

    @property
    def stock_value(self):
        """库存价值（按进价计算）"""
        return self.stock * (self.cost or 0)

    @property
    def status(self):
        """库存状态：ok / low / out"""
        if self.stock <= 0:
            return "out"
        if self.stock <= self.low_stock_threshold:
            return "low"
        return "ok"

    @property
    def status_label(self):
        return {"ok": "充足", "low": "偏低", "out": "缺货"}.get(self.status)

    @property
    def status_color(self):
        return {"ok": "success", "low": "warning", "out": "danger"}.get(self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "category": self.category,
            "stock": self.stock,
            "cost": self.cost,
            "price": self.price,
            "low_stock_threshold": self.low_stock_threshold,
            "location": self.location,
            "stock_value": self.stock_value,
            "status": self.status,
            "status_label": self.status_label,
        }


class Transaction(db.Model):
    """出入库流水表"""
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # type: "in" 入库 / "out" 出库
    type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, comment="数量（正整数）")
    note = db.Column(db.String(200), nullable=True, comment="备注")
    operator = db.Column(db.String(30), default="管理员", comment="操作人")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def type_label(self):
        return {"in": "入库", "out": "出库"}.get(self.type, self.type)

    @property
    def type_color(self):
        return {"in": "success", "out": "primary"}.get(self.type, "secondary")

    @property
    def sign(self):
        return "+" if self.type == "in" else "-"

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else "已删除",
            "type": self.type,
            "type_label": self.type_label,
            "quantity": self.quantity,
            "note": self.note,
            "operator": self.operator,
            "created_at": self.created_at,
            "sign": self.sign,
        }
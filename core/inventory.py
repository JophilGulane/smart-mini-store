"""Business rules: atomic stock transactions, integer money, immutable sale prices."""
from decimal import Decimal, InvalidOperation
import sqlite3
import uuid
import pandas as pd
from core.database import connect, now


def money_to_centavos(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError("Enter a nonnegative amount with at most two decimal places.")
        return int(amount * 100)
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid monetary amount.") from None


def units(value, allow_zero=False):
    try:
        numeric = Decimal(str(value))
        if not numeric.is_finite() or numeric != int(numeric) or numeric < (0 if allow_zero else 1):
            raise ValueError
        return int(numeric)
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        raise ValueError("Quantity must be a whole number " + ("of zero or more." if allow_zero else "greater than zero.")) from None


def products(path, active_only=False):
    with connect(path) as db:
        return pd.read_sql_query("SELECT * FROM products" + (" WHERE active=1" if active_only else "") + " ORDER BY name", db)


def add_product(path, name, category, cost, price, opening_stock=0, reorder_level=10):
    name, category = name.strip(), category.strip()
    if not name or not category:
        raise ValueError("Product name and category are required.")
    cost, price = money_to_centavos(cost), money_to_centavos(price)
    opening_stock, reorder_level = units(opening_stock, True), units(reorder_level, True)
    try:
        with connect(path) as db:
            cur = db.execute("INSERT INTO products(name,category,cost_centavos,price_centavos,stock_qty,reorder_level,created_at) VALUES(?,?,?,?,?,?,?)",
                             (name, category, cost, price, opening_stock, reorder_level, now()))
            pid = cur.lastrowid
            db.execute("INSERT INTO stock_movements(product_id,movement_type,quantity_delta,occurred_at,note) VALUES(?,?,?,?,?)",
                       (pid, "opening", opening_stock, now(), "Opening balance"))
            return pid
    except sqlite3.IntegrityError:
        raise ValueError("A product with this name already exists.") from None


def edit_product(path, pid, name, category, cost, price, reorder_level, active):
    if not name.strip() or not category.strip():
        raise ValueError("Product name and category are required.")
    values = (name.strip(), category.strip(), money_to_centavos(cost), money_to_centavos(price), units(reorder_level, True), int(active), int(pid))
    try:
        with connect(path) as db:
            if db.execute("UPDATE products SET name=?,category=?,cost_centavos=?,price_centavos=?,reorder_level=?,active=? WHERE id=?", values).rowcount != 1:
                raise ValueError("Product not found.")
    except sqlite3.IntegrityError:
        raise ValueError("A product with this name already exists.") from None


def receive_stock(path, pid, quantity, request_id=None, note="Stock received"):
    qty, token = units(quantity), request_id or str(uuid.uuid4())
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT id FROM stock_movements WHERE request_id=?", (token,)).fetchone():
            return False
        if db.execute("UPDATE products SET stock_qty=stock_qty+? WHERE id=? AND active=1", (qty, int(pid))).rowcount != 1:
            raise ValueError("Select an active product.")
        db.execute("INSERT INTO stock_movements(product_id,movement_type,quantity_delta,occurred_at,note,request_id) VALUES(?,?,?,?,?,?)",
                   (int(pid), "receipt", qty, now(), note.strip(), token))
    return True


def record_sale(path, pid, quantity, request_id):
    qty = units(quantity)
    if not request_id:
        raise ValueError("A submission token is required.")
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT id FROM sales WHERE request_id=?", (request_id,)).fetchone()
        if previous:
            return previous["id"], False
        row = db.execute("SELECT * FROM products WHERE id=? AND active=1", (int(pid),)).fetchone()
        if not row:
            raise ValueError("Select an active product.")
        if db.execute("UPDATE products SET stock_qty=stock_qty-? WHERE id=? AND stock_qty>=?", (qty, int(pid), qty)).rowcount != 1:
            raise ValueError(f"Insufficient stock. Only {row['stock_qty']} unit(s) available.")
        ts = now()
        sale = db.execute("INSERT INTO sales(request_id,product_id,quantity,unit_price_centavos,unit_cost_centavos,occurred_at) VALUES(?,?,?,?,?,?)",
                          (request_id, int(pid), qty, row["price_centavos"], row["cost_centavos"], ts)).lastrowid
        db.execute("INSERT INTO stock_movements(product_id,movement_type,quantity_delta,sale_id,occurred_at,note) VALUES(?,?,?,?,?,?)",
                   (int(pid), "sale", -qty, sale, ts, "Recorded sale"))
        return sale, True


def sales(path):
    with connect(path) as db:
        return pd.read_sql_query("""SELECT s.id, p.name AS product, s.quantity,
          s.unit_price_centavos/100.0 AS unit_price_php,
          s.quantity*s.unit_price_centavos/100.0 AS revenue_php,
          s.quantity*(s.unit_price_centavos-s.unit_cost_centavos)/100.0 AS gross_margin_php,
          substr(s.occurred_at,1,10) AS date, s.occurred_at
          FROM sales s JOIN products p ON p.id=s.product_id ORDER BY s.occurred_at DESC, s.id DESC""", db)


def ledger(path, pid=None):
    with connect(path) as db:
        return pd.read_sql_query("SELECT * FROM stock_movements" + (" WHERE product_id=?" if pid is not None else "") + " ORDER BY id DESC", db, params=(int(pid),) if pid is not None else ())

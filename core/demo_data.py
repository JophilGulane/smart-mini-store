"""Reproducible, conspicuously synthetic history; safe to call repeatedly."""
from datetime import timedelta
import numpy as np
from core.database import connect, today

CATALOG = [
    ("Bottled water 500 ml", "Drinks", 10, 15, 11),
    ("Coffee sachet", "Drinks", 6, 9, 9),
    ("Powdered juice", "Drinks", 15, 20, 5),
    ("Crackers", "Snacks", 5, 8, 10),
    ("Chocolate biscuit", "Snacks", 7, 10, 6),
    ("Potato chips", "Snacks", 12, 18, 3),
    ("Instant noodles", "Pantry", 10, 15, 8),
    ("Canned sardines", "Pantry", 20, 27, 4),
    ("Soy sauce sachet", "Pantry", 4, 7, 2),
    ("Shampoo sachet", "Personal care", 5, 8, 5),
    ("Bath soap", "Personal care", 18, 25, 2),
    ("Toothpaste sachet", "Personal care", 6, 10, 3),
]


def seed_demo(path, seed=2026, days=90):
    rng = np.random.default_rng(seed)
    start = today() - timedelta(days=days)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            return False
        for i, (name, category, cost, price, mean) in enumerate(CATALOG):
            observations = []
            for d in range(days):
                day = start + timedelta(days=d)
                factor = (1.45 if day.weekday() < 5 else 0.55) if i % 2 == 0 else (0.8 if day.weekday() < 5 else 1.5)
                qty = int(rng.poisson(mean * factor))
                observations.append((day.isoformat(), qty))
            current = 6 if i in (0, 4, 8) else 25 + i
            opening = sum(q for _, q in observations) + current
            pid = db.execute("INSERT INTO products(name,category,cost_centavos,price_centavos,stock_qty,reorder_level,created_at) VALUES(?,?,?,?,?,?,?)",
                             (name, category, cost*100, price*100, current, 10, start.isoformat()+"T07:00:00+08:00")).lastrowid
            db.execute("INSERT INTO stock_movements(product_id,movement_type,quantity_delta,occurred_at,note) VALUES(?,?,?,?,?)",
                       (pid, "opening", opening, start.isoformat()+"T07:00:00+08:00", "Synthetic opening stock covering demo history"))
            for day, qty in observations:
                db.execute("INSERT INTO daily_history VALUES(?,?,?,?,?)", (pid, day, qty, 0, "synthetic"))
                if qty:
                    ts = day+"T17:00:00+08:00"
                    sid = db.execute("INSERT INTO sales(request_id,product_id,quantity,unit_price_centavos,unit_cost_centavos,occurred_at) VALUES(?,?,?,?,?,?)",
                                     (f"demo-{pid}-{day}", pid, qty, price*100, cost*100, ts)).lastrowid
                    db.execute("INSERT INTO stock_movements(product_id,movement_type,quantity_delta,sale_id,occurred_at,note) VALUES(?,?,?,?,?,?)",
                               (pid, "sale", -qty, sid, ts, "Synthetic historical daily sale"))
    return True

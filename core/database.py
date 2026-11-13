"""SQLite connections are short-lived; transaction boundaries belong to callers."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
MANILA = timezone(timedelta(hours=8))


def today():
    return datetime.now(MANILA).date()


def now():
    return datetime.now(MANILA).isoformat(timespec="seconds")


@contextmanager
def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path):
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
          category TEXT NOT NULL, cost_centavos INTEGER NOT NULL CHECK(cost_centavos>=0),
          price_centavos INTEGER NOT NULL CHECK(price_centavos>=0),
          stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty>=0),
          reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level>=0),
          active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sales (
          id INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE,
          product_id INTEGER NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity>0),
          unit_price_centavos INTEGER NOT NULL, unit_cost_centavos INTEGER NOT NULL,
          occurred_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stock_movements (
          id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
          movement_type TEXT NOT NULL, quantity_delta INTEGER NOT NULL,
          sale_id INTEGER UNIQUE REFERENCES sales(id), occurred_at TEXT NOT NULL,
          note TEXT NOT NULL DEFAULT '', request_id TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS daily_history (
          product_id INTEGER NOT NULL REFERENCES products(id), date TEXT NOT NULL,
          units_sold INTEGER NOT NULL CHECK(units_sold>=0), stockout_flag INTEGER NOT NULL DEFAULT 0,
          source TEXT NOT NULL, PRIMARY KEY(product_id,date));
        CREATE TABLE IF NOT EXISTS model_runs (
          id INTEGER PRIMARY KEY, algorithm TEXT NOT NULL, product_id INTEGER,
          trained_at TEXT NOT NULL, data_cutoff TEXT NOT NULL, data_signature TEXT NOT NULL,
          metrics_json TEXT NOT NULL, artifact_path TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS sales_date ON sales(occurred_at);
        """)

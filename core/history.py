"""Completed-day observations are separate from live stock transactions."""
import hashlib
import json
from datetime import date
import pandas as pd
from core.database import connect, today


def history(path, pid=None):
    with connect(path) as db:
        return pd.read_sql_query("SELECT * FROM daily_history" + (" WHERE product_id=?" if pid is not None else "") + " ORDER BY date,product_id", db, params=(int(pid),) if pid is not None else ())


def signature(frame, settings=None):
    payload = frame.to_json(orient="split", date_format="iso") + json.dumps(settings, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def import_history(path, frame):
    needed = {"product_id", "date", "units_sold"}
    if not needed.issubset(frame.columns) or frame.empty:
        raise ValueError("CSV needs product_id, date, units_sold and at least one row.")
    frame = frame.copy()
    if "stockout_flag" not in frame:
        frame["stockout_flag"] = 0
    for col in ("product_id", "units_sold", "stockout_flag"):
        try:
            numeric = pd.to_numeric(frame[col], errors="raise")
            if numeric.isna().any() or (numeric < 0).any() or ((numeric % 1) != 0).any():
                raise ValueError
            frame[col] = numeric.astype(int)
        except (ValueError, TypeError, OverflowError):
            raise ValueError(f"{col} must contain nonnegative whole numbers.") from None
    if not frame.stockout_flag.isin([0, 1]).all():
        raise ValueError("stockout_flag must be 0 or 1.")
    try:
        frame["date"] = frame["date"].map(lambda x: date.fromisoformat(str(x)).isoformat())
    except (ValueError, TypeError):
        raise ValueError("Dates must use YYYY-MM-DD.") from None
    if (frame.date >= today().isoformat()).any():
        raise ValueError("Only completed days before today can be imported.")
    if frame.duplicated(["product_id", "date"]).any():
        raise ValueError("CSV contains duplicate product/date rows.")
    with connect(path) as db:
        ids = {r[0] for r in db.execute("SELECT id FROM products")}
        if not set(frame.product_id).issubset(ids):
            raise ValueError("CSV contains unknown product IDs. Add those products first.")
        existing = {(r[0], r[1]) for r in db.execute("SELECT product_id,date FROM daily_history")}
        if any((int(r.product_id), r.date) in existing for r in frame.itertuples()):
            raise ValueError("Some product/date observations already exist. No rows were imported.")
        db.executemany("INSERT INTO daily_history VALUES(?,?,?,?,?)", [(int(r.product_id), r.date, int(r.units_sold), int(r.stockout_flag), "imported") for r in frame.itertuples()])
    return len(frame)


def finalize_day(path, selected_date, stockout_ids=()):
    day = date.fromisoformat(str(selected_date))
    if day >= today():
        raise ValueError("Only completed days before today may be finalized.")
    with connect(path) as db:
        eligible = db.execute("SELECT id FROM products WHERE active=1 AND substr(created_at,1,10)<=?", (day.isoformat(),)).fetchall()
        if not eligible:
            raise ValueError("No active products existed on that date.")
        created = 0
        for row in eligible:
            pid = row[0]
            qty = db.execute("SELECT COALESCE(SUM(quantity),0) FROM sales WHERE product_id=? AND substr(occurred_at,1,10)=?", (pid, day.isoformat())).fetchone()[0]
            created += db.execute("INSERT OR IGNORE INTO daily_history VALUES(?,?,?,?,?)", (pid, day.isoformat(), qty, int(pid in stockout_ids), "recorded")).rowcount
    return created

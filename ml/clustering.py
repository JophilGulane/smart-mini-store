"""Group products by a common completed 30-day sales window, without labels."""
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from core.history import signature

FEATURES = ["mean_daily_units", "std_daily_units"]


def product_features(history, products):
    if history.empty:
        raise ValueError("Import or finalize completed daily history first.")
    end = pd.to_datetime(history.date.max())
    days = pd.date_range(end-pd.Timedelta(days=29), end, freq="D").strftime("%Y-%m-%d")
    rows = []
    for product in products.itertuples():
        sub = history[(history.product_id == product.id) & history.date.isin(days)]
        if len(sub) == 30 and sub.date.nunique() == 30 and sub.stockout_flag.eq(0).all():
            rows.append({"product_id": product.id, "product": product.name,
                         "mean_daily_units": float(sub.units_sold.mean()),
                         "std_daily_units": float(sub.units_sold.std(ddof=0))})
    if len(rows) < 3:
        raise ValueError("Need at least three products with complete, non-stockout history in the same last 30 days.")
    return pd.DataFrame(rows), str(days[0]), str(days[-1])


def cluster_products(history, products):
    frame, start, end = product_features(history, products)
    if len(frame[FEATURES].drop_duplicates()) < 3:
        raise ValueError("Need at least three distinct product sales patterns for three clusters.")
    scaler = StandardScaler()
    scaled = scaler.fit_transform(frame[FEATURES])
    model = KMeans(n_clusters=3, n_init=10, random_state=42)
    frame["cluster"] = model.fit_predict(scaled)
    summary = frame.groupby("cluster").agg(products=("product", "count"), mean_daily_units=("mean_daily_units", "mean"), std_daily_units=("std_daily_units", "mean")).reset_index()
    order = summary.sort_values("mean_daily_units").cluster.tolist()
    labels = dict(zip(order, ["Lower average volume", "Middle average volume", "Higher average volume"]))
    frame["group"] = frame.cluster.map(labels)
    summary["description"] = summary.cluster.map(labels)
    metrics = {"eligible_products": len(frame), "window_start": start, "window_end": end,
               "silhouette": float(silhouette_score(scaled, frame.cluster)) if len(frame) > 3 else None}
    return {"model": model, "scaler": scaler, "assignments": frame, "summary": summary,
            "scaled": pd.DataFrame(scaled, columns=FEATURES), "metrics": metrics,
            "signature": signature(history, products.to_dict("records")), "cutoff": end}

"""Chronological, one-day-ahead evaluation; features never include target sales."""
import math
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.tree import DecisionTreeRegressor
from core.history import signature

FEATURES = ["weekday", "yesterday", "mean_7_days"]


def feature_frame(history):
    if history.empty or len(history) < 35:
        raise ValueError("At least 35 completed daily observations are required.")
    frame = history.copy()
    frame["date"] = pd.to_datetime(frame.date)
    frame = frame.sort_values("date").set_index("date")
    if frame.index.duplicated().any():
        raise ValueError("History contains duplicate dates.")
    frame = frame.reindex(pd.date_range(frame.index.min(), frame.index.max(), freq="D"))
    # Missing days and stockout days remain unknown, not zero demand.
    observed = frame.units_sold.where(frame.stockout_flag.eq(0))
    frame["weekday"] = frame.index.day_of_week
    frame["yesterday"] = observed.shift(1)
    frame["mean_7_days"] = observed.shift(1).rolling(7, min_periods=7).mean()
    frame["target"] = observed
    return frame.dropna(subset=FEATURES+["target"])[FEATURES+["target"]].rename_axis("date").reset_index()


def train_forecast(history):
    frame = feature_frame(history)
    if len(frame) < 28:
        raise ValueError("Need at least 28 usable target days after lagging and excluding gaps/stockouts.")
    split = int(len(frame) * 0.8)
    train, test = frame.iloc[:split], frame.iloc[split:]
    model = DecisionTreeRegressor(max_depth=3, min_samples_leaf=5, random_state=42)
    model.fit(train[FEATURES], train.target)
    predicted = np.maximum(0, model.predict(test[FEATURES]))
    predictions = pd.DataFrame({"date": test.date.dt.strftime("%Y-%m-%d"), "actual": test.target.to_numpy(), "prediction": predicted, "baseline": test.mean_7_days.to_numpy()})
    metrics = {"mae": float(mean_absolute_error(test.target, predicted)),
               "baseline_mae": float(mean_absolute_error(test.target, test.mean_7_days)),
               "train_rows": len(train), "test_rows": len(test),
               "train_start": str(train.date.iloc[0].date()), "train_end": str(train.date.iloc[-1].date()),
               "test_start": str(test.date.iloc[0].date()), "test_end": str(test.date.iloc[-1].date())}
    # Keep the evaluated tree distinct from the final all-history inference tree.
    final = DecisionTreeRegressor(max_depth=3, min_samples_leaf=5, random_state=42)
    final.fit(frame[FEATURES], frame.target)
    return {"model": final, "evaluated_model": model, "predictions": predictions,
            "features": frame, "metrics": metrics, "signature": signature(history), "cutoff": str(history.date.max())}


def predict_next(result, history):
    frame = history.sort_values("date").tail(7).copy()
    if len(frame) < 7 or frame.stockout_flag.ne(0).any():
        raise ValueError("The last seven days must have complete, non-stockout observations.")
    dates = pd.to_datetime(frame.date)
    if (dates.diff().dropna() != pd.Timedelta(days=1)).any():
        raise ValueError("The last seven observations must be consecutive calendar days.")
    next_date = dates.iloc[-1] + pd.Timedelta(days=1)
    features = pd.DataFrame([[next_date.day_of_week, float(frame.units_sold.iloc[-1]), float(frame.units_sold.mean())]], columns=FEATURES)
    raw = max(0.0, float(result["model"].predict(features)[0]))
    return {"date": str(next_date.date()), "raw_units": raw, "units": int(math.floor(raw+0.5)), "inputs": features}

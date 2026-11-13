import pandas as pd
import pytest
from core.history import history
from ml.forecasting import feature_frame, train_forecast, predict_next


def test_target_change_does_not_change_its_features(demo):
    raw = history(demo, 1)
    original = feature_frame(raw)
    changed = raw.copy()
    changed.loc[changed.index[-1], "units_sold"] = 99999
    after = feature_frame(changed)
    assert original.iloc[-1].yesterday == after.iloc[-1].yesterday
    assert original.iloc[-1].mean_7_days == after.iloc[-1].mean_7_days
    assert after.iloc[-1].target == 99999


def test_missing_days_are_not_zero_filled(demo):
    raw = history(demo, 1)
    missing_date = raw.iloc[40].date
    frame = feature_frame(raw.drop(raw.index[40]))
    excluded = pd.date_range(missing_date, periods=8).strftime("%Y-%m-%d")
    assert not frame.date.dt.strftime("%Y-%m-%d").isin(excluded).any()


def test_forecast_chronology_and_metrics(demo):
    raw = history(demo, 1)
    result = train_forecast(raw)
    assert result["metrics"]["train_end"] < result["metrics"]["test_start"]
    error = (result["predictions"].actual-result["predictions"].prediction).abs().mean()
    assert result["metrics"]["mae"] == pytest.approx(error)
    forecast = predict_next(result, raw)
    assert pd.Timestamp(forecast["date"]) > pd.Timestamp(raw.date.max())
    assert forecast["units"] >= 0


def test_clustering_uses_real_features_without_labels(demo):
    from ml.clustering import cluster_products
    from core.inventory import products
    result = cluster_products(history(demo), products(demo, True))
    assert len(result["assignments"]) == 12
    assert result["assignments"].cluster.nunique() == 3
    assert (result["scaled"].mean().abs() < 1e-10).all()

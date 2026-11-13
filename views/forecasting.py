import streamlit as st
import plotly.express as px
from sklearn.tree import export_text
from core.history import history, signature
from core.artifacts import latest_run, save_run
from ml.forecasting import train_forecast, predict_next, FEATURES
from views.common import choose_product, provenance, chart, download_csv


def render(path):
    st.title("Tomorrow's sales")
    st.write("Supervised learning · A Decision Tree learns from historical sales with known answers.")
    row = choose_product(path, "forecast_product_"+path.stem)
    if row is None:
        return
    hist = history(path, row.id)
    st.caption(f"{len(hist)} completed daily observations. Known stockout observations and missing days are excluded from usable forecast windows.")
    with st.expander("1 · Inspect the input data"):
        st.dataframe(hist.tail(14), hide_index=True, width="stretch")
        st.write("Inputs: target weekday, yesterday's units, preceding seven-day mean. Target: units sold on that day. Sales are a proxy for demand when stock is adequate.")
    if st.button("Train & evaluate forecast", type="primary"):
        try:
            with st.spinner("Training on earlier dates and evaluating on later dates…"):
                result = train_forecast(hist)
                save_run(path, "forecast", result, row.id)
            st.success("Training and held-out evaluation completed.")
        except ValueError as exc:
            st.error(str(exc))
    result, meta = latest_run(path, "forecast", row.id)
    if result is None:
        st.info("Train a model to see its predictions. At least 35 completed observations and 28 usable feature rows are needed.")
        return
    provenance(meta)
    if result["signature"] != signature(hist):
        st.warning("History has changed since this model was trained. Retrain before using its results.")
        return
    st.subheader("2 · Next-day forecast")
    try:
        prediction = predict_next(result, hist)
        a, b = st.columns([1, 2])
        a.metric(f"Expected units · {prediction['date']}", prediction["units"])
        b.write(f"Current stock: **{int(row.stock_qty)} units**. A forecast estimates sales; it does not automatically purchase stock.")
        st.caption(f"Unrounded estimate: {prediction['raw_units']:.2f} units. Forecast date is the day after the latest completed history, which may be earlier than today if records are out of date.")
        if st.checkbox("Show forecast inputs"):
            st.dataframe(prediction["inputs"], hide_index=True)
    except ValueError as exc:
        st.info(str(exc))
    st.subheader("3 · Test on unseen later dates")
    m = result["metrics"]
    a, b, c = st.columns(3)
    a.metric("Decision Tree MAE", f"{m['mae']:.2f} units")
    b.metric("7-day mean baseline MAE", f"{m['baseline_mae']:.2f} units")
    c.metric("Held-out days", m["test_rows"])
    st.caption(f"Train: {m['train_start']}–{m['train_end']} ({m['train_rows']} days). Test: {m['test_start']}–{m['test_end']}. Lower MAE is better. These are one-day-ahead tests, with prior actual days available.")
    chart(px.line(result["predictions"], x="date", y=["actual", "prediction", "baseline"], labels={"value": "Units sold", "date": "Test date"}, markers=True))
    download_csv(result["predictions"], "Export forecast evaluation", "forecast-evaluation.csv")
    with st.expander("How the code works"):
        st.write("The evaluated tree sees only the earlier 80% of eligible dates. A separate final tree is refitted on all history for the next-day forecast. Depth 3 and minimum leaf size 5 keep the model small.")
        st.code('observed.shift(1).rolling(7, min_periods=7).mean()\nmodel = DecisionTreeRegressor(max_depth=3, min_samples_leaf=5, random_state=42)\nmodel.fit(train[FEATURES], train.target)\npredicted = model.predict(test[FEATURES])', language="python")
        st.dataframe(result["features"].tail(14), hide_index=True)
        st.code(export_text(result["evaluated_model"], feature_names=FEATURES), language="text")

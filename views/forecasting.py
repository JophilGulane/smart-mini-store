from datetime import datetime

import plotly.express as px
import streamlit as st
from sklearn.tree import export_text

from core.artifacts import latest_run, save_run
from core.history import history, signature
from ml.forecasting import FEATURES, predict_next, train_forecast
from views import ui
from views.common import chart, choose_product, download_csv, provenance


def render(path):
    ui.page_header(
        "Demand forecast",
        "Tomorrow's sales",
        "Supervised learning · A Decision Tree learns from completed daily sales with known answers.",
    )
    with st.container(border=True):
        ui.section("Model run", "Decision Tree · depth 3")
        row = choose_product(path, "forecast_product_" + path.stem)
        if row is None:
            return
        hist = history(path, row.id)
        info, action = st.columns([2.1, 1], vertical_alignment="bottom")
        with info:
            st.caption(
                f"{len(hist):,} completed daily observations for {row['name']}. Known stockout observations and missing days are excluded from usable windows."
            )
        with action:
            train = st.button("Train & evaluate forecast", type="primary", key="forecast_train_" + path.stem)
        with st.expander("Input data · last 14 observations"):
            st.dataframe(hist.tail(14), hide_index=True, width="stretch")
            st.caption(
                "Inputs: target weekday, yesterday's units, and the preceding seven-day mean. Target: units sold that day, a proxy for demand when stock is adequate."
            )

    if train:
        try:
            with st.spinner("Training on earlier dates and evaluating on later dates…"):
                result = train_forecast(hist)
                save_run(path, "forecast", result, row.id)
            st.success("Training and held-out evaluation completed.")
        except ValueError as exc:
            st.error(str(exc))

    result, meta = latest_run(path, "forecast", row.id)
    if result is None:
        ui.empty_state(
            "No saved forecast yet",
            "Train a model to see its next-day estimate and its measured error. At least 35 completed observations and 28 usable feature rows are needed.",
            "Train & evaluate forecast",
        )
        return
    provenance(meta)
    if result["signature"] != signature(hist):
        ui.note("History changed", "This model predates the current history. Retrain before using its results.", "warn")
        return

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        ui.section("Next-day estimate", "After the latest completed history")
        try:
            prediction = predict_next(result, hist)
            stock = int(row.stock_qty)
            gap = prediction["units"] - stock
            stock_chip = ui.chip(f"Short {gap} units", "warn") if gap > 0 else ui.chip("Stock covers forecast", "good")
            forecast_day = datetime.fromisoformat(prediction["date"]).strftime("%a %d %b %Y")
            st.markdown(
                f'<div class="ms-forecast">'
                f'<div class="ms-forecast-top"><div>'
                f'<div class="ms-receipt-kicker">Expected units</div>'
                f'<div class="ms-forecast-figure">{prediction["units"]:,}<small>units</small></div>'
                f"</div>"
                f'<div class="ms-forecast-side">'
                f'<div class="ms-forecast-date">{ui.esc(forecast_day)}</div>'
                f"{stock_chip}"
                f"</div></div>"
                f'<div class="ms-forecast-foot"><span>Stock on hand <strong>{stock:,} units</strong></span>'
                f'<span class="ms-sep"></span>'
                f"<span>Unrounded estimate {prediction['raw_units']:.2f}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(
                "The forecast estimates sales; it does not purchase stock. The date follows the latest completed history, which may be earlier than today."
            )
            with st.expander("Forecast inputs"):
                st.dataframe(prediction["inputs"], hide_index=True)
        except ValueError as exc:
            ui.note("Estimate unavailable", str(exc), "warn")

    m = result["metrics"]
    better = m["mae"] <= m["baseline_mae"]
    ui.stat_row(
        [
            {"label": "Tree MAE", "value": f"{m['mae']:.2f}", "sub": "units · lower is better", "tone": "accent"},
            {"label": "7-day mean MAE", "value": f"{m['baseline_mae']:.2f}", "sub": "baseline on the same days", "tone": "neutral"},
            {"label": "Held-out days", "value": f"{m['test_rows']:,}", "sub": f"{m['test_start']} → {m['test_end']}", "tone": "neutral"},
        ]
    )
    difference = abs(m["mae"] - m["baseline_mae"])
    ui.note(
        "Measured on later, unseen dates",
        (
            f"The tree beats the seven-day mean by {difference:.2f} units of MAE on {m['test_rows']} held-out days."
            if better
            else f"The tree trails the seven-day mean by {difference:.2f} units of MAE on {m['test_rows']} held-out days."
        )
        + f" Train: {m['train_start']}–{m['train_end']} ({m['train_rows']} days). Test: {m['test_start']}–{m['test_end']}. These are one-day-ahead tests with prior actual days available.",
        "good" if better else "warn",
    )

    with st.container(border=True):
        ui.section("Actual vs predicted", "Held-out test dates")
        fig = px.line(
            result["predictions"],
            x="date",
            y=["actual", "prediction", "baseline"],
            markers=True,
            labels={"value": "Units sold", "date": "Test date", "variable": "Series"},
            color_discrete_map={"actual": "#365455", "prediction": ui.TEAL, "baseline": "#B08A45"},
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=5))
        renamed = {"actual": "Actual", "prediction": "Tree forecast", "baseline": "7-day mean"}
        fig.for_each_trace(lambda trace: trace.update(name=renamed.get(trace.name, trace.name)))
        chart(fig, key="forecast_chart_" + path.stem)
    download_csv(result["predictions"], "Export forecast evaluation", "forecast-evaluation.csv")

    with st.expander("How the code works"):
        st.write(
            "The evaluated tree sees only the earlier 80% of eligible dates. A separate final tree refits on all history for the next-day forecast. Depth 3 and minimum leaf size 5 keep the model small."
        )
        st.code(
            'observed.shift(1).rolling(7, min_periods=7).mean()\n'
            "model = DecisionTreeRegressor(max_depth=3, min_samples_leaf=5, random_state=42)\n"
            "model.fit(train[FEATURES], train.target)\n"
            "predicted = model.predict(test[FEATURES])",
            language="python",
        )
        st.dataframe(result["features"].tail(14), hide_index=True, width="stretch")
        st.code(export_text(result["evaluated_model"], feature_names=FEATURES), language="text")

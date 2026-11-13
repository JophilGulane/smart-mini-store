import plotly.express as px
import streamlit as st

from core.artifacts import latest_run, save_run
from core.history import history, signature
from core.inventory import products
from ml.clustering import cluster_products
from views import ui
from views.common import COLORS, chart, download_csv, provenance


def render(path):
    ui.page_header(
        "Product groups",
        "Discover product patterns",
        "Unsupervised learning · K-means groups products with similar sales behaviour, without correct group labels.",
    )
    hist, items = history(path), products(path, True)
    with st.container(border=True):
        ui.section("Model run", "Three groups · same 30 days")
        st.caption(
            "Each product is described by mean daily sales and sales variability over the same completed 30 days. Only complete, non-stockout windows are included."
        )
        run = st.button("Run product clustering", type="primary", key="cluster_run")

    if run:
        try:
            with st.spinner("Standardizing features and finding three groups…"):
                result = cluster_products(hist, items)
                save_run(path, "clusters", result)
            st.success("Clustering completed.")
        except ValueError as exc:
            st.error(str(exc))

    result, meta = latest_run(path, "clusters")
    if result is None:
        ui.empty_state(
            "No groups yet",
            "Run clustering to see the groups. Three products with distinct patterns and complete 30-day history are required.",
            "Run product clustering",
        )
        return
    provenance(meta)
    if result["signature"] != signature(hist, items.to_dict("records")):
        ui.note("Products or history changed", "Run clustering again for current groups.", "warn")
        return

    m = result["metrics"]
    ui.stat_row(
        [
            {"label": "Products grouped", "value": f"{m['eligible_products']:,}", "sub": "Complete 30-day windows", "tone": "accent"},
            {
                "label": "Silhouette score",
                "value": f"{m['silhouette']:.3f}" if m["silhouette"] is not None else "n/a",
                "sub": "Separation, not accuracy · −1 to 1",
                "tone": "neutral",
            },
            {"label": "Window", "value": "30 days", "sub": f"{m['window_start']} → {m['window_end']}", "tone": "neutral"},
        ]
    )
    st.caption(
        "Higher silhouette means stronger separation; it is not classification accuracy. Clusters can overlap."
    )

    summary = result["summary"].sort_values("mean_daily_units")
    groups = result["assignments"][["cluster", "group"]].drop_duplicates().sort_values("cluster")
    palette = {row.group: COLORS[index % len(COLORS)] for index, row in enumerate(groups.itertuples())}
    cards = []
    for row in summary.itertuples():
        color = palette.get(row.description, COLORS[0])
        cards.append(
            f'<div class="ms-group">'
            f'<div class="ms-group-top"><span class="ms-group-dot" style="background:{color}"></span>'
            f'<span class="ms-group-name">{ui.esc(row.description)}</span></div>'
            f'<div class="ms-group-value">{row.mean_daily_units:.1f}<small>units/day</small></div>'
            f'<div class="ms-group-meta">{int(row.products)} products · ±{row.std_daily_units:.1f} std</div>'
            f"</div>"
        )
    st.markdown(f'<div class="ms-group-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    with st.container(border=True):
        ui.section("Sales behaviour", "Average volume vs variability")
        frame = result["assignments"]
        fig = px.scatter(
            frame,
            x="mean_daily_units",
            y="std_daily_units",
            color="group",
            hover_name="product",
            color_discrete_map=palette,
            category_orders={"group": summary.description.tolist()},
            labels={
                "mean_daily_units": "Average daily sales (units)",
                "std_daily_units": "Sales variability (std)",
                "group": "",
            },
        )
        fig.update_traces(marker=dict(size=13, line=dict(width=2, color="#FFFFFF")))
        fig.update_layout(height=330)
        chart(fig, key="cluster_chart")

    ui.section("Group summaries", "Descriptions reflect measured volume", spaced=True)
    st.dataframe(
        summary[["description", "products", "mean_daily_units", "std_daily_units"]],
        hide_index=True,
        width="stretch",
        column_config={
            "description": st.column_config.TextColumn("Group", width="medium"),
            "products": st.column_config.NumberColumn("Products", format="%d", width="small"),
            "mean_daily_units": st.column_config.NumberColumn("Avg units/day", format="%.2f"),
            "std_daily_units": st.column_config.NumberColumn("Variability", format="%.2f"),
        },
    )
    st.caption(
        "Descriptions summarize average volume after fitting. Cluster IDs have no built-in ranking, and products can differ in variability within a group."
    )
    download_csv(frame, "Export product groups", "product-groups.csv")

    with st.expander("Assignments and scaled features"):
        st.dataframe(
            frame[["product", "group", "mean_daily_units", "std_daily_units"]],
            hide_index=True,
            width="stretch",
            column_config={
                "mean_daily_units": st.column_config.NumberColumn("Avg units/day", format="%.2f"),
                "std_daily_units": st.column_config.NumberColumn("Variability", format="%.2f"),
            },
        )
        st.dataframe(result["scaled"], hide_index=True, width="stretch")

    with st.expander("Inputs, preprocessing & implementation"):
        st.write(
            "Standardization gives each feature mean zero and unit variance before distance calculations. K-means assigns products to nearby centers and updates those centers."
        )
        st.code(
            'scaled = StandardScaler().fit_transform(frame[FEATURES])\n'
            "model = KMeans(n_clusters=3, n_init=10, random_state=42)\n"
            'frame["cluster"] = model.fit_predict(scaled)',
            language="python",
        )

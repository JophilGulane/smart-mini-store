import streamlit as st
import plotly.express as px
from core.inventory import products
from core.history import history, signature
from core.artifacts import latest_run, save_run
from ml.clustering import cluster_products
from views.common import chart, download_csv, provenance, COLORS


def render(path):
    st.title("Discover product patterns")
    st.write("Unsupervised learning · K-means finds products with similar sales behavior, without correct group labels.")
    hist, items = history(path), products(path, True)
    st.caption("Each product is described by mean daily sales and sales variability over the same completed 30 days. Only complete, non-stockout windows are included.")
    if st.button("Run product clustering", type="primary"):
        try:
            with st.spinner("Standardizing features and finding three groups…"):
                result = cluster_products(hist, items)
                save_run(path, "clusters", result)
            st.success("Clustering completed.")
        except ValueError as exc:
            st.error(str(exc))
    result, meta = latest_run(path, "clusters")
    if result is None:
        st.info("Run clustering to see the groups. Three products with distinct patterns and complete 30-day history are required.")
        return
    provenance(meta)
    if result["signature"] != signature(hist, items.to_dict("records")):
        st.warning("Products or history have changed. Run clustering again for current groups.")
        return
    m = result["metrics"]
    a, b = st.columns(2)
    a.metric("Products grouped", m["eligible_products"])
    b.metric("Silhouette score", f"{m['silhouette']:.3f}" if m["silhouette"] is not None else "Not applicable")
    st.caption(f"Window: {m['window_start']}–{m['window_end']}. Silhouette ranges from -1 to 1; higher indicates stronger separation. It is not classification accuracy.")
    frame = result["assignments"]
    chart(px.scatter(frame, x="mean_daily_units", y="std_daily_units", color="group", hover_name="product", size_max=15,
                     color_discrete_sequence=COLORS, labels={"mean_daily_units": "Average daily sales (units)", "std_daily_units": "Sales variability (standard deviation)"}).update_traces(marker_size=14))
    st.subheader("Group summaries")
    st.dataframe(result["summary"], hide_index=True, width="stretch")
    st.caption("Descriptions summarize measured average volume after fitting. Clusters can overlap, and products may differ in variability within a group. Cluster IDs have no built-in ranking.")
    st.dataframe(frame, hide_index=True, width="stretch")
    download_csv(frame, "Export product groups", "product-groups.csv")
    with st.expander("Inputs, preprocessing & implementation"):
        st.dataframe(frame[["product", "mean_daily_units", "std_daily_units"]], hide_index=True)
        st.write("Standardization gives each feature mean zero and unit variance before distance calculations. K-means assigns products to nearby centers and updates those centers.")
        st.dataframe(result["scaled"], hide_index=True)
        st.code('scaled = StandardScaler().fit_transform(frame[FEATURES])\nmodel = KMeans(n_clusters=3, n_init=10, random_state=42)\nframe["cluster"] = model.fit_predict(scaled)', language="python")

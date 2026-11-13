"""Run with: python -m streamlit run streamlit_app.py"""
import os
from pathlib import Path

import streamlit as st

from core.database import ROOT, initialize, today
from core.demo_data import seed_demo
from views import clustering, dashboard, forecasting, products, sales, simulator, ui

PAGES = [
    "Dashboard",
    "Products & Stock",
    "Record Sales",
    "Demand Forecast",
    "Product Groups",
    "Restocking Simulator",
]

st.set_page_config(page_title="Mini-Store · Inventory Assistant", page_icon="🏪", layout="wide")
ui.install_theme()

with st.sidebar:
    st.markdown(
        '<div class="ms-brand">'
        '<div class="ms-mark">MS</div>'
        '<div><div class="ms-word">Mini-Store</div>'
        '<div class="ms-word-sub">Inventory assistant</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ms-nav-label">Workspace</div>', unsafe_allow_html=True)
    mode = st.selectbox(
        "Workspace",
        ["Demonstration", "My store"],
        label_visibility="collapsed",
        key="workspace",
    )
    if mode == "Demonstration":
        st.markdown(
            '<div class="ms-ws-note">Synthetic history. Isolated from your own store records.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="ms-ws-note">Your records. Saved on this computer only.</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="ms-nav-label">Screens</div>', unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, label_visibility="collapsed", key="nav_page")
    st.markdown(
        f'<div class="ms-foot"><strong>{today():%d %b %Y}</strong>'
        "Asia/Manila · UTC+8<br>Local data only</div>",
        unsafe_allow_html=True,
    )
    with st.expander("About this project"):
        st.write("Three learning methods: a Decision Tree for demand, K-means for product groups, and tabular Q-learning for restocking.")
        st.write("Forecasts use completed history. Simulated restocking is advisory and never changes stock. Transactions stay on this computer.")

data_dir = Path(os.environ.get("MINISTORE_DATA_DIR", str(ROOT / "data")))
path = data_dir / ("demo.db" if mode == "Demonstration" else "store.db")
initialize(path)
if mode == "Demonstration":
    seed_demo(path)
    ui.context_bar(
        ["Demonstration workspace", "Synthetic sales history", "Isolated from My store", "Business date " + f"{today():%d %b %Y}"],
        tone="amber",
    )
else:
    ui.context_bar(
        ["My store", "Your local records", "Business date " + f"{today():%d %b %Y}"],
        tone="teal",
    )

pages = {
    "Dashboard": dashboard,
    "Products & Stock": products,
    "Record Sales": sales,
    "Demand Forecast": forecasting,
    "Product Groups": clustering,
    "Restocking Simulator": simulator,
}
pages[page].render(path)

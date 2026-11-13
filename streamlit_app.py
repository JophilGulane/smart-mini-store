"""Run with: python -m streamlit run streamlit_app.py"""
import os
from pathlib import Path
import streamlit as st
from core.database import ROOT, initialize, today
from core.demo_data import seed_demo
from views import dashboard, products, sales, forecasting, clustering, simulator

st.set_page_config(page_title="Mini-Store · Inventory Assistant", page_icon="🏪", layout="wide")
st.markdown("""<style>
.block-container {padding-top:4rem; max-width:1440px;}
h1 {font-weight:750; letter-spacing:-0.035em;}
h2,h3 {letter-spacing:-0.02em;}
[data-testid="stMetric"] {background:white;border:1px solid #E3E9ED;border-radius:12px;padding:16px;}
[data-testid="stSidebar"] {border-right:1px solid #E3E9ED;}
div.stButton > button {border-radius:8px;}
@media (max-width:1100px) {
  [data-testid="stMetricValue"] {font-size:1.35rem;}
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap:wrap;}
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {min-width:45%;flex:1 1 45%;}
}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## MINI-STORE")
    st.caption("Inventory assistant")
    mode = st.selectbox("Workspace", ["Demonstration", "My store"])
    st.divider()
    page = st.radio("Navigate", ["Dashboard", "Products & Stock", "Record Sales", "Demand Forecast", "Product Groups", "Restocking Simulator"], label_visibility="collapsed")
    st.divider()
    st.caption("One store. Clear records. Better decisions.")
    with st.expander("About this project"):
        st.write("Supervised: Decision Tree regression. Unsupervised: K-means. Reinforcement: tabular Q-learning.")
        st.write("Forecasts use completed history. Simulated restocking suggestions are advisory. Transactions are stored locally.")
        st.write(f"Local business date: {today()} (Asia/Manila)")

data_dir = Path(os.environ.get("MINISTORE_DATA_DIR", str(ROOT/"data")))
path = data_dir / ("demo.db" if mode == "Demonstration" else "store.db")
initialize(path)
if mode == "Demonstration":
    seed_demo(path)
    st.caption("DEMONSTRATION WORKSPACE · Synthetic sales history · Isolated from My store records")
else:
    st.caption("MY STORE · Your local inventory and sales records")

pages = {"Dashboard": dashboard, "Products & Stock": products, "Record Sales": sales,
         "Demand Forecast": forecasting, "Product Groups": clustering, "Restocking Simulator": simulator}
pages[page].render(path)

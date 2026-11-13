from datetime import timedelta
import streamlit as st
import plotly.express as px
from core.database import today
from core.inventory import products, sales
from views.common import chart, download_csv


def render(path):
    st.title("Your store, at a glance")
    st.write("Track what is selling and what needs attention.")
    items, transactions = products(path, True), sales(path)
    dates = st.date_input("Sales period", (today()-timedelta(days=29), today()), max_value=today())
    if len(dates) != 2:
        st.info("Choose a start and end date.")
        return
    start, end = map(str, dates)
    period = transactions[transactions.date.between(start, end)] if not transactions.empty else transactions
    low = items[items.stock_qty <= items.reorder_level] if not items.empty else items
    a, b, c, d = st.columns(4)
    a.metric("Active products", len(items))
    b.metric("Need restocking", len(low))
    c.metric("Sales revenue", f"PHP {period.revenue_php.sum():,.2f}")
    d.metric("Inventory at cost", f"PHP {(items.stock_qty*items.cost_centavos).sum()/100:,.2f}")
    st.caption("Revenue follows the selected period. Inventory shows the current active-product balance; it is valued at the current unit cost.")
    left, right = st.columns([1.7, 1])
    with left:
        st.subheader("Daily sales")
        if period.empty:
            st.info("No recorded sales in this period. Record a sale or change the dates.")
        else:
            grouped = period.groupby("date", as_index=False).revenue_php.sum()
            chart(px.bar(grouped, x="date", y="revenue_php", labels={"date": "Date", "revenue_php": "Revenue (PHP)"}, color_discrete_sequence=["#087F75"]))
    with right:
        st.subheader("Stock to watch")
        if low.empty:
            st.success("No active products are below their reorder threshold.")
        else:
            st.dataframe(low[["name", "stock_qty", "reorder_level"]].rename(columns={"name": "Product", "stock_qty": "Available", "reorder_level": "Alert at"}), hide_index=True, width="stretch")
            st.caption("Alerts are threshold rules. The learning features are on their own pages.")
    st.subheader("Sales records")
    st.dataframe(period[["id", "product", "quantity", "unit_price_php", "revenue_php", "date"]], hide_index=True, width="stretch")
    download_csv(period, "Export sales CSV", "sales-summary.csv")

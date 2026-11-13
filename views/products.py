import uuid
from datetime import timedelta
import pandas as pd
import streamlit as st
from core.database import today
from core import inventory
from core.history import history, import_history, finalize_day
from views.common import choose_product, download_csv


def render(path):
    st.title("Products & stock")
    st.write("Keep a reliable product list and record stock when it arrives.")
    if "product_flash" in st.session_state:
        st.success(st.session_state.pop("product_flash"))
    items = inventory.products(path)
    if not items.empty:
        table = items.copy()
        table["Cost (PHP)"] = table.cost_centavos/100
        table["Price (PHP)"] = table.price_centavos/100
        table["Status"] = table.apply(lambda r: "Archived" if not r.active else ("Low stock" if r.stock_qty <= r.reorder_level else "In stock"), axis=1)
        st.dataframe(table[["id", "name", "category", "Cost (PHP)", "Price (PHP)", "stock_qty", "reorder_level", "Status"]], hide_index=True, width="stretch")
        download_csv(table.drop(columns=["cost_centavos", "price_centavos"]), "Export products CSV", "products.csv")
    tabs = st.tabs(["Add product", "Receive stock", "Edit product", "History & data"])
    with tabs[0]:
        with st.form("add_product", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Product name")
            category = b.text_input("Category", "General")
            cost = a.number_input("Unit cost (PHP)", 0.0, value=10.0, step=0.5, format="%.2f")
            price = b.number_input("Selling price (PHP)", 0.0, value=15.0, step=0.5, format="%.2f")
            opening = a.number_input("Opening stock", 0, value=0, step=1)
            level = b.number_input("Low-stock threshold", 0, value=10, step=1)
            if st.form_submit_button("Add product", type="primary"):
                try:
                    inventory.add_product(path, name, category, cost, price, opening, level)
                    st.session_state.product_flash = "Product added."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with tabs[1]:
        row = choose_product(path, "receive_product")
        if row is not None:
            st.caption(f"Available now: {int(row.stock_qty)} units")
            token = st.session_state.setdefault("receipt_token", str(uuid.uuid4()))
            with st.form("receive_stock", clear_on_submit=True):
                qty = st.number_input("Units received", 1, value=10, step=1)
                note = st.text_input("Receipt note", "Stock received")
                if st.form_submit_button("Record stock receipt", type="primary"):
                    try:
                        inventory.receive_stock(path, row.id, qty, token, note)
                        st.session_state.receipt_token = str(uuid.uuid4())
                        st.session_state.product_flash = f"Received {qty} units of {row['name']}."
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            with st.expander("Stock movement history"):
                st.dataframe(inventory.ledger(path, row.id), hide_index=True, width="stretch")
    with tabs[2]:
        row = choose_product(path, "edit_product", active=False)
        if row is not None:
            with st.form(f"edit_{row.id}"):
                a, b = st.columns(2)
                name = a.text_input("Name", row["name"])
                category = b.text_input("Product category", row.category)
                cost = a.number_input("Current unit cost (PHP)", 0.0, value=float(row.cost_centavos/100), step=0.5, format="%.2f")
                price = b.number_input("Current selling price (PHP)", 0.0, value=float(row.price_centavos/100), step=0.5, format="%.2f")
                level = a.number_input("Reorder threshold", 0, value=int(row.reorder_level), step=1)
                active = b.checkbox("Active product", bool(row.active))
                st.caption("Archiving preserves sales history. Price changes affect future sales only.")
                if st.form_submit_button("Save product"):
                    try:
                        inventory.edit_product(path, row.id, name, category, cost, price, level, active)
                        st.session_state.product_flash = "Product updated."
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
    with tabs[3]:
        st.subheader("Completed daily history")
        st.write("These observations feed the ML pages. Importing history does not create sales receipts or change current stock.")
        hist = history(path)
        st.dataframe(hist.tail(60), hide_index=True, width="stretch")
        download_csv(hist, "Export daily history", "daily-history.csv")
        st.download_button("Download CSV template", "product_id,date,units_sold,stockout_flag\n", "history-template.csv", "text/csv")
        upload = st.file_uploader("Import completed daily observations", type="csv")
        if upload is not None and st.button("Validate and import CSV"):
            try:
                count = import_history(path, pd.read_csv(upload))
                st.session_state.product_flash = f"Imported {count} observations. Retrain affected models."
                st.rerun()
            except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
                st.error(str(exc))
        with st.expander("Finalize a completed selling day"):
            st.write("Confirm that all sales were recorded, including genuine zero-sales days. Existing observations are preserved. Flag products whose sales were limited by unavailable stock.")
            day = st.date_input("Completed date", today()-timedelta(days=1), max_value=today()-timedelta(days=1))
            active_items = items[items.active.eq(1)]
            names = dict(zip(active_items.id, active_items.name))
            stockouts = st.multiselect("Products with stockouts", active_items.id.tolist(), format_func=lambda x: names[x])
            confirm = st.checkbox("All transactions for this date have been recorded")
            if st.button("Finalize daily observations", disabled=not confirm):
                try:
                    n = finalize_day(path, day, stockouts)
                    st.session_state.product_flash = f"Finalized {n} new daily observations. Existing history was preserved."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

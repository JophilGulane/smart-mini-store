import uuid
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import inventory
from core.database import today
from core.history import finalize_day, history, import_history
from views import ui
from views.common import choose_product, download_csv


def _status(row):
    if not row.active:
        return "Archived"
    if row.stock_qty == 0:
        return "Out of stock"
    if row.stock_qty <= row.reorder_level:
        return "Low stock"
    return "In stock"


def render(path):
    ui.page_header(
        "Products & Stock",
        "Products & stock",
        "Keep a reliable product list, receive stock when it arrives, and preserve the history the models learn from.",
    )
    if "product_flash" in st.session_state:
        st.success(st.session_state.pop("product_flash"))

    items = inventory.products(path)
    active = items[items.active.eq(1)] if not items.empty else items
    low = active[active.stock_qty <= active.reorder_level] if not active.empty else active
    inventory_value = float((active.stock_qty * active.cost_centavos).sum()) / 100 if not active.empty else 0.0
    ui.stat_row(
        [
            {"label": "Active products", "value": f"{len(active):,}", "sub": f"{len(items):,} in the catalogue including archived", "tone": "accent"},
            {"label": "Need restocking", "value": f"{len(low):,}", "sub": "At or below the alert threshold", "tone": "warn" if len(low) else "good"},
            {"label": "Out of stock", "value": f"{int((active.stock_qty == 0).sum()) if not active.empty else 0:,}", "sub": "Blocked from selling until received", "tone": "bad" if not active.empty and (active.stock_qty == 0).any() else "good"},
            {"label": "Inventory at cost", "prefix": "PHP", "value": f"{inventory_value:,.2f}", "sub": "Current active balance", "tone": "neutral"},
        ]
    )

    if items.empty:
        ui.empty_state(
            "Your store is empty",
            "Add your first product below. Opening stock creates the first movement record; nothing is imported from the demo.",
            "Add product → fill in the form",
        )
    else:
        table = items.copy()
        table["Cost (PHP)"] = table.cost_centavos / 100
        table["Price (PHP)"] = table.price_centavos / 100
        table["Status"] = table.apply(_status, axis=1)
        ui.section("Catalogue", f"{len(table):,} products", spaced=True)
        f1, f2, f3 = st.columns([1.5, 1.1, 1.1])
        query = f1.text_input("Search products", placeholder="Name or category", key="product_search")
        category = f2.selectbox(
            "Category",
            ["All categories"] + sorted(table.category.unique().tolist()),
            key="product_category",
        )
        status = f3.selectbox(
            "Status",
            ["All products", "In stock", "Low stock", "Out of stock", "Archived"],
            key="product_status",
        )
        filtered = table.copy()
        if query:
            mask = filtered.name.str.contains(query, case=False, na=False) | filtered.category.str.contains(query, case=False, na=False)
            filtered = filtered[mask]
        if category != "All categories":
            filtered = filtered[filtered.category.eq(category)]
        if status != "All products":
            filtered = filtered[filtered.Status.eq(status)]
        if filtered.empty:
            ui.empty_state("No products match", "Clear the search or choose a different category and status.")
        else:
            st.dataframe(
                filtered[["id", "name", "category", "Cost (PHP)", "Price (PHP)", "stock_qty", "reorder_level", "Status"]],
                hide_index=True,
                width="stretch",
                height=min(420, 56 + 35 * len(filtered)),
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "name": st.column_config.TextColumn("Product", width="medium"),
                    "category": st.column_config.TextColumn("Category"),
                    "Cost (PHP)": st.column_config.NumberColumn("Unit cost", format="%.2f", width="small"),
                    "Price (PHP)": st.column_config.NumberColumn("Selling price", format="%.2f", width="small"),
                    "stock_qty": st.column_config.NumberColumn("Stock", format="%d", width="small"),
                    "reorder_level": st.column_config.NumberColumn("Alert at", format="%d", width="small"),
                    "Status": st.column_config.TextColumn("Status"),
                },
            )
            st.caption(
                f"Showing {len(filtered):,} of {len(table):,} products · amounts in PHP. "
                "Archived products keep their history and cannot be sold."
            )
        download_csv(table.drop(columns=["cost_centavos", "price_centavos"]), "Export products CSV", "products.csv")

    tabs = st.tabs(["Add product", "Receive stock", "Edit product", "History & data"])
    with tabs[0]:
        with st.form("add_product", clear_on_submit=True):
            a, b = st.columns(2)
            name = a.text_input("Product name", placeholder="e.g. Bottled water 500 ml")
            category = b.text_input("Category", "General")
            cost = a.number_input("Unit cost (PHP)", 0.0, value=10.0, step=0.5, format="%.2f")
            price = b.number_input("Selling price (PHP)", 0.0, value=15.0, step=0.5, format="%.2f")
            opening = a.number_input("Opening stock", 0, value=0, step=1)
            level = b.number_input("Low-stock threshold", 0, value=10, step=1)
            st.caption("Opening stock is recorded as a movement. Cost and price can change later without rewriting past receipts.")
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
            st.caption(f"Available now: **{int(row.stock_qty):,} units** · Alert at **{int(row.reorder_level):,} units**")
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
                st.dataframe(
                    inventory.ledger(path, row.id),
                    hide_index=True,
                    width="stretch",
                    column_config={"quantity_delta": st.column_config.NumberColumn("Units", format="%+d")},
                )

    with tabs[2]:
        row = choose_product(path, "edit_product", active=False)
        if row is not None:
            with st.form(f"edit_{row.id}"):
                a, b = st.columns(2)
                name = a.text_input("Name", row["name"])
                category = b.text_input("Product category", row.category)
                cost = a.number_input("Current unit cost (PHP)", 0.0, value=float(row.cost_centavos / 100), step=0.5, format="%.2f")
                price = b.number_input("Current selling price (PHP)", 0.0, value=float(row.price_centavos / 100), step=0.5, format="%.2f")
                level = a.number_input("Reorder threshold", 0, value=int(row.reorder_level), step=1)
                active_flag = b.checkbox("Active product", bool(row.active))
                st.caption("Archiving preserves sales history. Price changes affect future sales only; existing receipts keep their original amounts.")
                if st.form_submit_button("Save product", type="primary"):
                    try:
                        inventory.edit_product(path, row.id, name, category, cost, price, level, active_flag)
                        st.session_state.product_flash = "Product updated."
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

    with tabs[3]:
        ui.section("Completed daily history", "Feeds the ML pages")
        st.write(
            "These observations feed the ML pages. Importing history does not create sales receipts or change current stock."
        )
        hist = history(path)
        if hist.empty:
            ui.empty_state("No completed history yet", "Finalize a selling day below, or import a CSV of completed observations.")
        else:
            st.dataframe(hist.tail(60), hide_index=True, width="stretch", height=300)
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
            st.write(
                "Confirm that all sales were recorded, including genuine zero-sales days. Existing observations are preserved. "
                "Flag products whose sales were limited by unavailable stock."
            )
            day = st.date_input("Completed date", today() - timedelta(days=1), max_value=today() - timedelta(days=1))
            active_items = active
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

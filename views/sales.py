import uuid

import pandas as pd
import streamlit as st

from core.inventory import record_sale, sales
from views import ui
from views.common import choose_product


def _receipt(receipt, saved=False):
    state = "saved" if saved else "preview"
    return (
        f'<div class="ms-receipt{" ms-receipt--saved" if saved else ""}">'
        f'<div class="ms-receipt-head">'
        f'<span class="ms-receipt-kicker">{"Saved receipt" if saved else "Receipt preview"}</span>'
        f'{ui.chip("Saved", "good") if saved else ui.chip("Not saved yet", "neutral")}'
        f"</div>"
        f'<div class="ms-receipt-line"><span>Product</span><strong>{ui.esc(receipt["product"])}</strong></div>'
        f'<div class="ms-receipt-line"><span>Unit price</span><strong>PHP {receipt["unit_price"]:,.2f}</strong></div>'
        f'<div class="ms-receipt-line"><span>Quantity</span><strong>{receipt["quantity"]:,} unit{"s" if receipt["quantity"] != 1 else ""}</strong></div>'
        f'<div class="ms-receipt-total"><span>Total</span><strong>PHP {receipt["total"]:,.2f}</strong></div>'
        f'<div class="ms-receipt-foot">Stock after this sale: {receipt["after"]:,} units. '
        f'The stored unit price is used for this receipt.</div>'
        f"</div>"
    )


def render(path):
    ui.page_header(
        "Record Sales",
        "Record a sale",
        "Stock is deducted only after a valid sale is saved. Overselling is rejected.",
    )
    done_key = "sale_done_" + path.stem
    token_key = "sale_token_" + path.stem

    if done_key in st.session_state:
        receipt = st.session_state[done_key]
        with st.container(border=True):
            st.success(receipt["message"])
            st.markdown(_receipt(receipt, saved=True), unsafe_allow_html=True)
            a, b, _ = st.columns([1, 1, 1.4], vertical_alignment="center")
            with a:
                if st.button("Start another sale", type="primary", key="sale_again_" + path.stem, width="stretch"):
                    del st.session_state[done_key]
                    st.session_state[token_key] = str(uuid.uuid4())
                    st.rerun()
            with b:
                ui.nav_button("Back to overview", "Dashboard", key="sale_back_" + path.stem, width="stretch")
    else:
        row = None
        save = False
        left, right = st.columns([1.08, 0.92], gap="large")
        with left:
            with st.container(border=True):
                ui.section("New sale", "One product at a time")
                row = choose_product(path, "sale_product_" + path.stem)
                if row is None:
                    ui.nav_button("Add a product first", "Products & Stock", kind="primary", key="sale_add_" + path.stem)
                else:
                    stock = int(row.stock_qty)
                    price = float(row.price_centavos / 100)
                    st.caption(
                        f"Available now: **{stock:,} units** · Unit price: **PHP {price:,.2f}** · "
                        f"Alert at **{int(row.reorder_level):,} units**"
                    )
                    token = st.session_state.setdefault(token_key, str(uuid.uuid4()))
                    qty = st.number_input(
                        "Quantity sold",
                        min_value=1,
                        max_value=max(1, stock),
                        value=1,
                        step=1,
                        key="sale_qty_" + path.stem,
                        disabled=stock == 0,
                    )
                    st.caption("A positive whole number. Overselling is rejected, and the receipt keeps its stored price.")
                    save = st.button(
                        "Save sale",
                        type="primary",
                        disabled=stock == 0,
                        key="sale_save_" + path.stem,
                    )
                    if stock == 0:
                        ui.note(
                            "Out of stock",
                            "Receive stock for this product before recording a sale.",
                            "warn",
                        )
        with right:
            if row is not None:
                preview = {
                    "product": row["name"],
                    "unit_price": price,
                    "quantity": qty,
                    "total": qty * price,
                    "after": stock - qty,
                }
                st.markdown(_receipt(preview), unsafe_allow_html=True)
                st.caption("Saving deducts stock and writes the receipt in one transaction.")
                if stock - qty <= int(row.reorder_level):
                    st.caption("After this sale the product will be at or below its low-stock threshold.")
                ui.note(
                    "What gets saved",
                    "A sale record, a stock movement, and this receipt are written together. A rejected sale changes nothing.",
                )
        if save and row is not None:
            try:
                sid, created = record_sale(path, row.id, qty, token)
                if created:
                    message = (
                        f"Sale #{sid} saved: {qty} × {row['name']} · PHP {qty * price:,.2f}. "
                        f"Stock remaining: {stock - qty}."
                    )
                else:
                    message = f"Sale #{sid} was already saved; no duplicate was created."
                st.session_state[done_key] = {
                    "message": message,
                    "product": row["name"],
                    "unit_price": price,
                    "quantity": qty,
                    "total": qty * price,
                    "after": stock - qty,
                }
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    ui.section("Recent receipts", "Newest first", spaced=True)
    recent = sales(path).head(15)
    if recent.empty:
        ui.empty_state(
            "No sales yet",
            "The first saved sale will appear here with its stored unit price and revenue.",
            "Record Sales → Save sale",
        )
    else:
        recent = recent.copy()
        recent["recorded"] = pd.to_datetime(recent.occurred_at).dt.strftime("%d %b %Y · %H:%M")
        st.dataframe(
            recent[["id", "product", "quantity", "unit_price_php", "revenue_php", "recorded"]],
            hide_index=True,
            width="stretch",
            height=min(360, 56 + 35 * len(recent)),
            column_config={
                "id": st.column_config.NumberColumn("Receipt", width="small"),
                "product": st.column_config.TextColumn("Product", width="medium"),
                "quantity": st.column_config.NumberColumn("Units", format="%d", width="small"),
                "unit_price_php": st.column_config.NumberColumn("Unit price (PHP)", format="%.2f", width="small"),
                "revenue_php": st.column_config.NumberColumn("Revenue (PHP)", format="%.2f", width="small"),
                "recorded": st.column_config.TextColumn("Recorded"),
            },
        )

import uuid
import streamlit as st
from core.inventory import record_sale, sales
from views.common import choose_product


def render(path):
    st.title("Record a sale")
    st.write("Stock is deducted only after a valid sale is saved.")
    done_key = "sale_done_"+path.stem
    token_key = "sale_token_"+path.stem
    if done_key in st.session_state:
        receipt = st.session_state[done_key]
        st.success(receipt)
        if st.button("Start another sale", type="primary"):
            del st.session_state[done_key]
            st.session_state[token_key] = str(uuid.uuid4())
            st.rerun()
    else:
        row = choose_product(path, "sale_product_"+path.stem)
        if row is not None:
            a, b, c = st.columns(3)
            a.metric("Available units", int(row.stock_qty))
            b.metric("Unit price", f"PHP {row.price_centavos/100:,.2f}")
            c.metric("Low-stock threshold", int(row.reorder_level))
            token = st.session_state.setdefault(token_key, str(uuid.uuid4()))
            with st.form("sale_form"):
                qty = st.number_input("Quantity sold", 1, value=1, step=1)
                st.caption("The stored unit price is used for this receipt. Overselling is rejected.")
                submitted = st.form_submit_button("Save sale", type="primary", disabled=int(row.stock_qty)==0)
            if submitted:
                try:
                    sid, created = record_sale(path, row.id, qty, token)
                    st.session_state[done_key] = f"Sale #{sid} saved: {qty} × {row['name']} · PHP {qty*row.price_centavos/100:,.2f}. Stock remaining: {int(row.stock_qty)-qty}." if created else f"Sale #{sid} was already saved; no duplicate was created."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            if int(row.stock_qty) == 0:
                st.info("This product is out of stock. Record a stock receipt first.")
    st.subheader("Recent receipts")
    st.dataframe(sales(path).head(15)[["id", "product", "quantity", "unit_price_php", "revenue_php", "occurred_at"]], hide_index=True, width="stretch")

from datetime import timedelta

import plotly.express as px
import streamlit as st

from core.database import today
from core.inventory import products, sales
from views import ui
from views.common import chart, download_csv

PERIODS = {"7 days": 7, "30 days": 30, "90 days": 90, "Custom": None}


def _change(current, previous):
    if previous > 0:
        change = (current - previous) / previous * 100
        arrow, word = ("▲", "up") if change >= 0 else ("▼", "down")
        return f'<span class="{word}">{arrow} {abs(change):.1f}%</span>'
    return ""


def render(path):
    ui.page_header(
        "Overview",
        "Your store, at a glance",
        "What sold, what is running low, and what needs attention next.",
    )
    items, transactions = products(path, True), sales(path)

    left, right = st.columns([1.7, 1], vertical_alignment="bottom")
    with left:
        ui.section("Period")
        choice = st.segmented_control(
            "Sales period",
            list(PERIODS),
            default="30 days",
            key="dash_period",
            label_visibility="collapsed",
        )
    with right:
        ui.nav_button("Record a sale", "Record Sales", kind="primary", key="dash_quick_sale")

    choice = choice or "30 days"
    if choice == "Custom":
        dates = st.date_input(
            "Custom period",
            (today() - timedelta(days=29), today()),
            max_value=today(),
            key="dash_custom",
        )
        if len(dates) != 2:
            ui.note("Pick both dates", "Choose a start and an end date to see the period.")
            return
        start, end = dates
        days = (end - start).days + 1
        previous_end, previous_start = start - timedelta(days=1), start - timedelta(days=days)
    else:
        days = PERIODS[choice]
        end = today()
        start = end - timedelta(days=days - 1)
        previous_end, previous_start = start - timedelta(days=1), start - timedelta(days=days)

    start, end = str(start), str(end)
    period = transactions[transactions.date.between(start, end)] if not transactions.empty else transactions
    previous = (
        transactions[transactions.date.between(str(previous_start), str(previous_end))]
        if not transactions.empty
        else transactions
    )

    revenue = float(period.revenue_php.sum()) if not period.empty else 0.0
    previous_revenue = float(previous.revenue_php.sum()) if not previous.empty else 0.0
    units = int(period.quantity.sum()) if not period.empty else 0
    receipts = len(period)
    low = items[items.stock_qty <= items.reorder_level] if not items.empty else items
    out_of_stock = int((low.stock_qty == 0).sum()) if not low.empty else 0
    inventory_value = float((items.stock_qty * items.cost_centavos).sum()) / 100 if not items.empty else 0.0
    inventory_units = int(items.stock_qty.sum()) if not items.empty else 0

    if previous_revenue > 0:
        revenue_sub = f"{_change(revenue, previous_revenue)} vs previous {days} days"
    elif revenue > 0:
        revenue_sub = "No prior-period revenue to compare"
    else:
        revenue_sub = "No revenue in this period"

    ui.stat_row(
        [
            {
                "label": "Sales revenue",
                "prefix": "PHP",
                "value": f"{revenue:,.2f}",
                "sub": revenue_sub,
                "tone": "accent",
            },
            {
                "label": "Units sold",
                "value": f"{units:,}",
                "sub": f"{receipts:,} receipts · {units / receipts:.1f} units per sale" if receipts else "No sales recorded yet",
                "tone": "neutral",
            },
            {
                "label": "Need restocking",
                "value": f"{len(low):,}",
                "sub": (
                    "No products yet"
                    if items.empty
                    else f"{len(items):,} active products · {out_of_stock:,} out of stock"
                    if len(low)
                    else "All products above threshold"
                ),
                "tone": "neutral" if items.empty else "warn" if len(low) else "good",
            },
            {
                "label": "Inventory at cost",
                "prefix": "PHP",
                "value": f"{inventory_value:,.2f}",
                "sub": f"{inventory_units:,} units · current unit cost",
                "tone": "neutral",
            },
        ]
    )
    st.caption(
        "Revenue follows the selected period. Inventory is the current active-product balance, valued at the current unit cost."
    )

    chart_col, alert_col = st.columns([1.65, 1], gap="large")
    with chart_col:
        with st.container(border=True):
            ui.section("Sales over time", f"{start} → {end}")
            if period.empty:
                ui.empty_state(
                    "No sales in this range",
                    "Record a sale, or widen the period to see revenue move."
                    if not items.empty
                    else "Add your first product, then record a sale to start the history.",
                    "Record Sales → Save sale" if not items.empty else "Products & Stock → Add product",
                )
            else:
                grouped = period.groupby("date", as_index=False).revenue_php.sum().sort_values("date")
                average = grouped.revenue_php.mean()
                fig = px.bar(
                    grouped,
                    x="date",
                    y="revenue_php",
                    labels={"date": "Date", "revenue_php": "Revenue (PHP)"},
                )
                fig.update_traces(
                    marker_color=ui.TEAL,
                    marker_line_width=0,
                    hovertemplate="%{x|%d %b %Y}<br>PHP %{y:,.2f}<extra></extra>",
                )
                fig.add_hline(y=average, line_dash="dot", line_width=1, line_color="#B08A45")
                fig.update_layout(height=300, showlegend=False, xaxis_title=None, yaxis_title=None, bargap=0.45)
                fig.update_yaxes(tickprefix="PHP ", tickformat=",.0f", rangemode="tozero")
                chart(fig, key="dash_sales_chart")
                st.caption(f"Dashed line marks the daily average, PHP {average:,.0f}.")

    with alert_col:
        with st.container(border=True):
            ui.section("Stock to watch", f"{len(low):,} of {len(items):,} products")
            if items.empty:
                ui.empty_state(
                    "No products yet",
                    "Add your first product to start tracking stock and low-stock alerts.",
                    "Products & Stock → Add product",
                )
            elif low.empty:
                st.markdown('<div class="ms-alert-empty">All active products are above their threshold.</div>',
                            unsafe_allow_html=True)
                st.caption("Alerts are threshold rules, not predictions. Demand forecasts live on their own page.")
            else:
                rows = []
                for row in low.sort_values(["stock_qty", "name"]).head(5).itertuples():
                    ratio = min(row.stock_qty / max(row.reorder_level, 1), 1.0)
                    tone = "bad" if row.stock_qty == 0 else "warn"
                    rows.append(
                        f'<div class="ms-alert-row">'
                        f'<div class="ms-alert-top"><div>'
                        f'<div class="ms-alert-name">{ui.esc(row.name)}</div>'
                        f'<div class="ms-alert-meta">{ui.esc(row.category)} · alert at {int(row.reorder_level)}</div>'
                        f'</div><div class="ms-alert-qty">{int(row.stock_qty)} units</div></div>'
                        f'<div class="ms-meter ms-meter--{tone}"><i style="width:{ratio * 100:.0f}%"></i></div>'
                        f"</div>"
                    )
                st.markdown(f'<div class="ms-alert">{"".join(rows)}</div>', unsafe_allow_html=True)
                if len(low) > 5:
                    st.caption(f"{len(low) - 5} more below threshold.")
                st.caption("Alerts are threshold rules, not predictions.")
            ui.nav_button(
                "Add a product" if items.empty else "Review products & stock",
                "Products & Stock",
                kind="primary" if items.empty else "secondary",
                key="dash_review_stock",
            )

    ui.section("Sales records", f"{receipts:,} receipts in this period", spaced=True)
    if period.empty:
        ui.empty_state(
            "No receipts to show",
            "Sales recorded in the selected period will appear here with their stored unit price."
            if not items.empty
            else "Add a product, then record a sale. Receipts keep their stored unit price.",
            "Record Sales → Save sale" if not items.empty else "Products & Stock → Add product",
        )
    else:
        table = period[["id", "product", "quantity", "unit_price_php", "revenue_php", "date"]]
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            height=min(360, 56 + 35 * len(table)),
            column_config={
                "id": st.column_config.NumberColumn("Receipt", width="small"),
                "product": st.column_config.TextColumn("Product", width="medium"),
                "quantity": st.column_config.NumberColumn("Units", format="%d", width="small"),
                "unit_price_php": st.column_config.NumberColumn("Unit price (PHP)", format="%.2f", width="small"),
                "revenue_php": st.column_config.NumberColumn("Revenue (PHP)", format="%.2f", width="small"),
                "date": st.column_config.TextColumn("Date"),
            },
        )
        download_csv(period, "Export sales CSV", "sales-summary.csv")

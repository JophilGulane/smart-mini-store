from datetime import datetime

import streamlit as st
import plotly.express as px

from core.inventory import products
from views import ui

COLORS = [ui.TEAL, "#D08A2C", "#5B6FB0", "#537C96"]


def chart(fig, key=None):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif", size=12, color="#365455"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=14, t=18, b=14),
        colorway=COLORS,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11), title_text=""),
        hoverlabel=dict(bgcolor="#102B2C", bordercolor="#102B2C", font=dict(color="#F2F7F6", size=12)),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#DEE8E8", tickfont=dict(size=11), title_font=dict(size=11)),
        yaxis=dict(gridcolor="#EAF0F0", zeroline=False, linecolor="rgba(0,0,0,0)", tickfont=dict(size=11), title_font=dict(size=11)),
    )
    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        theme=None,
        config={"displayModeBar": False, "displaylogo": False},
    )


def choose_product(path, key, active=True):
    frame = products(path, active_only=active)
    if frame.empty:
        ui.empty_state(
            "No products yet",
            "Add a product in Products & Stock before recording stock or sales.",
            "Products & Stock → Add product",
        )
        return None
    names = dict(zip(frame.id, frame.name))
    selected = st.selectbox("Product", frame.id.tolist(), format_func=lambda x: names[x], key=key)
    return frame.loc[frame.id.eq(selected)].iloc[0]


def provenance(metadata):
    if metadata:
        try:
            stamp = datetime.fromisoformat(str(metadata["trained_at"])).strftime("%d %b %Y · %H:%M")
        except ValueError:
            stamp = metadata["trained_at"]
        st.caption(f"Saved training run · {stamp} · observations through {metadata['data_cutoff']}")


def download_csv(frame, label, name, key=None):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8-sig"), file_name=name, mime="text/csv", key=key)

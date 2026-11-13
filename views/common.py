import streamlit as st
import plotly.express as px
from core.inventory import products

COLORS = ["#087F75", "#D38B30", "#6366B0", "#537C96"]


def chart(fig, key=None):
    fig.update_layout(template="plotly_white", font_family="Arial", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=12, r=12, t=30, b=20),
                      colorway=COLORS, legend_title_text="")
    st.plotly_chart(fig, width="stretch", key=key)


def choose_product(path, key, active=True):
    frame = products(path, active_only=active)
    if frame.empty:
        st.info("Add a product in Products & Stock to get started.")
        return None
    names = dict(zip(frame.id, frame.name))
    selected = st.selectbox("Product", frame.id.tolist(), format_func=lambda x: names[x], key=key)
    return frame.loc[frame.id.eq(selected)].iloc[0]


def provenance(metadata):
    if metadata:
        st.caption(f"Saved training run · {metadata['trained_at']} · observations through {metadata['data_cutoff']}")


def download_csv(frame, label, name, key=None):
    st.download_button(label, frame.to_csv(index=False).encode("utf-8-sig"), file_name=name, mime="text/csv", key=key)

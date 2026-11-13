"""Presentation layer: design tokens, the global stylesheet, and shared UI primitives.

All six screens build their interface from this module so spacing, type, color,
and states stay consistent. Business logic never lives here.
"""
import html

import streamlit as st

UI_FONT = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
MONO_FONT = '"SFMono-Regular", "Cascadia Mono", "Roboto Mono", Consolas, monospace'

TEAL = "#0B6E66"
TEAL_DEEP = "#07524C"
AMBER = "#8A5A10"
RED = "#9C3B32"
GREEN = "#1D6B4F"


def esc(value):
    return html.escape(str(value))


def install_theme():
    st.markdown(f"<style>{STYLESHEET}</style>", unsafe_allow_html=True)


def context_bar(items, tone="teal"):
    """A thin app-wide status strip: workspace, data source, business date."""
    parts = []
    for index, item in enumerate(items):
        if index:
            parts.append('<span class="ms-sep"></span>')
        parts.append(f"<span>{esc(item)}</span>")
    st.markdown(
        f'<div class="ms-context"><span class="ms-dot ms-dot--{esc(tone)}"></span>{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def page_header(kicker, title, subtitle):
    st.markdown(
        f'<header class="ms-head">'
        f'<div class="ms-kicker">{esc(kicker)}</div>'
        f'<h1 class="ms-title">{esc(title)}</h1>'
        f'<p class="ms-sub">{esc(subtitle)}</p>'
        f"</header>",
        unsafe_allow_html=True,
    )


def section(title, caption="", spaced=False):
    cap = f'<span class="ms-section-cap">{esc(caption)}</span>' if caption else ""
    spacing = " ms-section--spaced" if spaced else ""
    st.markdown(f'<div class="ms-section{spacing}"><span class="ms-section-title">{esc(title)}</span>{cap}</div>',
                unsafe_allow_html=True)


def chip(label, tone="neutral"):
    return f'<span class="ms-chip ms-chip--{esc(tone)}">{esc(label)}</span>'


def stat_card(label, value, sub="", tone="neutral", prefix=""):
    pre = f'<span class="cur">{esc(prefix)}</span>' if prefix else ""
    sub_html = f'<div class="ms-stat-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="ms-stat ms-stat--{esc(tone)}">'
        f'<div class="ms-stat-label">{esc(label)}</div>'
        f'<div class="ms-stat-value">{pre}{value}</div>'
        f"{sub_html}"
        f"</div>"
    )


def stat_row(cards):
    inner = "".join(stat_card(**card) for card in cards)
    st.markdown(
        f'<div class="ms-stat-grid" style="--n:{len(cards)}">{inner}</div>',
        unsafe_allow_html=True,
    )


def note(title, body, tone="info"):
    st.markdown(
        f'<div class="ms-note ms-note--{esc(tone)}">'
        f'<div class="ms-note-title">{esc(title)}</div>'
        f'<div class="ms-note-body">{esc(body)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def empty_state(title, body, hint=""):
    hint_html = f'<div class="ms-empty-hint">{esc(hint)}</div>' if hint else ""
    st.markdown(
        f'<div class="ms-empty">'
        f'<div class="ms-empty-rule"></div>'
        f'<div class="ms-empty-title">{esc(title)}</div>'
        f'<div class="ms-empty-body">{esc(body)}</div>'
        f"{hint_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def nav_button(label, page, kind="secondary", key=None, icon=None, width="content"):
    """A button that moves the sidebar navigation, like an in-app link."""
    def _go():
        st.session_state["nav_page"] = page

    st.button(label, type=kind, key=key, on_click=_go, icon=icon, width=width)


def money(amount):
    return f"PHP {amount:,.2f}"


STYLESHEET = f"""
:root {{
  --ms-ground: #F1F5F5;
  --ms-surface: #FFFFFF;
  --ms-surface-alt: #F7FAFA;
  --ms-ink: #102B2C;
  --ms-ink-soft: #365455;
  --ms-muted: #5C7273;
  --ms-line: #DEE8E8;
  --ms-line-soft: #EAF0F0;
  --ms-line-strong: #C9D8D8;
  --ms-teal: {TEAL};
  --ms-teal-deep: {TEAL_DEEP};
  --ms-teal-bright: #12958A;
  --ms-teal-wash: #E6F3F1;
  --ms-amber: {AMBER};
  --ms-amber-wash: #FAF0DF;
  --ms-red: {RED};
  --ms-red-wash: #FAEAE8;
  --ms-green: {GREEN};
  --ms-green-wash: #E7F3EC;
  --ms-radius: 14px;
  --ms-shadow: 0 1px 0 rgba(16, 43, 44, .04), 0 18px 36px -28px rgba(16, 43, 44, .45);
  --ms-ui: {UI_FONT};
  --ms-mono: {MONO_FONT};
}}

html, body, .stApp {{
  font-family: var(--ms-ui);
  color: var(--ms-ink);
}}
.stApp {{
  background:
    radial-gradient(1100px 360px at 72% -8%, rgba(11, 110, 102, .07), transparent 62%),
    var(--ms-ground);
}}
::selection {{ background: rgba(18, 149, 138, .22); }}
* {{ scrollbar-width: thin; scrollbar-color: #B9CBCB transparent; }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-thumb {{ background: #C4D4D4; border: 3px solid var(--ms-ground); border-radius: 999px; }}

[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ background: transparent; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stToolbar"] [data-testid="stStatusWidget"] {{ display: none; }}
[data-testid="stMainBlockContainer"] {{
  max-width: 1240px;
  padding: 1.9rem 2.6rem 4rem;
}}
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 {{
  letter-spacing: -.02em;
  color: var(--ms-ink);
}}
h2 {{ font-size: 1.15rem; font-weight: 620; margin: 1.5rem 0 .55rem; }}
h3 {{ font-size: .98rem; font-weight: 600; margin: 1.2rem 0 .4rem; }}
p, li {{ line-height: 1.6; }}

/* ---------- Sidebar shell ---------- */
[data-testid="stSidebar"] {{
  background: #0E2528;
  border-right: 1px solid #0A1D1F;
}}
[data-testid="stSidebarContent"] {{ padding-top: .35rem; }}
[data-testid="stSidebarUserContent"] {{ padding: .4rem 1.15rem 1.4rem; }}
[data-testid="stSidebarHeader"] {{ padding: .55rem .9rem 0; }}
[data-testid="stSidebarCollapseButton"] span {{ color: #8FB5B0 !important; }}

.ms-brand {{ display: flex; align-items: center; gap: 11px; padding: .25rem 0 1.1rem; }}
.ms-mark {{
  width: 36px; height: 36px; border-radius: 10px;
  display: grid; place-items: center;
  background: #2BB3A3; color: #06211F;
  font-family: var(--ms-mono); font-size: 12px; font-weight: 700;
  letter-spacing: -.06em;
  box-shadow: inset 0 -8px 14px rgba(6, 33, 31, .18);
}}
.ms-word {{ font-size: 15.5px; font-weight: 640; color: #F1F7F6; letter-spacing: -.01em; line-height: 1.2; }}
.ms-word-sub {{ font-size: 11px; color: #8FB5B0; margin-top: 3px; letter-spacing: .02em; }}

.ms-nav-label {{
  font-family: var(--ms-mono); font-size: 9.5px; letter-spacing: .16em;
  text-transform: uppercase; color: #7FA5A1;
  margin: .35rem 0 .35rem;
}}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
  font-family: var(--ms-mono); font-size: 9.5px; letter-spacing: .14em;
  text-transform: uppercase; color: #7FA5A1;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[role="group"] {{
  background: rgba(255, 255, 255, .06);
  border: 1px solid rgba(255, 255, 255, .16);
  border-radius: 9px;
  min-height: 38px;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[role="group"]:hover {{ border-color: rgba(43, 179, 163, .55); }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] input {{
  color: #EDF5F4 !important; font-size: 13px; font-weight: 500;
  background: transparent !important;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] button {{ color: #9BBAB6; }}
[data-testid="stSidebar"] [data-testid="stSelectbox"] svg {{ color: #9BBAB6; }}

.ms-ws-note {{
  display: flex; gap: 7px; align-items: flex-start;
  margin: .55rem 0 .1rem;
  font-size: 10.5px; line-height: 1.45; color: #8FB5B0;
}}
.ms-ws-note::before {{
  content: ""; flex: 0 0 auto; width: 5px; height: 5px; border-radius: 50%;
  background: #2BB3A3; margin-top: 5px;
}}

[data-testid="stSidebar"] [data-testid="stRadioGroup"] {{ gap: 2px; }}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div {{ border-radius: 8px; }}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(2),
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:nth-child(4) {{ margin-top: 15px; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] {{
  padding: 7px 10px; border-radius: 8px; width: 100%;
  transition: background .14s ease;
}}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div {{ gap: 0; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:first-child {{ display: none; }}
[data-testid="stSidebar"] [data-testid="stRadioOption"] p {{
  color: #B9CFCC; font-size: 13.5px; font-weight: 450; letter-spacing: .005em;
}}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div:hover {{ background: rgba(255, 255, 255, .055); }}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"] {{
  background: rgba(43, 179, 163, .15);
  box-shadow: inset 2px 0 0 #2BB3A3;
}}
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div[data-selected="true"] p {{
  color: #FFFFFF; font-weight: 620;
}}

.ms-foot {{
  margin-top: 1.1rem; padding-top: .85rem;
  border-top: 1px solid rgba(255, 255, 255, .1);
  font-family: var(--ms-mono); font-size: 10px; letter-spacing: .04em;
  color: #7FA5A1; line-height: 1.7;
}}
.ms-foot strong {{ color: #D7E6E3; font-weight: 600; display: block; font-size: 11px; letter-spacing: .02em; }}

[data-testid="stSidebar"] [data-testid="stExpander"] details {{
  background: rgba(255, 255, 255, .04);
  border: 1px solid rgba(255, 255, 255, .1);
  border-radius: 9px;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{ padding: 9px 11px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{ color: #B9CFCC; font-size: 11.5px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] p,
[data-testid="stSidebar"] [data-testid="stExpander"] li {{ color: #9FBAB7; font-size: 11.5px; line-height: 1.55; }}
[data-testid="stSidebar"] [data-testid="stExpander"] {{
  margin-top: 10px;
}}

/* ---------- Typographic chrome ---------- */
.ms-context {{
  display: flex; flex-wrap: wrap; align-items: center; gap: 9px;
  padding-bottom: 15px; margin-bottom: 24px;
  border-bottom: 1px solid var(--ms-line-soft);
  font-family: var(--ms-mono); font-size: 10.5px; letter-spacing: .085em;
  text-transform: uppercase; color: #556B6C;
}}
.ms-context .ms-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--ms-teal); box-shadow: 0 0 0 3px var(--ms-teal-wash); margin-right: 2px; }}
.ms-context .ms-dot--amber {{ background: var(--ms-amber); box-shadow: 0 0 0 3px var(--ms-amber-wash); }}
.ms-sep {{ width: 1px; height: 11px; background: var(--ms-line); }}

.ms-head {{ padding: 0 0 20px; }}
.ms-kicker {{
  display: flex; align-items: center; gap: 9px;
  font-family: var(--ms-mono); font-size: 10px; letter-spacing: .17em;
  text-transform: uppercase; color: var(--ms-teal); font-weight: 550;
}}
.ms-kicker::before {{ content: ""; width: 20px; height: 1px; background: currentColor; opacity: .65; }}
.ms-title {{
  font-family: var(--ms-ui);
  font-size: 2.05rem; line-height: 1.1; font-weight: 640;
  letter-spacing: -.038em; color: var(--ms-ink);
  margin: .48rem 0 .55rem; text-wrap: balance;
}}
.ms-sub {{ font-size: .92rem; line-height: 1.58; color: var(--ms-muted); max-width: 68ch; margin: 0; }}

.ms-section {{
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 12px; padding: 0 0 .35rem; margin: 0;
}}
.ms-section--spaced {{ margin-top: 24px; }}
.ms-section-title {{
  font-family: var(--ms-mono); font-size: 10.5px; letter-spacing: .13em;
  text-transform: uppercase; color: var(--ms-ink-soft); font-weight: 550;
}}
.ms-section-cap {{ font-size: 11.5px; color: var(--ms-muted); text-align: right; }}

/* ---------- Cards & data ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {{
  background: var(--ms-surface);
  border: 1px solid var(--ms-line) !important;
  border-radius: var(--ms-radius);
  box-shadow: var(--ms-shadow);
}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{ padding: 1.05rem 1.15rem .55rem; }}
[data-testid="stForm"] {{
  background: var(--ms-surface);
  border: 1px solid var(--ms-line);
  border-radius: var(--ms-radius);
  box-shadow: var(--ms-shadow);
  padding: 1.15rem 1.2rem .9rem;
}}
[data-testid="stExpander"] details {{
  border: 1px solid var(--ms-line);
  border-radius: 11px;
  background: var(--ms-surface);
}}
[data-testid="stExpander"] summary {{ padding: 11px 14px; }}
[data-testid="stExpander"] summary p {{ font-size: 12.5px; font-weight: 550; color: var(--ms-ink-soft); }}
[data-testid="stExpanderDetails"] {{ padding: 0 14px 12px; }}

.ms-stat-grid {{
  display: grid; grid-template-columns: repeat(var(--n, 4), minmax(0, 1fr));
  gap: 10px; margin: 4px 0 0;
}}
.ms-stat {{
  background: var(--ms-surface); border: 1px solid var(--ms-line);
  border-radius: var(--ms-radius); padding: 14px 16px 13px;
  box-shadow: var(--ms-shadow); height: 100%; min-width: 0;
}}
.ms-stat-label {{
  display: flex; align-items: center; gap: 7px;
  font-family: var(--ms-mono); font-size: 10px; letter-spacing: .12em;
  text-transform: uppercase; color: #5C7273;
}}
.ms-stat-label::before {{ content: ""; width: 5px; height: 5px; border-radius: 50%; background: var(--ms-line-strong); }}
.ms-stat--good .ms-stat-label::before {{ background: var(--ms-green); }}
.ms-stat--warn .ms-stat-label::before {{ background: var(--ms-amber); }}
.ms-stat--bad .ms-stat-label::before {{ background: var(--ms-red); }}
.ms-stat--accent .ms-stat-label::before {{ background: var(--ms-teal); }}
.ms-stat-value {{
  font-size: 1.62rem; font-weight: 620; letter-spacing: -.035em;
  color: var(--ms-ink); margin-top: 7px; line-height: 1.15;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}}
.ms-stat-value .cur {{ font-size: .64em; font-weight: 550; color: var(--ms-muted); letter-spacing: 0; margin-right: 3px; }}
.ms-stat--good .ms-stat-value {{ color: var(--ms-green); }}
.ms-stat--warn .ms-stat-value {{ color: var(--ms-amber); }}
.ms-stat--bad .ms-stat-value {{ color: var(--ms-red); }}
.ms-stat-sub {{ font-size: 11.8px; color: #5C7273; margin-top: 4px; line-height: 1.45; }}
.ms-stat-sub .up {{ color: var(--ms-green); font-weight: 600; }}
.ms-stat-sub .down {{ color: var(--ms-red); font-weight: 600; }}

.ms-chip {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px; border-radius: 999px;
  font-family: var(--ms-mono); font-size: 9.5px; letter-spacing: .08em;
  text-transform: uppercase; white-space: nowrap;
  background: var(--ms-surface-alt); color: var(--ms-muted);
  border: 1px solid var(--ms-line);
}}
.ms-chip--good {{ background: var(--ms-green-wash); color: var(--ms-green); border-color: #CFE6D8; }}
.ms-chip--warn {{ background: var(--ms-amber-wash); color: var(--ms-amber); border-color: #EDDCC0; }}
.ms-chip--bad {{ background: var(--ms-red-wash); color: var(--ms-red); border-color: #EFD3CF; }}
.ms-chip--teal {{ background: var(--ms-teal-wash); color: var(--ms-teal-deep); border-color: #CBE6E2; }}

.ms-note {{
  border: 1px solid var(--ms-line);
  background: var(--ms-surface); border-radius: 10px;
  padding: 12px 15px; margin: 4px 0 14px;
}}
.ms-note-title {{
  display: flex; align-items: center; gap: 7px;
  font-size: 12.5px; font-weight: 620; color: var(--ms-ink);
}}
.ms-note-title::before {{
  content: ""; flex: 0 0 auto; width: 6px; height: 6px; border-radius: 50%;
  background: var(--ms-teal);
}}
.ms-note-body {{ font-size: 12px; line-height: 1.55; color: var(--ms-muted); margin-top: 3px; }}
.ms-note--warn {{ background: #FFFDF8; border-color: #EADCC2; }}
.ms-note--warn .ms-note-title::before {{ background: var(--ms-amber); }}
.ms-note--bad {{ background: #FFFBFB; border-color: #EFD3CF; }}
.ms-note--bad .ms-note-title::before {{ background: var(--ms-red); }}
.ms-note--good {{ background: #FBFEFC; border-color: #CFE6D8; }}
.ms-note--good .ms-note-title::before {{ background: var(--ms-green); }}

.ms-empty {{
  border: 1px dashed var(--ms-line-strong); border-radius: 12px;
  padding: 26px 22px; background: rgba(255, 255, 255, .55);
  margin: 4px 0 14px;
}}
.ms-empty-rule {{ width: 26px; height: 2px; background: var(--ms-teal); opacity: .55; margin-bottom: 12px; }}
.ms-empty-title {{ font-size: 14px; font-weight: 620; color: var(--ms-ink); }}
.ms-empty-body {{ font-size: 12.5px; color: var(--ms-muted); line-height: 1.55; margin-top: 3px; max-width: 58ch; }}
.ms-empty-hint {{ font-family: var(--ms-mono); font-size: 10px; letter-spacing: .07em; text-transform: uppercase; color: var(--ms-teal); margin-top: 9px; }}

/* ---------- Controls ---------- */
.stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button {{
  border-radius: 8px; border: 1px solid var(--ms-line-strong);
  background: var(--ms-surface); color: var(--ms-ink);
  font-weight: 550; font-size: 13px; padding: .4rem .95rem;
  box-shadow: 0 1px 0 rgba(16, 43, 44, .03);
  transition: background .14s ease, border-color .14s ease, transform .14s ease;
}}
.stButton button p, .stDownloadButton button p, [data-testid="stFormSubmitButton"] button p {{ color: inherit; font-size: 13px; font-weight: inherit; }}
.stButton button:hover, .stDownloadButton button:hover {{ border-color: var(--ms-teal); color: var(--ms-teal-deep); background: #F5FBFA; }}
button[kind="primary"], button[kind="primaryFormSubmit"] {{
  background: var(--ms-teal) !important; border-color: var(--ms-teal) !important; color: #FFFFFF !important;
  box-shadow: 0 1px 0 rgba(7, 82, 76, .25), 0 8px 18px -14px rgba(11, 110, 102, .9);
}}
button[kind="primary"] p, button[kind="primaryFormSubmit"] p {{ color: #FFFFFF !important; }}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
  background: var(--ms-teal-deep) !important; border-color: var(--ms-teal-deep) !important;
}}
button:focus-visible, a:focus-visible, input:focus-visible {{ outline: 2px solid var(--ms-teal-bright); outline-offset: 2px; }}
button:disabled, button:disabled p {{ color: #8A9C9C !important; }}
button:disabled {{ background: #F3F6F6 !important; border-color: var(--ms-line) !important; box-shadow: none; }}

[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {{
  background: transparent; border: 1px solid transparent; color: #5C7273;
  font-weight: 550; border-radius: 7px; box-shadow: none;
}}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"]:hover {{ background: #E8EFEF; color: var(--ms-ink); }}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"] {{
  background: var(--ms-surface) !important; border-color: var(--ms-line-strong) !important;
  color: var(--ms-ink) !important; box-shadow: 0 1px 0 rgba(16, 43, 44, .04);
}}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected="true"] p {{ color: var(--ms-ink) !important; font-weight: 600; }}

[data-testid="stWidgetLabel"] p {{ font-size: 12px; font-weight: 550; color: var(--ms-ink-soft); }}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInputField"], [data-testid="stSelectbox"] div[role="group"],
[data-testid="stMultiSelect"] div[role="group"] {{ border-radius: 8px; }}
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {{ border-color: var(--ms-teal); }}
[data-testid="stCaptionContainer"] p {{ font-size: 11.5px; line-height: 1.5; color: var(--ms-muted); }}
[data-testid="stMarkdownContainer"] p {{ color: inherit; }}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  gap: 2px; border-bottom: 1px solid var(--ms-line); background: transparent;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
  padding: 9px 14px; border-radius: 8px 8px 0 0;
  font-size: 12.5px; font-weight: 550; color: var(--ms-muted);
}}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{
  color: var(--ms-ink); background: var(--ms-surface);
  box-shadow: inset 0 -2px 0 var(--ms-teal);
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background: var(--ms-teal); }}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {{ padding-top: 14px; }}

[data-testid="stAlert"] {{ border-radius: 9px; padding: 10px 13px; }}
[data-testid="stAlert"] p {{ font-size: 12.5px; line-height: 1.5; }}
[data-testid="stDataFrame"] {{
  border: 1px solid var(--ms-line); border-radius: 11px;
  background: var(--ms-surface); font-size: 12px;
}}
[data-testid="stProgress"] > div > div {{ background: var(--ms-teal); }}
.js-plotly-plot .modebar {{ display: none !important; }}
[data-testid="stPlotlyChart"] {{ margin-top: -2px; }}

/* ---------- Domain components ---------- */
.ms-alert {{ display: flex; flex-direction: column; gap: 0; }}
.ms-alert-row {{ padding: 10px 0 7px; border-top: 1px solid var(--ms-line-soft); }}
.ms-alert-row:first-child {{ border-top: 0; padding-top: 2px; }}
.ms-alert-top {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }}
.ms-alert-name {{ font-size: 12.8px; font-weight: 600; color: var(--ms-ink); }}
.ms-alert-meta {{ font-size: 10.5px; color: var(--ms-muted); margin-top: 1px; }}
.ms-alert-qty {{ font-family: var(--ms-mono); font-size: 11px; color: var(--ms-ink-soft); white-space: nowrap; font-variant-numeric: tabular-nums; }}
.ms-meter {{ height: 4px; border-radius: 999px; background: #EEF3F3; margin-top: 7px; overflow: hidden; }}
.ms-meter i {{ display: block; height: 100%; border-radius: inherit; background: var(--ms-amber); }}
.ms-meter--bad i {{ background: var(--ms-red); }}
.ms-meter--good i {{ background: var(--ms-green); }}
.ms-alert-empty {{ display: flex; gap: 9px; align-items: center; padding: 8px 0; color: var(--ms-green); font-size: 12.5px; font-weight: 550; }}
.ms-alert-empty::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--ms-green); box-shadow: 0 0 0 3px var(--ms-green-wash); }}

.ms-receipt {{
  background: #FFFEFB;
  border: 1px solid var(--ms-line);
  border-radius: 12px;
  padding: 15px 16px 13px;
  box-shadow: var(--ms-shadow);
}}
.ms-receipt--saved {{ border-color: #CFE6D8; background: #FCFEFC; }}
.ms-receipt-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.ms-receipt-kicker {{ font-family: var(--ms-mono); font-size: 9.5px; letter-spacing: .14em; text-transform: uppercase; color: var(--ms-muted); }}
.ms-receipt-line {{ display: flex; justify-content: space-between; gap: 16px; padding: 6px 0; font-size: 12.5px; border-top: 1px dashed var(--ms-line); }}
.ms-receipt-line:first-of-type {{ border-top: 0; }}
.ms-receipt-line span {{ color: var(--ms-muted); }}
.ms-receipt-line strong {{ color: var(--ms-ink); font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; }}
.ms-receipt-total {{ display: flex; justify-content: space-between; align-items: baseline; margin-top: 9px; padding-top: 10px; border-top: 1px solid var(--ms-line); }}
.ms-receipt-total span {{ font-size: 11px; color: var(--ms-muted); text-transform: uppercase; letter-spacing: .1em; font-family: var(--ms-mono); }}
.ms-receipt-total strong {{ font-size: 1.45rem; letter-spacing: -.03em; font-weight: 620; color: var(--ms-ink); font-variant-numeric: tabular-nums; }}
.ms-receipt-foot {{ margin-top: 8px; font-size: 10.5px; color: var(--ms-muted); line-height: 1.5; }}

.ms-forecast {{
  background: linear-gradient(180deg, #FBFEFD 0%, #FFFFFF 70%);
  border: 1px solid var(--ms-line); border-radius: var(--ms-radius);
  padding: 16px 18px; box-shadow: var(--ms-shadow);
}}
.ms-forecast-top {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; }}
.ms-forecast-date {{ font-size: 12px; color: var(--ms-muted); }}
.ms-forecast-side {{ display: flex; flex-direction: column; align-items: flex-end; gap: 6px; text-align: right; }}
.ms-forecast-figure {{ font-size: 3rem; font-weight: 650; letter-spacing: -.05em; line-height: 1; color: var(--ms-teal-deep); font-variant-numeric: tabular-nums; white-space: nowrap; margin-top: 6px; }}
.ms-forecast-figure small {{ font-size: .34em; font-weight: 550; color: var(--ms-muted); letter-spacing: 0; margin-left: 3px; }}
.ms-forecast-foot {{ margin-top: 11px; padding-top: 10px; border-top: 1px solid var(--ms-line-soft); display: flex; flex-wrap: wrap; gap: 10px; align-items: center; font-size: 11.5px; color: var(--ms-muted); }}

.ms-group-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }}
.ms-group {{ border: 1px solid var(--ms-line); border-radius: 11px; padding: 11px 13px; background: var(--ms-surface-alt); }}
.ms-group-top {{ display: flex; align-items: center; gap: 7px; }}
.ms-group-dot {{ width: 7px; height: 7px; border-radius: 50%; }}
.ms-group-name {{ font-size: 12px; font-weight: 620; color: var(--ms-ink); }}
.ms-group-value {{ font-size: 1.25rem; font-weight: 620; letter-spacing: -.03em; margin-top: 6px; color: var(--ms-ink); font-variant-numeric: tabular-nums; }}
.ms-group-value small {{ font-size: .55em; color: var(--ms-muted); font-weight: 500; letter-spacing: 0; margin-left: 2px; }}
.ms-group-meta {{ font-size: 10.5px; color: var(--ms-muted); margin-top: 2px; }}

@media (max-width: 1180px) {{
  .ms-stat-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 1080px) {{
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 100%; flex: 1 1 100%; }}
}}
@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 1.4rem 1.25rem 3rem; }}
  .ms-title {{ font-size: 1.7rem; }}
  .ms-group-grid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 620px) {{
  .ms-stat-grid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 760px) {{
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 100%; flex: 1 1 100%; }}
  [data-testid="stMainBlockContainer"] {{ padding-top: 4.3rem; }}
  [data-testid="stHeader"] {{ background: rgba(241, 245, 245, .92); backdrop-filter: blur(8px); }}
  .ms-context {{ font-size: 9.5px; }}
  .ms-stat-value {{ font-size: 1.45rem; }}
  .ms-forecast-top {{ flex-wrap: wrap; }}
  .ms-forecast-side {{ align-items: flex-start; text-align: left; }}
}}
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition: none !important; animation: none !important; }}
}}
"""

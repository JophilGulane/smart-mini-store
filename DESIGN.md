---
name: Mini-Store Inventory Assistant
description: Calm data console for a classroom inventory and ML demonstration
---

## Overview

A calm, factual data console for a single-user inventory app. The interface is
laptop-first and designed to be read across a table or projected in a classroom:
strong contrast, tabular numerals, and short labels. The visual identity comes
from the deep ink sidebar, a restrained shop-green accent, and precise data
typography rather than decoration.

The normative implementation lives in `views/ui.py`; this file records the
decisions so new screens stay inside the same system.

## Colors

| Role | Value | Use |
|---|---|---|
| ground | `#F1F5F5` | App canvas, with a faint teal wash at the top |
| surface | `#FFFFFF` | Cards, tables, forms |
| surface-alt | `#F7FAFA` | Group cards, quiet fills |
| ink | `#102B2C` | Primary text |
| ink-soft | `#365455` | Section labels, secondary headings |
| muted | `#5C7273` | Captions and supporting copy (≥4.5:1 on white and ground) |
| line | `#DEE8E8` | Hairlines |
| line-strong | `#C9D8D8` | Control borders |
| primary | `#0B6E66` | Primary actions, selected navigation, forecast headline |
| primary-deep | `#07524C` | Hover, high-emphasis text |
| primary-wash | `#E6F3F1` | Selected nav background, teal chips |
| sidebar | `#0E2528` | Navigation ground |
| warn | `#8A5A10` | Low stock, caveats |
| danger | `#9C3B32` | Out of stock, rejected actions |
| success | `#1D6B4F` | Healthy stock, passing comparison |

Status tones are semantic only, each with a light wash and a visible text
label. Sidebar text uses `#B9CFCC` idle, `#FFFFFF` selected, `#8FB5B0` for
supporting copy, and `#2BB3A3` for the mark and selected rule. Tints are
derived from these roles, not new brand colors.

## Typography

- One workhorse system sans for prose and UI; one system mono for labels,
  timestamps, and dense numeric metadata.
- Section labels are 10.5px mono, uppercase, tracked `0.13em`. Micro labels
  sit at 9.5–10px; captions at 11.5–12.5px. Body copy never goes below 11.5px.
- Numbers use `font-variant-numeric: tabular-nums` so columns do not shift.
  Stat values run 1.45–1.62rem at weight ~620; the forecast hero is 3rem; the
  page title is 2.05rem at weight 640 with tracking `-0.038em`.
- Headings use balanced wrapping (`text-wrap: balance`) and never exceed 68ch
  for supporting prose.

## Layout

- 300px fixed sidebar: brand block, workspace picker, six screen links, business
  date footer, about expander.
- Main column maxes at 1240px with 2.6rem side padding. The reading order on
  every screen is: context strip → page header → statistics → work area.
- Desktop work areas are two columns (chart 1.65 : alerts 1; form 1.08 :
  receipt 0.92). Below 1080px columns become full width; below 760px the
  sidebar collapses to Streamlit's native mobile control and the header gains
  a solid blurred ground so content cannot scroll under the toggle.
- Statistics are a CSS grid: four across on wide screens, two across below
  1180px, one across below 620px. Standalone sections add 24px of space above.

## Elevation & Depth

Cards use a 1px hairline and a soft downward shadow
(`0 1px 0 rgba(16,43,44,.04), 0 18px 36px -28px rgba(16,43,44,.45)`).
The sidebar is flat. Charts sit on transparent paper. No glow, no colored halo,
no glassmorphism.

## Shapes

Radii: 7–8px controls, 9–10px inputs and small panels, 11–12px notes and
expanders, 14px cards, pills for status chips. No side-tab accent borders on
cards; notes carry a 6px semantic dot instead. Meters are 4px rounded tracks
with a filled status bar.

## Components

- **Page header** — mono kicker with a rule, a 2.05rem balanced title, and a
  68ch muted subtitle. It opens every screen.
- **Stat cards** — mono uppercase label with a tone dot, large tabular value,
  optional `PHP` prefix, and one line of context or a period delta.
- **Dataframe** — full width, hidden index, currency and count formats declared
  through `column_config`; currency is named once in the header or caption.
- **Note** — neutral panel with a semantic dot and a short title. Used for
  caveats, simulation warnings, and measured-result verdicts.
- **Empty state** — dashed panel with a short rule, title, explanation, and the
  exact next action. Never claim health or sufficiency when there is no data.
- **Receipt** — preview and saved variants share the same ruled layout; the
  saved state adds the green chip and the success banner.
- **Forecast hero** — expected units at 3rem, forecast date and stock chip on
  the right, stock context and unrounded value in the footer.
- **Charts** — Plotly, transparent paper, teal bars and lines, amber comparison
  rule, hidden modebar, legend above the plot, dates as `%d %b`.

## Do's and Don'ts

- Do keep every workflow's existing labels and behavior; presentation changes
  must not change stock, sale, or model semantics.
- Do format timestamps for humans (`13 Nov 2026 · 22:32`) and money with two
  decimals and a `PHP` prefix.
- Do state limits next to results: "trails the seven-day mean", "simulation
  only", "not classification accuracy".
- Don't introduce thick side accent borders, emoji as UI chrome, gradient
  text, or generic icon tiles.
- Don't use color alone for status; pair it with a label.
- Don't show a positive empty state ("all products above threshold") when the
  product list is empty.

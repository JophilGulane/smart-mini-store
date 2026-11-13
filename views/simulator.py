import pandas as pd
import plotly.express as px
import streamlit as st

from core.artifacts import latest_run, save_run
from core.history import history, signature
from ml.evaluation import evaluate_agent
from ml.q_learning import train_agent
from ml.restocking_env import Settings, settings_dict
from views import ui
from views.common import chart, choose_product, download_csv, provenance


def render(path):
    ui.page_header(
        "Restocking simulator",
        "Learn when to restock",
        "Reinforcement learning · Q-learning improves order decisions through simulated experience.",
    )
    ui.note(
        "Simulation only",
        "Orders here never change actual inventory. Immediate deliveries, fixed prices, and Poisson demand simplify the store environment.",
        "warn",
    )
    with st.container(border=True):
        ui.section("Simulation settings", "One week · capacity 30 units")
        row = choose_product(path, "rl_product_" + path.stem)
        if row is None:
            return
        hist = history(path, row.id)
        a, b, c = st.columns(3)
        a.write(f"Unit cost: **PHP {row.cost_centavos / 100:.2f}**")
        b.write(f"Selling price: **PHP {row.price_centavos / 100:.2f}**")
        c.write("Capacity: **30 units**")
        holding = a.number_input("Daily holding cost / unit (PHP)", min_value=0.0, value=0.5, step=0.1)
        shortage = b.number_input("Unmet demand penalty / unit (PHP)", min_value=0.0, value=3.0, step=0.5)
        episodes = c.number_input("Training weeks", min_value=100, max_value=20000, value=3000, step=100)
        st.caption(
            "Each episode starts Monday with zero inventory and ends Sunday. State: stock + weekday. Actions: order 0, 5, 10, or 15 units, subject to capacity. Leftovers carry forward and receive their cost value at the end of the week."
        )
        train = st.button("Train restocking agent", type="primary", key="rl_train_" + path.stem)

    try:
        cfg = Settings(cost=row.cost_centavos / 100, price=row.price_centavos / 100, holding=holding, shortage=shortage)
    except ValueError as exc:
        ui.note("Check the settings", str(exc), "warn")
        return

    if train:
        try:
            progress = st.progress(0.0, text="Learning from simulated weeks…")
            result = train_agent(hist, cfg, int(episodes), progress=lambda v: progress.progress(v))
            save_run(path, "q_learning", result, row.id)
            progress.empty()
            st.success(f"Trained for {episodes:,} weeks. The Q-table is saved.")
        except ValueError as exc:
            st.error(str(exc))

    result, meta = latest_run(path, "q_learning", row.id)
    if result is None:
        ui.empty_state(
            "No trained agent yet",
            "Train an agent to see learned decisions. At least 35 completed non-stockout observations are required, and selling price must exceed cost.",
            "Train restocking agent",
        )
        return
    provenance(meta)
    if result["signature"] != signature(hist, settings_dict(cfg)):
        ui.note(
            "Inputs or reward settings changed",
            "History, product economics, or reward settings differ from this run. Retrain before evaluating this agent.",
            "warn",
        )
        return

    m = result["metrics"]
    st.caption(
        f"Saved run: {m['episodes']:,} episodes · alpha {m['alpha']} · gamma {m['gamma']} · seed {m['seed']}. "
        f"Demand parameters fitted on {m['fit_start']}–{m['fit_end']} ({m['fit_rows']} rows). Changing the training-weeks control takes effect on the next training run."
    )

    with st.container(border=True):
        ui.section("Learning curve", "Mean reward over the last 100 training weeks")
        curve = result["curve"].copy()
        curve["mean_reward_100"] = curve.reward.rolling(100, min_periods=1).mean()
        fig = px.line(
            curve,
            x="episode",
            y="mean_reward_100",
            labels={"episode": "Training week", "mean_reward_100": "Mean reward (PHP)"},
            color_discrete_sequence=[ui.TEAL],
        )
        fig.update_traces(line=dict(width=2))
        fig.update_layout(height=280, showlegend=False)
        chart(fig, key="rl_curve_" + path.stem)
    st.caption("Training includes exploration. The curve can fluctuate and does not prove superiority over a simple policy.")

    ui.section("Evaluation", "Frozen policies · fresh simulated weeks", spaced=True)
    weeks_col, _ = st.columns([1, 2.2])
    weeks = weeks_col.number_input("Evaluation weeks", min_value=100, max_value=5000, value=200, step=100)
    # Evaluation is deterministic for the saved agent/settings and never updates Q.
    evaluation = evaluate_agent(result, int(weeks))
    st.caption(
        f"Frozen policies, no exploration or Q updates. Evaluation seed {evaluation['seed']} differs from training. "
        f"All policies receive identical demand weeks and zero opening stock. Fixed order: {evaluation['fixed_order']} units/day; "
        f"target-stock rule: {evaluation['target_stock']} units."
    )
    summary = evaluation["summary"]
    with st.container(border=True):
        ui.section("Average weekly reward", "Error bars show one standard error")
        fig = px.bar(
            summary,
            x="policy",
            y="mean_reward",
            error_y="reward_standard_error",
            color="policy",
            labels={"policy": "", "mean_reward": "Average weekly reward (PHP)"},
            color_discrete_map={
                "Q-learning": ui.TEAL,
                "Fixed daily order": "#B08A45",
                "Reorder to target": "#537C96",
            },
        )
        fig.update_traces(marker_line_width=0)
        fig.update_layout(height=300, showlegend=False)
        chart(fig, key="rl_eval_" + path.stem)
    st.caption(
        "Reward includes the unmet-demand penalty; inventory-adjusted profit excludes that penalty and includes terminal stock valued at cost."
    )

    learned = float(summary.loc[summary.policy.eq("Q-learning"), "mean_reward"].iloc[0])
    baseline = float(summary.loc[summary.policy.ne("Q-learning"), "mean_reward"].max())
    difference = learned - baseline
    comparison = (
        f"earns PHP {difference:,.2f} more per week than the stronger simple rule"
        if difference >= 0
        else f"earns PHP {abs(difference):,.2f} less per week than the stronger simple rule"
    )
    ui.note(
        "Measured on fresh simulated weeks",
        f"The learned policy {comparison}. This comparison applies to the fitted simulator, not a real store.",
        "good" if difference > 0 else "warn",
    )
    display = summary[["policy", "mean_reward", "mean_inventory_adjusted_profit", "mean_unmet_units", "mean_leftover"]]
    st.dataframe(
        display.round(2),
        hide_index=True,
        width="stretch",
        column_config={
            "policy": st.column_config.TextColumn("Policy", width="medium"),
            "mean_reward": st.column_config.NumberColumn("Mean reward (PHP)", format="%.2f"),
            "mean_inventory_adjusted_profit": st.column_config.NumberColumn("Inventory profit (PHP)", format="%.2f"),
            "mean_unmet_units": st.column_config.NumberColumn("Unmet units", format="%.1f"),
            "mean_leftover": st.column_config.NumberColumn("Leftover units", format="%.1f"),
        },
    )
    download_csv(evaluation["samples"], "Export all evaluation weeks", "restocking-evaluation.csv")

    with st.expander("Inspect one identical evaluation week", expanded=True):
        policy = st.selectbox("Policy to inspect", summary.policy.tolist())
        log = evaluation["log"].query("policy == @policy")
        log_display = log.drop(columns="policy").rename(
            columns={
                "weekday": "Day", "opening": "Opening", "order": "Ordered", "demand": "Demand",
                "sold": "Sold", "leftover": "Leftover", "unmet": "Unmet", "revenue": "Revenue",
                "purchase_cost": "Purchase", "holding_cost": "Holding", "service_penalty": "Penalty",
                "terminal_value": "Terminal value", "reward": "Reward",
            }
        )
        st.dataframe(log_display.round(2), hide_index=True, width="stretch")
        download_csv(evaluation["log"], "Export decision logs", "restocking-decision-logs.csv")

    with st.expander("Q-table, demand estimates & implementation"):
        st.dataframe(
            pd.DataFrame(
                {"weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "fitted_mean_demand": result["means"]}
            ),
            hide_index=True,
        )
        stock = st.slider("Inspect Q-values at inventory", 0, 30, 0)
        st.dataframe(
            pd.DataFrame(
                result["q"][stock],
                index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                columns=[f"Order {q}" for q in cfg.actions],
            )
        )
        st.caption(
            "Actions exceeding capacity are masked even though the table has entries for them. Unvisited state-action entries can remain zero."
        )
        st.code(
            "target = reward\n"
            "if not terminal:\n"
            "    target += gamma * max(q[next_state[0], next_state[1], i] for i in valid_next)\n"
            "q[state[0], state[1], action] += alpha * (target-q[state[0], state[1], action])",
            language="python",
        )
        st.write(
            "Weekday means estimate a Poisson demand distribution from earlier history. Future demand is sampled and revealed after the decision. "
            "New random weeks test policies within that assumed distribution; they do not validate real-world demand. "
            "Reward = revenue − purchase cost − holding cost − service penalty + terminal stock value."
        )

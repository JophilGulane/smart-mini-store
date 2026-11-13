import pandas as pd
import streamlit as st
import plotly.express as px
from core.history import history, signature
from core.artifacts import latest_run, save_run
from ml.restocking_env import Settings, settings_dict
from ml.q_learning import train_agent
from ml.evaluation import evaluate_agent
from views.common import choose_product, provenance, chart, download_csv


def render(path):
    st.title("Learn when to restock")
    st.write("Reinforcement learning · Q-learning improves order decisions through simulated experience.")
    st.info("Simulation only. Orders here never change actual inventory. Immediate deliveries, fixed prices and Poisson demand simplify the store environment.")
    row = choose_product(path, "rl_product_"+path.stem)
    if row is None:
        return
    hist = history(path, row.id)
    with st.expander("Simulation settings", expanded=True):
        a, b, c = st.columns(3)
        a.write(f"Unit cost: **PHP {row.cost_centavos/100:.2f}**")
        b.write(f"Selling price: **PHP {row.price_centavos/100:.2f}**")
        c.write("Capacity: **30 units**")
        holding = a.number_input("Daily holding cost / unit (PHP)", min_value=0.0, value=0.5, step=0.1)
        shortage = b.number_input("Unmet demand penalty / unit (PHP)", min_value=0.0, value=3.0, step=0.5)
        episodes = c.number_input("Training weeks", min_value=100, max_value=20000, value=3000, step=100)
        st.caption("Each episode starts Monday with zero inventory and ends Sunday. State: stock + weekday. Actions: order 0, 5, 10 or 15 units, subject to capacity. Leftovers carry forward and receive their cost value at the end of the week.")
    try:
        cfg = Settings(cost=row.cost_centavos/100, price=row.price_centavos/100, holding=holding, shortage=shortage)
    except ValueError as exc:
        st.info(str(exc))
        return
    if st.button("Train restocking agent", type="primary"):
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
        st.info("Train an agent to see learned decisions. At least 35 completed non-stockout observations are required.")
        return
    provenance(meta)
    if result["signature"] != signature(hist, settings_dict(cfg)):
        st.warning("History, product economics or reward settings have changed. Retrain before evaluating this agent.")
        return
    m = result["metrics"]
    st.caption(f"Saved run: {m['episodes']:,} episodes · alpha {m['alpha']} · gamma {m['gamma']} · seed {m['seed']}. Demand parameters fitted on {m['fit_start']}–{m['fit_end']} ({m['fit_rows']} rows). Changing the training-weeks control takes effect on the next training run.")
    curve = result["curve"].copy()
    curve["mean_reward_100"] = curve.reward.rolling(100, min_periods=1).mean()
    chart(px.line(curve, x="episode", y="mean_reward_100", labels={"episode": "Training week", "mean_reward_100": "Mean reward over last 100 weeks (PHP)"}))
    st.caption("Training includes exploration. The curve can fluctuate and does not prove superiority over a simple policy.")
    st.subheader("Compare on fresh simulated weeks")
    weeks = st.number_input("Evaluation weeks", min_value=100, max_value=5000, value=200, step=100)
    # Evaluation is deterministic for the saved agent/settings and never updates Q.
    evaluation = evaluate_agent(result, int(weeks))
    st.caption(f"Frozen policies, no exploration or Q updates. Evaluation seed {evaluation['seed']} differs from training. All policies receive identical demand weeks and zero opening stock. Fixed order: {evaluation['fixed_order']} units/day; target-stock rule: {evaluation['target_stock']} units.")
    summary = evaluation["summary"]
    chart(px.bar(summary, x="policy", y="mean_reward", error_y="reward_standard_error", color="policy", labels={"policy": "Policy", "mean_reward": "Average weekly reward (PHP)"}))
    st.caption("Error bars show one standard error across simulated weeks. Reward includes the unmet-demand penalty; inventory-adjusted profit excludes that penalty and includes terminal stock valued at cost.")
    st.dataframe(summary.round(2), hide_index=True, width="stretch")
    learned = float(summary.loc[summary.policy.eq("Q-learning"), "mean_reward"].iloc[0])
    baseline = float(summary.loc[summary.policy.ne("Q-learning"), "mean_reward"].max())
    st.write(f"Measured reward difference from the stronger simple rule: **PHP {learned-baseline:+,.2f} per week**. This comparison applies to the fitted simulator, not a real store.")
    download_csv(evaluation["samples"], "Export all evaluation weeks", "restocking-evaluation.csv")
    with st.expander("Inspect one identical evaluation week", expanded=True):
        policy = st.selectbox("Policy to inspect", summary.policy.tolist())
        log = evaluation["log"].query("policy == @policy")
        st.dataframe(log.drop(columns="policy").round(2), hide_index=True, width="stretch")
        download_csv(evaluation["log"], "Export decision logs", "restocking-decision-logs.csv")
    with st.expander("Q-table, demand estimates & implementation"):
        st.dataframe(pd.DataFrame({"weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "fitted_mean_demand": result["means"]}), hide_index=True)
        stock = st.slider("Inspect Q-values at inventory", 0, 30, 0)
        st.dataframe(pd.DataFrame(result["q"][stock], index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], columns=[f"Order {q}" for q in cfg.actions]))
        st.caption("Actions exceeding capacity are masked even though the table has entries for them. Unvisited state-action entries can remain zero.")
        st.code('target = reward\nif not terminal:\n    target += gamma * max(q[next_state[0], next_state[1], i] for i in valid_next)\nq[state[0], state[1], action] += alpha * (target-q[state[0], state[1], action])', language="python")
        st.write("Weekday means estimate a Poisson demand distribution from earlier history. Future demand is sampled and revealed after the decision. New random weeks test policies within that assumed distribution; they do not validate real-world demand. Reward = revenue − purchase cost − holding cost − service penalty + terminal stock value.")

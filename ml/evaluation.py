"""Frozen policy comparison on shared, newly sampled demand weeks."""
import numpy as np
import pandas as pd
from ml.restocking_env import RestockingEnv


def evaluate_agent(result, weeks=100, seed=314159):
    if seed == result["metrics"]["seed"]:
        raise ValueError("Use a different random seed for evaluation.")
    if not 1 <= int(weeks) <= 10000:
        raise ValueError("Evaluation weeks must be between 1 and 10,000.")
    q, cfg, means = result["q"], result["settings"], result["means"]
    demands = np.random.default_rng(seed).poisson(means, size=(int(weeks), 7))
    # Baselines use only simulator training means, never evaluation demand.
    fixed_index = min(range(len(cfg.actions)), key=lambda a: abs(cfg.actions[a]-means.mean()))
    target_stock = min(cfg.capacity, int(np.ceil(means.mean()*1.5)))
    rows, logs = [], []
    for policy in ("Q-learning", "Fixed daily order", "Reorder to target"):
        for week, demand in enumerate(demands):
            env = RestockingEnv(cfg, demand)
            daily = []
            for _ in range(7):
                valid = env.valid_actions()
                if policy == "Q-learning":
                    action = max(valid, key=lambda a: q[env.stock, env.day, a])
                elif policy == "Fixed daily order":
                    desired = cfg.actions[fixed_index]
                    action = max((a for a in valid if cfg.actions[a] <= desired), key=lambda a: cfg.actions[a])
                else:
                    desired = max(0, target_stock-env.stock)
                    action = min(valid, key=lambda a: (abs(cfg.actions[a]-desired), cfg.actions[a]))
                _, _, _, log = env.step(action)
                daily.append(log)
                if week == 0:
                    logs.append({"policy": policy, **log})
            frame = pd.DataFrame(daily)
            rows.append({"policy": policy, "week": week+1, "reward": frame.reward.sum(),
                         "revenue": frame.revenue.sum(), "purchase_cost": frame.purchase_cost.sum(),
                         "holding_cost": frame.holding_cost.sum(), "service_penalty": frame.service_penalty.sum(),
                         "terminal_value": frame.terminal_value.sum(),
                         "inventory_adjusted_profit": frame.revenue.sum()-frame.purchase_cost.sum()-frame.holding_cost.sum()+frame.terminal_value.sum(),
                         "unmet_units": frame.unmet.sum(), "mean_leftover": frame.leftover.mean(), "ending_stock": env.stock})
    samples = pd.DataFrame(rows)
    summary = samples.groupby("policy", sort=False).agg(
        mean_reward=("reward", "mean"), reward_std=("reward", "std"),
        mean_revenue=("revenue", "mean"), mean_purchase_cost=("purchase_cost", "mean"),
        mean_holding_cost=("holding_cost", "mean"), mean_service_penalty=("service_penalty", "mean"),
        mean_terminal_value=("terminal_value", "mean"),
        mean_inventory_adjusted_profit=("inventory_adjusted_profit", "mean"),
        mean_unmet_units=("unmet_units", "mean"), mean_leftover=("mean_leftover", "mean")
    ).reset_index()
    summary["reward_standard_error"] = summary.reward_std/np.sqrt(weeks)
    return {"summary": summary, "samples": samples, "log": pd.DataFrame(logs),
            "weeks": int(weeks), "seed": seed, "fixed_order": cfg.actions[fixed_index], "target_stock": target_stock}

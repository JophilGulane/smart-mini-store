"""Readable tabular Q-learning: explicit exploration, action masks, terminal target."""
import numpy as np
import pandas as pd
from core.history import signature
from ml.restocking_env import RestockingEnv, settings_dict


def demand_estimates(history):
    usable = history.loc[history.stockout_flag.eq(0)].sort_values("date").copy()
    if len(usable) < 35:
        raise ValueError("Need at least 35 completed, non-stockout observations for this product.")
    # Fit simulator parameters on earlier data. New evaluation samples are still
    # from this fitted simulator, not a claim of real-world validation.
    train = usable.iloc[:int(len(usable)*0.8)].copy()
    train["weekday"] = pd.to_datetime(train.date).dt.day_of_week
    counts = train.groupby("weekday").size()
    if len(counts) != 7 or counts.min() < 3:
        raise ValueError("Need at least three training observations per weekday.")
    means = train.groupby("weekday").units_sold.mean().reindex(range(7)).to_numpy(dtype=float)
    return means, {"fit_start": train.date.iloc[0], "fit_end": train.date.iloc[-1], "fit_rows": len(train)}


def q_update(q, state, action, reward, next_state, terminal, valid_next, alpha=0.1, gamma=0.95):
    target = reward
    if not terminal:
        target += gamma * max(q[next_state[0], next_state[1], i] for i in valid_next)
    q[state[0], state[1], action] += alpha * (target-q[state[0], state[1], action])


def train_agent(history, settings, episodes=3000, seed=42, progress=None):
    if not 10 <= int(episodes) <= 20000:
        raise ValueError("Training episodes must be between 10 and 20,000.")
    means, meta = demand_estimates(history)
    rng = np.random.default_rng(seed)
    q = np.zeros((settings.capacity+1, 7, len(settings.actions)), dtype=float)
    curve = []
    for episode in range(int(episodes)):
        epsilon = max(0.05, 1.0-0.95*episode/max(1, episodes*0.8))
        env = RestockingEnv(settings, rng.poisson(means))
        total = 0.0
        for _ in range(7):
            state, valid = env.state, env.valid_actions()
            if rng.random() < epsilon:
                action = int(rng.choice(valid))
            else:
                values = q[state[0], state[1], valid]
                # Random ties during training avoid always favoring action zero.
                action = int(rng.choice(np.array(valid)[values == values.max()]))
            next_state, reward, terminal, _ = env.step(action)
            q_update(q, state, action, reward, next_state, terminal, [] if terminal else env.valid_actions())
            total += reward
        curve.append({"episode": episode+1, "reward": total, "epsilon": epsilon})
        if progress and ((episode+1) % 250 == 0 or episode+1 == episodes):
            progress((episode+1)/episodes)
    metrics = {**meta, "episodes": int(episodes), "seed": seed, "alpha": 0.1, "gamma": 0.95,
               "epsilon_start": 1.0, "epsilon_end": float(epsilon), "states": (settings.capacity+1)*7}
    return {"q": q, "means": means, "settings": settings, "curve": pd.DataFrame(curve),
            "metrics": metrics, "signature": signature(history, settings_dict(settings)), "cutoff": str(history.date.max())}

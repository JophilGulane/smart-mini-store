import numpy as np
import pandas as pd
import pytest
from core.history import history
from ml.restocking_env import Settings, RestockingEnv
from ml.q_learning import q_update, train_agent
from ml.evaluation import evaluate_agent


def test_inventory_conservation_reward_and_terminal_value():
    cfg = Settings(10, 15)
    env = RestockingEnv(cfg, [3]*7)
    _, reward, terminal, log = env.step(1)  # order 5, sell 3, leave 2
    assert log["leftover"] == 2 and log["unmet"] == 0
    assert reward == 45-50-1 and not terminal
    for _ in range(6):
        _, reward, terminal, log = env.step(1)
        assert log["opening"]+log["order"] == log["sold"]+log["leftover"]
    assert terminal and log["terminal_value"] == env.stock*10
    with pytest.raises(ValueError, match="finished"):
        env.step(0)


def test_invalid_actions_and_terminal_update():
    env = RestockingEnv(Settings(10, 15), [0]*7)
    env.stock = 29
    assert env.valid_actions() == [0]
    with pytest.raises(ValueError, match="capacity"):
        env.step(1)
    q = np.zeros((31, 7, 4))
    q[0, 0] = 999
    q_update(q, (0, 6), 0, 20, (0, 7), True, [], alpha=0.1)
    assert q[0, 6, 0] == 2  # No illegal terminal lookup or bootstrapping.


def test_nonterminal_update_masks_actions():
    q = np.zeros((31, 7, 4))
    q[29, 1] = [10, 9999, 9999, 9999]
    q_update(q, (0, 0), 0, 2, (29, 1), False, [0], alpha=1, gamma=0.5)
    assert q[0, 0, 0] == 7


def test_training_reproducible_and_evaluation_frozen(demo):
    raw = history(demo, 1)
    result = train_agent(raw, Settings(10, 15), episodes=100)
    second = train_agent(raw, Settings(10, 15), episodes=100)
    np.testing.assert_array_equal(result["q"], second["q"])
    assert np.count_nonzero(result["q"]) > 0
    frozen = result["q"].copy()
    output = evaluate_agent(result, weeks=20)
    np.testing.assert_array_equal(result["q"], frozen)
    demands = output["log"].pivot(index="weekday", columns="policy", values="demand")
    assert (demands.nunique(axis=1) == 1).all()
    pd.testing.assert_frame_equal(output["summary"], evaluate_agent(result, weeks=20)["summary"])
    assert len(output["samples"]) == 60
    with pytest.raises(ValueError, match="different"):
        evaluate_agent(result, seed=42)

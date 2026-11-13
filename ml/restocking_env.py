"""A seven-day, finite-horizon inventory environment, Monday through Sunday."""
from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class Settings:
    cost: float
    price: float
    holding: float = 0.5
    shortage: float = 3.0
    capacity: int = 30
    actions: tuple = (0, 5, 10, 15)

    def __post_init__(self):
        if not all(np.isfinite(x) and x >= 0 for x in (self.cost, self.price, self.holding, self.shortage)):
            raise ValueError("Costs, price, and penalties must be finite and nonnegative.")
        if self.price <= self.cost:
            raise ValueError("For this simulator, selling price must exceed unit cost.")
        if self.capacity < 15:
            raise ValueError("Storage capacity must be at least 15 units.")


class RestockingEnv:
    def __init__(self, settings, demand):
        self.settings = settings
        self.demand = np.asarray(demand, dtype=int)
        if self.demand.shape != (7,) or (self.demand < 0).any():
            raise ValueError("Provide seven nonnegative daily demand values.")
        self.stock, self.day = 0, 0

    @property
    def state(self):
        return self.stock, self.day

    def valid_actions(self):
        return [i for i, order in enumerate(self.settings.actions) if self.stock+order <= self.settings.capacity]

    def step(self, action_index):
        if self.day >= 7:
            raise ValueError("Episode has finished.")
        if action_index not in self.valid_actions():
            raise ValueError("Order would exceed storage capacity.")
        cfg, opening, day = self.settings, self.stock, self.day
        order = cfg.actions[action_index]
        demand = int(self.demand[day])
        sold = min(opening+order, demand)
        self.stock = opening+order-sold
        unmet = demand-sold
        terminal = day == 6
        revenue, purchases = sold*cfg.price, order*cfg.cost
        holding, penalty = self.stock*cfg.holding, unmet*cfg.shortage
        terminal_value = self.stock*cfg.cost if terminal else 0.0
        reward = revenue-purchases-holding-penalty+terminal_value
        log = {"weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day],
               "opening": opening, "order": order, "demand": demand, "sold": sold,
               "leftover": self.stock, "unmet": unmet, "revenue": revenue,
               "purchase_cost": purchases, "holding_cost": holding, "service_penalty": penalty,
               "terminal_value": terminal_value, "reward": reward}
        self.day += 1
        return self.state, reward, terminal, log


def settings_dict(settings):
    return asdict(settings)

"""Ranking rules: in which order the greedy looks at orders and aisles.

Each rule receives the instance and returns an array with ALL indices, best first.
To try a new rule, write a function and register it in ORDER_RANKINGS or
AISLE_RANKINGS - the solver automatically tries every combination.

"""

from collections.abc import Callable

import numpy as np

from wop.instance import Instance

Ranking = Callable[[Instance], np.ndarray]

def total_demand(inst: Instance) -> np.ndarray:
    """demand[i] = units of item i requested by all orders together."""
    demand = np.zeros(inst.n_items, dtype=np.int64)
    for items, qtys in inst.orders:
        demand[items] += qtys
    return demand

def useful_stock(inst: Instance) -> np.ndarray:
    """useful[a] = units in aisle a that some order could actually use."""
    demand = total_demand(inst)
    return np.array(
        [np.minimum(qtys, demand[items]).sum() for items, qtys in inst.aisles], dtype = np.int64
    )

# ---------------------------------------------------------------- orders ---

def orders_by_units(inst: Instance) -> np.ndarray:
    """Biggest orders first (by total units, `inst.order_units`)."""
    return np.argsort(-inst.order_units, kind="stable")


ORDER_RANKINGS: dict[str, Ranking] = {
    "units_desc": orders_by_units,
}

# ---------------------------------------------------------------- aisles ---

def aisles_by_useful_stock(inst: Instance) -> np.ndarray:
    """Aisles with the most *useful* stock first.

    Useful stock of an aisle = for each item in it, min(units in the aisle,
    units of that item requested by all orders together). Stock nobody asked
    for does not help.
    """
    return np.argsort(-useful_stock(inst), kind="stable")


AISLE_RANKINGS: dict[str, Ranking] = {
    "useful_stock": aisles_by_useful_stock,
}

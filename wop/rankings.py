"""Ranking rules: in which order the greedy looks at orders and aisles.

Each rule receives the instance and returns an array with ALL indices, best first.
To try a new rule, write a function and register it in ORDER_RANKINGS or
AISLE_RANKINGS - the solver automatically tries every combination.

NOT IMPLEMENTED YET - the first rules come with issue "Greedy construction".
"""

from collections.abc import Callable

import numpy as np

from wop.instance import Instance

Ranking = Callable[[Instance], np.ndarray]


# ---------------------------------------------------------------- orders ---

def orders_by_units(inst: Instance) -> np.ndarray:
    """Biggest orders first (by total units, `inst.order_units`)."""
    raise NotImplementedError("issue: Greedy construction")


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
    raise NotImplementedError("issue: Greedy construction")


AISLE_RANKINGS: dict[str, Ranking] = {
    "useful_stock": aisles_by_useful_stock,
}

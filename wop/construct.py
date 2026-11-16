"""Constructive heuristic.

NOT IMPLEMENTED YET - see issue "Greedy construction" and docs/strategy.md.

Two building blocks:

1. fill_orders   - aisles are fixed: pick orders greedily while they fit in the
                   remaining stock and keep the wave <= UB.
2. greedy_prefix - try the first k aisles of a ranking for k = 1, 2, 3, ...
                   and keep the best feasible result.
"""

import numpy as np

from wop.instance import Instance
from wop.solution import Solution


def aisle_stock(inst: Instance, aisle_ids) -> np.ndarray:
    """stock[i] = units of item i available in the given aisles."""
    stock = np.zeros(inst.n_items, dtype=np.int64)
    for a in aisle_ids:
        items, qtys = inst.aisles[a]
        stock[items] += qtys  # item ids are unique inside one aisle (checked in tests)
    return stock


def fill_orders(inst: Instance, aisle_ids, order_rank) -> list[int]:
    """Aisles are fixed: choose which orders to pick.

    Go through the orders in `order_rank` order and take each one that still fits:
    (a) every item it needs is still in the remaining stock of `aisle_ids`, and
    (b) adding its units does not make the wave exceed UB.
    When an order is taken, subtract its quantities from the remaining stock.

    Return the list of chosen order indices. The result may be below LB -
    the caller must check that.
    """
    raise NotImplementedError("issue: Greedy construction")


def greedy_prefix(inst: Instance, aisle_rank, order_rank) -> Solution | None:
    """Choose how many aisles to visit.

    For k = 1, 2, 3, ...: visit the first k aisles of `aisle_rank`, call
    `fill_orders`, and if the wave reaches LB compute units / k.
    Return the best feasible Solution found (None if no k reaches LB).

    Pruning (important for speed): with k aisles the objective can never exceed
    min(UB, stock of those k aisles) / k. Once UB / k cannot beat the best
    value found so far, no larger k can either - stop the loop.
    """
    raise NotImplementedError("issue: Greedy construction")

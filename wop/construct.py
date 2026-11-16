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
from wop.rankings import useful_stock


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
    stock = aisle_stock(inst, aisle_ids)
    total = 0
    chosen = []
    for o in order_rank:
        units = inst.order_units[o]
        if total + units > inst.ub:
            continue
        items, qtys = inst.orders[o]
        if np.all(stock[items] >= qtys):
            stock[items] -= qtys
            total += units
            chosen.append(int(o))
    return chosen


def greedy_prefix(inst: Instance, aisle_rank, order_rank) -> Solution | None:
    """Choose how many aisles to visit.

    For k = 1, 2, 3, ...: visit the first k aisles of `aisle_rank`, call
    `fill_orders`, and if the wave reaches LB compute units / k.
    Return the best feasible Solution found (None if no k reaches LB).

    Pruning (important for speed): with k aisles the objective can never exceed
    min(UB, stock of those k aisles) / k. Once UB / k cannot beat the best
    value found so far, no larger k can either - stop the loop.
    """
    useful = useful_stock(inst)
    best, best_value = None, 0.0
    stock_so_far = 0
    for k in range(1, inst.n_aisles + 1):
        stock_so_far += useful[aisle_rank[k - 1]]
        if inst.ub / k <= best_value:
            break
        if min(inst.ub, stock_so_far) / k <= best_value:
            continue
        
        aisles = [int(a) for a in aisle_rank[:k]]
        orders = fill_orders(inst, aisles, order_rank)
        units = int(inst.order_units[orders].sum()) if orders else 0
        if units >= inst.lb and units / k > best_value:
            best, best_value = Solution(orders, aisles), units / k
    return best
        

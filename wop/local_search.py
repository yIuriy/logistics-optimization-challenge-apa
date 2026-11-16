"""Local search: improve a feasible solution with small changes.

NOT IMPLEMENTED YET - see the "Local search" issue and docs/strategy.md.

Idea: the aisle set decides everything (orders are re-filled with
`fill_orders`). Starting from `sol`, repeatedly try:

* remove - drop one visited aisle,
* add    - visit one more aisle,
* swap   - replace a visited aisle by a non-visited one,

re-fill the orders, and accept the change if the solution stays feasible and
the objective improves. Stop when no move helps or the deadline is reached.
"""

import time

from wop.solution import Solution, objective
from wop.construct import fill_orders
from wop.instance import Instance
from wop.rankings import aisles_by_useful_stock
from wop.instance import Instance


def evaluate(inst: Instance, aisles: list[int], order_rank) -> tuple[list[int] | None, float]: 
    """Fill orders for this aisle set and return (orders, objective)"""
    if not aisles:
        return None, 0.0
    orders = fill_orders(inst, aisles, order_rank)
    units = int(inst.order_units[orders].sum()) if orders else 0
    if units < inst.lb:
        return None, 0.0
    return orders, units / len(aisles)
        

def neighbours(aisles: list[int], outside: list[int]) -> list[list[int]]:
    """All aisle sets one move away from `aisles`.

    remove: drop one visited aisle             (fewer aisles -> ratio may go up)
    add:    visit one more aisle                (more stock -> more orders fit)
    swap:   replace a visited aisle by an outside one
    """
    removes = [[x for x in aisles if x != r] for r in aisles]
    adds = [aisles + [a] for a in outside]
    swaps = [[a if x == r else x for x in aisles] for r in aisles for a in outside]
    return removes + adds + swaps
    
    
def improve(inst: Instance, sol: Solution, order_rank, deadline: float, n_candidates: int = 30) -> Solution:
    """Local search over the aisle set (first improvement).

    Repeatedly look at the neighbours of the current aisle set (remove / add /
    swap one aisle), re-fill the orders, and move to the first neighbour with a
    better objective. Stop when no neighbour improves or the deadline passes.
    Only the `n_candidates` best outside aisles (by useful stock) are tried,
    so each round stays fast on large instances.

    `deadline` is an absolute time.perf_counter() value - stop before it.
    """
    aisles = list(sol.aisles)
    orders, value = sol.orders, objective(inst, sol)
    ranked = [int(a) for a in aisles_by_useful_stock(inst)]
    moves = 0
    improved = True
    while improved and time.perf_counter() < deadline:
        improved = False
        outside = [a for a in ranked if a not in aisles][:n_candidates]
        for candidate in neighbours(aisles, outside):
            if time.perf_counter() >= deadline:
                break
            new_orders, new_value = evaluate(inst, candidate, order_rank)
            if new_value > value + 1e-9:
                aisles, orders, value = candidate, new_orders, new_value
                moves += 1
                improved = True
                break
    return Solution(orders, aisles, {"local_search_moves": moves})

"""Solver pipeline: construct (every ranking combination) -> improve."""

import time

from wop.construct import greedy_prefix
from wop.instance import Instance
from wop.local_search import improve
from wop.rankings import AISLE_RANKINGS, ORDER_RANKINGS
from wop.solution import Solution, objective


def solve(inst: Instance, time_limit: float = 60.0, seed: int = 0) -> Solution | None:
    """Return the best feasible solution found, or None if none was found."""
    deadline = time.perf_counter() + time_limit

    # 1. Construction: try every (aisle ranking, order ranking) pair.
    best, best_value, best_order_rank = None, -1.0, None
    order_ranks = {name: rank(inst) for name, rank in ORDER_RANKINGS.items()}
    for aisle_name, aisle_ranking in AISLE_RANKINGS.items():
        aisle_rank = aisle_ranking(inst)
        for order_name, order_rank in order_ranks.items():
            sol = greedy_prefix(inst, aisle_rank, order_rank)
            if sol is not None and objective(inst, sol) > best_value:
                best, best_value, best_order_rank = sol, objective(inst, sol), order_rank
                best.info["construction"] = f"{aisle_name}+{order_name}"

    # 2. Improvement.
    if best is not None:
        info = best.info
        best = improve(inst, best, best_order_rank, deadline)
        best.info = {**info, **best.info}
    return best

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

from wop.instance import Instance
from wop.solution import Solution


def improve(inst: Instance, sol: Solution, order_rank, deadline: float) -> Solution:
    """Return a solution at least as good as `sol` (currently: `sol` itself).

    `deadline` is an absolute time.perf_counter() value - stop before it.
    """
    return sol

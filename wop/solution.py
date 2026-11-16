"""Solutions: objective, feasibility check and file I/O.

Output format (same as the official challenge):

    <number of selected orders>
    <order index>          (one per line)
    <number of visited aisles>
    <aisle index>          (one per line)
"""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from wop.instance import Instance


@dataclass
class Solution:
    orders: list[int]  # O' - the wave
    aisles: list[int]  # A' - aisles visited
    info: dict = field(default_factory=dict)  # free-form metadata (strategy used, ...)


def total_units(inst: Instance, sol: Solution) -> int:
    return int(inst.order_units[sol.orders].sum()) if sol.orders else 0


def objective(inst: Instance, sol: Solution) -> float:
    """Units picked per visited aisle (the value we maximize)."""
    if not sol.aisles:
        return 0.0
    return total_units(inst, sol) / len(sol.aisles)


def violations(inst: Instance, sol: Solution) -> list[str]:
    """Return the list of broken rules. An empty list means the solution is feasible."""
    problems = []
    if len(set(sol.orders)) != len(sol.orders):
        problems.append("duplicated order")
    if len(set(sol.aisles)) != len(sol.aisles):
        problems.append("duplicated aisle")
    if any(not 0 <= o < inst.n_orders for o in sol.orders):
        problems.append("order index out of range")
    if any(not 0 <= a < inst.n_aisles for a in sol.aisles):
        problems.append("aisle index out of range")
    if problems:
        return problems
    if not sol.aisles:
        problems.append("no aisle visited")

    units = total_units(inst, sol)
    if units < inst.lb:
        problems.append(f"wave too small: {units} < LB={inst.lb}")
    if units > inst.ub:
        problems.append(f"wave too large: {units} > UB={inst.ub}")

    demand = np.zeros(inst.n_items, dtype=np.int64)
    for o in sol.orders:
        items, qtys = inst.orders[o]
        np.add.at(demand, items, qtys)
    stock = np.zeros(inst.n_items, dtype=np.int64)
    for a in sol.aisles:
        items, qtys = inst.aisles[a]
        np.add.at(stock, items, qtys)
    short = np.flatnonzero(demand > stock)
    if short.size:
        problems.append(f"not enough stock for {short.size} item(s), e.g. item {short[0]}")
    return problems


def is_feasible(inst: Instance, sol: Solution) -> bool:
    return not violations(inst, sol)


def write_solution(path: str | Path, sol: Solution) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [str(len(sol.orders)), *map(str, sol.orders), str(len(sol.aisles)), *map(str, sol.aisles)]
    path.write_text("\n".join(lines) + "\n")


def read_solution(path: str | Path) -> Solution:
    values = [int(v) for v in Path(path).read_text().split()]
    n_orders = values[0]
    orders = values[1 : 1 + n_orders]
    n_aisles = values[1 + n_orders]
    aisles = values[2 + n_orders : 2 + n_orders + n_aisles]
    return Solution(orders, aisles)

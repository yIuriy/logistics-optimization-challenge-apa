"""Reading problem instances.

Input format (same as the official challenge):

    <n_orders> <n_items> <n_aisles>
    one line per order:  <k> <item> <qty> <item> <qty> ...   (k pairs)
    one line per aisle:  <k> <item> <qty> <item> <qty> ...   (k pairs)
    <LB> <UB>
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# An order or an aisle is stored as two aligned arrays: item ids and quantities.
ItemList = tuple[np.ndarray, np.ndarray]


@dataclass
class Instance:
    name: str
    n_items: int
    orders: list[ItemList]  # orders[o] = (items, quantities requested)
    aisles: list[ItemList]  # aisles[a] = (items, quantities in stock)
    lb: int  # minimum total units in the wave
    ub: int  # maximum total units in the wave
    order_units: np.ndarray  # order_units[o] = total units of order o

    @property
    def n_orders(self) -> int:
        return len(self.orders)

    @property
    def n_aisles(self) -> int:
        return len(self.aisles)


def _read_lists(tokens: list[str], pos: int, count: int) -> tuple[list[ItemList], int]:
    lists = []
    for _ in range(count):
        k = int(tokens[pos])
        pos += 1
        items = np.array(tokens[pos : pos + 2 * k : 2], dtype=np.int64)
        qtys = np.array(tokens[pos + 1 : pos + 2 * k : 2], dtype=np.int64)
        pos += 2 * k
        lists.append((items, qtys))
    return lists, pos


def read_instance(path: str | Path) -> Instance:
    path = Path(path)
    tokens = path.read_text().split()
    n_orders, n_items, n_aisles = int(tokens[0]), int(tokens[1]), int(tokens[2])
    orders, pos = _read_lists(tokens, 3, n_orders)
    aisles, pos = _read_lists(tokens, pos, n_aisles)
    lb, ub = int(tokens[pos]), int(tokens[pos + 1])
    order_units = np.array([q.sum() for _, q in orders], dtype=np.int64)
    name = f"{path.parent.name}/{path.name}"
    return Instance(name, n_items, orders, aisles, lb, ub, order_units)

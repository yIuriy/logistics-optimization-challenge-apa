"""Basic tests on the 5x5x5 example from the official problem description
(data/instances/a/instance_0020.txt), whose optimum is 5.0."""

from pathlib import Path

import numpy as np
import pytest

from wop.construct import fill_orders, greedy_prefix
from wop.instance import read_instance
from wop.official import official_check
from wop.rankings import AISLE_RANKINGS, ORDER_RANKINGS
from wop.solution import Solution, is_feasible, objective, read_solution, violations, write_solution
from wop.solver import solve

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "data" / "instances" / "a" / "instance_0020.txt"


@pytest.fixture
def inst():
    return read_instance(EXAMPLE)


def test_reads_example(inst):
    assert (inst.n_orders, inst.n_items, inst.n_aisles) == (5, 5, 5)
    assert (inst.lb, inst.ub) == (5, 12)
    assert inst.order_units.tolist() == [4, 2, 3, 5, 1]


def test_examples_from_pdf(inst):
    # The three waves listed in the problem description.
    assert objective(inst, Solution([0, 4], [0, 1])) == 2.5
    assert objective(inst, Solution([0, 2, 3], [1, 3, 4])) == 4.0
    optimal = Solution([0, 1, 2, 4], [1, 3])
    assert is_feasible(inst, optimal) and objective(inst, optimal) == 5.0


def test_detects_violations(inst):
    assert violations(inst, Solution([4], [0]))  # 1 unit < LB = 5
    assert violations(inst, Solution([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]))  # 15 units > UB = 12
    assert violations(inst, Solution([0, 4], [2]))  # aisle 2 has no item 0


def test_fill_respects_stock_and_ub(inst):
    orders = fill_orders(inst, [1, 3], ORDER_RANKINGS["units_desc"](inst))
    assert is_feasible(inst, Solution(orders, [1, 3]))


def test_greedy_and_solver_are_feasible(inst):
    sol = greedy_prefix(inst, AISLE_RANKINGS["useful_stock"](inst), ORDER_RANKINGS["units_desc"](inst))
    assert sol is not None and is_feasible(inst, sol)
    best = solve(inst, time_limit=5)
    assert is_feasible(inst, best) and objective(inst, best) >= objective(inst, sol)


def test_file_roundtrip_matches_official_checker(inst, tmp_path):
    sol = Solution([0, 1, 2, 4], [1, 3])
    path = tmp_path / "sol.txt"
    write_solution(path, sol)
    back = read_solution(path)
    assert (back.orders, back.aisles) == (sol.orders, sol.aisles)
    assert official_check(EXAMPLE, path) == (True, 5.0)


@pytest.mark.parametrize("dataset", ["a", "b", "x"])
def test_item_ids_are_unique_inside_each_order_and_aisle(dataset):
    # construct.py relies on this (fancy-index += / -=). Checks the first instance of each dataset.
    inst = read_instance(sorted((ROOT / "data" / "instances" / dataset).glob("*.txt"))[0])
    for items, _ in inst.orders + inst.aisles:
        assert len(np.unique(items)) == len(items)

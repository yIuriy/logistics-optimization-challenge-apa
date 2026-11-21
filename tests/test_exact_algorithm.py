import itertools
import math
import subprocess
import sys
import time
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from order_selection.exact_algorithm import solve
from order_selection.instance import (
    Instance,
    Solution,
    is_feasible,
    objective,
    read_instance,
    write_solution,
)

ROOT = Path(__file__).parents[1]
CHECKER = ROOT / "src" / "order_selection" / "checker.py"
B_INSTANCE_0001 = ROOT / "data" / "b_instance_0001.txt"

# Example of section 3.1 of the official rules (5 orders, 5 items, 5 aisles)
EXAMPLE_INSTANCE_TEXT = """5 5 5
2 0 3 2 1
2 1 1 3 1
2 2 1 4 2
4 0 1 2 2 3 1 4 1
1 1 1
4 0 2 1 1 2 1 4 1
4 0 2 1 1 2 2 4 1
3 1 2 3 1 4 2
4 0 2 1 1 3 1 4 1
4 1 1 2 2 3 1 4 2
5 12
"""


@st.composite
def small_instances(draw):
    """Draw a tiny random instance small enough to verify by brute force."""
    n_items = draw(st.integers(min_value=1, max_value=3))
    item_units = st.dictionaries(
        st.integers(min_value=0, max_value=n_items - 1),
        st.integers(min_value=1, max_value=4),
        min_size=1,
    )
    orders = draw(st.lists(item_units, min_size=1, max_size=4))
    aisles = draw(st.lists(item_units, min_size=1, max_size=3))
    wave_min_units = draw(st.integers(min_value=1, max_value=10))
    wave_max_units = draw(st.integers(min_value=wave_min_units, max_value=20))
    return Instance(
        orders=orders,
        aisles=aisles,
        n_items=n_items,
        wave_min_units=wave_min_units,
        wave_max_units=wave_max_units,
    )


def brute_force_optimum(instance: Instance) -> float | None:
    """Find the exact optimal objective by enumerating all order and aisle subsets."""
    order_subsets = [
        list(subset)
        for size in range(1, len(instance.orders) + 1)
        for subset in itertools.combinations(range(len(instance.orders)), size)
    ]
    aisle_subsets = [
        list(subset)
        for size in range(1, len(instance.aisles) + 1)
        for subset in itertools.combinations(range(len(instance.aisles)), size)
    ]
    feasible_values = [
        objective(instance, sol)
        for orders in order_subsets
        for aisles in aisle_subsets
        if is_feasible(instance, sol := Solution(orders, aisles))
    ]
    return max(feasible_values, default=None)


def test_example_instance_proves_optimum_five_and_passes_checker(tmp_path):
    instance_path = tmp_path / "example.txt"
    solution_path = tmp_path / "solution.txt"
    instance_path.write_text(EXAMPLE_INSTANCE_TEXT, encoding="utf-8")
    instance = read_instance(instance_path)

    solution, report = solve(instance, {"time_limit_seconds": 60})

    assert solution is not None
    assert is_feasible(instance, solution)
    assert math.isclose(objective(instance, solution), 5.0)
    assert report["status"] == "optimal"
    assert report["iterations"] >= 1
    assert report["objective_lower_bound"] <= report["objective_upper_bound"]
    assert math.isclose(report["objective_lower_bound"], 5.0)
    assert math.isclose(report["objective_upper_bound"], 5.0)

    write_solution(solution, solution_path)
    checker = subprocess.run(  # noqa: S603 (runs the official checker with test paths)
        [sys.executable, CHECKER, instance_path, solution_path],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Is solution feasible: True" in checker.stdout
    assert "Objective function value: 5.0" in checker.stdout


def test_infeasible_instance_returns_no_solution():
    instance = Instance(
        orders=[{0: 5}],
        aisles=[{0: 2}],
        n_items=1,
        wave_min_units=3,
        wave_max_units=10,
    )
    solution, report = solve(instance, {"time_limit_seconds": 30})
    assert solution is None
    assert report["status"] == "no_solution"
    assert report["objective_lower_bound"] is None
    assert report["objective_upper_bound"] is None


def test_time_limit_on_real_instance_respects_bounds():
    instance = read_instance(B_INSTANCE_0001)
    solution, report = solve(instance, {"time_limit_seconds": 2.0})
    assert report["status"] in {"optimal", "time_limit", "no_solution"}
    assert report["iterations"] >= 1
    if solution is not None:
        assert is_feasible(instance, solution)
        assert math.isclose(
            report["objective_lower_bound"], objective(instance, solution)
        )
        assert report["objective_lower_bound"] <= report["objective_upper_bound"]


def test_large_instance_stops_before_the_time_limit():
    # HiGHS alone ran 21 s with a 10 s limit here, inside the root cut rounds
    instance = read_instance(B_INSTANCE_0001)
    start = time.perf_counter()
    solution, report = solve(instance, {"time_limit_seconds": 10})
    assert time.perf_counter() - start < 10
    assert report["status"] == "time_limit"
    assert solution is not None
    assert is_feasible(instance, solution)
    assert math.isclose(report["objective_lower_bound"], objective(instance, solution))


@settings(max_examples=40, deadline=None)
@given(instance=small_instances())
def test_exact_algorithm_matches_brute_force_optimum(instance):
    expected = brute_force_optimum(instance)
    solution, report = solve(instance, {"time_limit_seconds": 30})

    if expected is None:
        assert solution is None
        assert report["status"] == "no_solution"
        assert report["objective_lower_bound"] is None
        assert report["objective_upper_bound"] is None
    else:
        assert solution is not None
        assert is_feasible(instance, solution)
        assert report["status"] == "optimal"
        assert math.isclose(objective(instance, solution), expected, rel_tol=1e-6)
        assert report["objective_lower_bound"] == report["objective_upper_bound"]
        assert math.isclose(report["objective_lower_bound"], expected, rel_tol=1e-6)

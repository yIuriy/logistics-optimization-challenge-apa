import random
from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from order_selection.genetic_algorithm import build_repair_tables, repair, solve
from order_selection.instance import Instance, Solution, is_feasible

# Example of section 3.1 of the official rules (5 orders, 5 items, 5 aisles)
EXAMPLE_INSTANCE = Instance(
    orders=[
        {0: 3, 2: 1},
        {1: 1, 3: 1},
        {2: 1, 4: 2},
        {0: 1, 2: 2, 3: 1, 4: 1},
        {1: 1},
    ],
    aisles=[
        {0: 2, 1: 1, 2: 1, 4: 1},
        {0: 2, 1: 1, 2: 2, 4: 1},
        {1: 2, 3: 1, 4: 2},
        {0: 2, 1: 1, 3: 1, 4: 1},
        {1: 1, 2: 2, 3: 1, 4: 2},
    ],
    n_items=5,
    wave_min_units=5,
    wave_max_units=12,
)


@st.composite
def instances_and_bits(draw):
    """Draw a small instance with a feasible wave and a random bit vector.

    The aisles are random, so some items may lack stock. One extra aisle stores
    exactly what order 0 requests, and the lower limit is at most the units of
    the smallest order, so any single order that fits the stock is a feasible wave.
    """
    n_items = draw(st.integers(min_value=1, max_value=4))
    item_units = st.dictionaries(
        st.integers(min_value=0, max_value=n_items - 1),
        st.integers(min_value=1, max_value=5),
        min_size=1,
    )
    orders = draw(st.lists(item_units, min_size=1, max_size=8))
    aisles = [*draw(st.lists(item_units, max_size=4)), dict(orders[0])]
    order_units = [sum(order.values()) for order in orders]
    instance = Instance(
        orders=orders,
        aisles=aisles,
        n_items=n_items,
        wave_min_units=draw(st.integers(min_value=1, max_value=min(order_units))),
        wave_max_units=draw(
            st.integers(min_value=order_units[0], max_value=sum(order_units))
        ),
    )
    bits = draw(st.lists(st.integers(0, 1), min_size=len(orders), max_size=len(orders)))
    return instance, bits


@given(instance_and_bits=instances_and_bits(), seed=st.integers(0, 1000))
def test_repair_always_returns_a_feasible_solution(instance_and_bits, seed):
    instance, bits = instance_and_bits
    tables = build_repair_tables(instance)
    solution = repair(instance, bits, random.Random(seed), tables)  # noqa: S311 (test draws, not cryptography)
    assert is_feasible(instance, solution)


@given(instance_and_bits=instances_and_bits(), seed=st.integers(0, 1000))
def test_removing_any_aisle_after_repair_makes_the_solution_infeasible(
    instance_and_bits, seed
):
    instance, bits = instance_and_bits
    tables = build_repair_tables(instance)
    solution = repair(instance, bits, random.Random(seed), tables)  # noqa: S311 (test draws, not cryptography)
    for aisle in solution.aisles:
        other_aisles = [other for other in solution.aisles if other != aisle]
        assert not is_feasible(instance, replace(solution, aisles=other_aisles))


def test_repair_drops_orders_whose_item_lacks_stock():
    # Two orders want 3 units of item 0 each, but all aisles store only 4
    instance = Instance(
        orders=[{0: 3}, {0: 3}],
        aisles=[{0: 4}],
        n_items=1,
        wave_min_units=1,
        wave_max_units=10,
    )
    tables = build_repair_tables(instance)
    solution = repair(instance, [1, 1], random.Random(0), tables)  # noqa: S311 (test draws, not cryptography)
    assert len(solution.orders) == 1
    assert is_feasible(instance, solution)


def test_repair_restarts_from_an_empty_wave_when_the_lower_limit_is_out_of_reach():
    # Order 0 uses the only unit of item 0 that order 1 also needs, and order 0
    # alone stays below the lower limit, so the selected wave is a dead end. The
    # restart draws the orders again, and with seed 1 it tries order 1 first
    instance = Instance(
        orders=[{0: 1}, {0: 1, 1: 2}],
        aisles=[{0: 1, 1: 2}],
        n_items=2,
        wave_min_units=3,
        wave_max_units=3,
    )
    tables = build_repair_tables(instance)
    solution = repair(instance, [1, 0], random.Random(1), tables)  # noqa: S311 (test draws, not cryptography)
    assert solution == Solution(orders=[1], aisles=[0])


def test_same_seed_gives_same_solution():
    parameters = {
        "population_size": 10,
        "tournament_size": 3,
        "mutation_rate": 0.1,
        "seed": 7,
        "time_limit_seconds": 5,
    }
    first_solution, _ = solve(EXAMPLE_INSTANCE, parameters)
    second_solution, _ = solve(EXAMPLE_INSTANCE, parameters)
    assert first_solution == second_solution


def test_solve_runs_generations_and_records_an_increasing_history():
    parameters = {
        "population_size": 10,
        "tournament_size": 3,
        "mutation_rate": 0.1,
        "seed": 1,
        "time_limit_seconds": 5.2,
    }
    solution, report = solve(EXAMPLE_INSTANCE, parameters)
    objectives = [objective for _, objective in report["history"]]
    assert is_feasible(EXAMPLE_INSTANCE, solution)
    assert report["generations"] > 0
    assert objectives == sorted(set(objectives))
    assert report["best_found_seconds"] == report["history"][-1][0]

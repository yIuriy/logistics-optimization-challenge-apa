import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from order_selection.genetic_algorithm import build_arrays, evaluate, solve
from order_selection.instance import Instance, Solution, is_feasible, objective

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

PARAMETERS = {
    "population_size": 10,
    "tournament_size": 3,
    "mutation_rate": 0.1,
    "max_generations": 20,
    "seed": 7,
    "time_limit_seconds": 600,
}


@st.composite
def instances_and_bits(draw):
    """Draw a small instance with random limits and stock, and random aisle bits."""
    n_items = draw(st.integers(min_value=1, max_value=4))
    item_units = st.dictionaries(
        st.integers(min_value=0, max_value=n_items - 1),
        st.integers(min_value=1, max_value=5),
        min_size=1,
    )
    orders = draw(st.lists(item_units, min_size=1, max_size=8))
    wave_min_units = draw(st.integers(min_value=1, max_value=20))
    instance = Instance(
        orders=orders,
        aisles=draw(st.lists(item_units, min_size=1, max_size=5)),
        n_items=n_items,
        wave_min_units=wave_min_units,
        wave_max_units=draw(st.integers(min_value=wave_min_units, max_value=40)),
    )
    n_aisles = len(instance.aisles)
    bits = draw(st.lists(st.booleans(), min_size=n_aisles, max_size=n_aisles))
    return instance, bits


def evaluate_aisles(instance, aisles):
    """Decode the given aisles and return the fitness and the solution."""
    chromosome = np.zeros(len(instance.aisles), dtype=bool)
    chromosome[aisles] = True
    fitness, orders = evaluate(instance, build_arrays(instance), chromosome)
    solution = None if orders is None else Solution(sorted(orders.tolist()), aisles)
    return fitness, solution


@given(instance_and_bits=instances_and_bits())
def test_decoded_wave_is_feasible_exactly_when_the_fitness_is_positive(
    instance_and_bits,
):
    instance, bits = instance_and_bits
    aisles = [aisle for aisle, bit in enumerate(bits) if bit]
    fitness, solution = evaluate_aisles(instance, aisles)
    if fitness > 0:
        assert is_feasible(instance, solution)
        assert fitness == objective(instance, solution)
    else:
        assert solution is None


def test_decoder_serves_disputed_stock_by_order_priority():
    # Aisle 0 holds 5 units of item 0, so only one of the orders of 3 and 4 fits
    # and the larger order of 4 comes first
    instance = Instance(
        orders=[{0: 3}, {0: 4}, {1: 1}],
        aisles=[{0: 5, 1: 1}],
        n_items=2,
        wave_min_units=1,
        wave_max_units=10,
    )
    fitness, solution = evaluate_aisles(instance, [0])
    assert solution == Solution(orders=[1, 2], aisles=[0])
    assert fitness == 5


def test_decoder_stops_adding_orders_at_the_upper_limit():
    instance = Instance(
        orders=[{0: 2}, {0: 2}, {0: 2}],
        aisles=[{0: 9}],
        n_items=1,
        wave_min_units=1,
        wave_max_units=5,
    )
    fitness, solution = evaluate_aisles(instance, [0])
    assert solution == Solution(orders=[0, 1], aisles=[0])
    assert fitness == 4


def test_same_seed_gives_same_solution():
    first_solution, first_report = solve(EXAMPLE_INSTANCE, PARAMETERS)
    second_solution, second_report = solve(EXAMPLE_INSTANCE, PARAMETERS)
    assert first_solution == second_solution
    assert first_report["generations"] == second_report["generations"] == 20


def test_solve_returns_a_feasible_solution_and_an_increasing_history():
    solution, report = solve(EXAMPLE_INSTANCE, PARAMETERS)
    objectives = [objective for _, objective in report["history"]]
    assert solution is not None
    assert is_feasible(EXAMPLE_INSTANCE, solution)
    assert objectives == sorted(set(objectives))
    assert report["best_found_seconds"] == report["history"][-1][0]


def test_solve_stops_at_the_time_limit():
    parameters = {**PARAMETERS, "max_generations": 10**9, "time_limit_seconds": 5.2}
    _, report = solve(EXAMPLE_INSTANCE, parameters)
    assert report["generations"] < 10**9


def test_limit_shorter_than_the_margin_still_runs_generations():
    parameters = {**PARAMETERS, "max_generations": 10**9, "time_limit_seconds": 1}
    solution, report = solve(EXAMPLE_INSTANCE, parameters)
    assert 0 < report["generations"] < 10**9
    assert solution is not None

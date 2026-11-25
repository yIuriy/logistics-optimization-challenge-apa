"""Genetic algorithm over aisles with a penalty for short waves (issue #13).

The chromosome is a NumPy boolean vector with one bit per aisle, where bit 1
means the wave visits that aisle. The number of visited aisles is the
denominator of the objective, so the search controls it directly. The
evaluation decodes the chromosome into a wave by adding the orders that the
stock of the visited aisles can serve, up to the upper limit. A wave below the
lower limit gets a negative fitness, so the selection pushes the population
toward feasible waves. Every step of the evaluation is a NumPy vector operation.
"""

import time
from dataclasses import dataclass

import numpy as np

from order_selection.instance import Instance, Solution

# Stopping this many seconds before the time limit, to leave time to write the output
SAFETY_MARGIN_SECONDS = 5


@dataclass
class InstanceArrays:
    """The instance as flat NumPy arrays, built once per run.

    Each order line (one item of one order) is an entry. The entries are sorted
    by item and, inside one item, by the priority of their order, and
    ``item_group_start`` gives the position of the first entry of the same item.
    ``priority`` lists the orders from the most units to the fewest. Each aisle
    line (one item stored in one aisle) is a stock entry.
    """

    entry_order: np.ndarray
    entry_item: np.ndarray
    entry_units: np.ndarray
    item_group_start: np.ndarray
    order_units: np.ndarray
    priority: np.ndarray
    stock_aisle: np.ndarray
    stock_item: np.ndarray
    stock_units: np.ndarray


def build_arrays(instance: Instance) -> InstanceArrays:
    """Flatten orders and aisles into entries and sort the order entries."""
    entry_order, entry_item, entry_units = np.array(
        [
            (order, item, units)
            for order, requested_units in enumerate(instance.orders)
            for item, units in requested_units.items()
        ],
        dtype=np.int64,
    ).T
    stock_aisle, stock_item, stock_units = np.array(
        [
            (aisle, item, units)
            for aisle, stored_units in enumerate(instance.aisles)
            for item, units in stored_units.items()
        ],
        dtype=np.int64,
    ).T.reshape(3, -1)
    order_units = np.bincount(
        entry_order, weights=entry_units, minlength=len(instance.orders)
    ).astype(np.int64)
    priority = np.argsort(-order_units, kind="stable")
    rank = np.empty_like(priority)
    rank[priority] = np.arange(len(priority))

    # Sorting the entries by item, then by order priority, and marking where
    # each item's group starts, so a running sum can restart at every item
    by_item = np.lexsort((rank[entry_order], entry_item))
    entry_order, entry_item, entry_units = (
        entry_order[by_item],
        entry_item[by_item],
        entry_units[by_item],
    )
    starts_group = np.r_[True, entry_item[1:] != entry_item[:-1]]
    positions = np.arange(len(entry_item))
    item_group_start = np.maximum.accumulate(np.where(starts_group, positions, 0))
    return InstanceArrays(
        entry_order,
        entry_item,
        entry_units,
        item_group_start,
        order_units,
        priority,
        stock_aisle,
        stock_item,
        stock_units,
    )


def evaluate(
    instance: Instance, arrays: InstanceArrays, chromosome: np.ndarray
) -> tuple[float, np.ndarray | None]:
    """Decode the visited aisles into a wave and return its fitness and orders.

    The decoder goes through four vector steps. (1) It sums the stock of the
    visited aisles per item. (2) It keeps the orders whose every item fits in
    that stock on its own. (3) Inside each item, it adds the demand of those
    orders in priority order and drops each order that reaches an item after its
    stock ran out. (4) It keeps the accepted orders, in priority order, while the
    running total of units stays within the upper limit.

    Args:
        instance: The problem instance.
        arrays: The arrays built by ``build_arrays``.
        chromosome: One boolean per aisle, true for the visited aisles.

    Returns:
        For a wave that reaches the lower limit, the objective (units divided by
        visited aisles) and the orders of the wave. Otherwise, minus the units
        missing to reach the lower limit (at least one unit) and ``None``.
    """
    n_orders = len(instance.orders)
    capacity = np.bincount(
        arrays.stock_item,
        weights=arrays.stock_units * chromosome[arrays.stock_aisle],
        minlength=instance.n_items,
    )

    # Keeping the orders that fit alone, then the ones that still fit after
    # the orders of higher priority took their share of each item
    available = capacity[arrays.entry_item]
    fits_alone = arrays.entry_units <= available
    order_fits = np.bincount(arrays.entry_order, ~fits_alone, n_orders) == 0
    demand = arrays.entry_units * order_fits[arrays.entry_order]
    running = np.cumsum(demand)
    start = arrays.item_group_start
    item_running = running - running[start] + demand[start]
    out_of_stock = item_running > available
    order_fits &= np.bincount(arrays.entry_order, out_of_stock, n_orders) == 0

    # Keeping the accepted orders while the running total stays within the
    # upper limit, which takes the first ones in priority order
    accepted = order_fits[arrays.priority]
    units_in_order = arrays.order_units[arrays.priority] * accepted
    within_limit = np.cumsum(units_in_order) <= instance.wave_max_units
    orders = arrays.priority[accepted & within_limit]
    wave_units = int(arrays.order_units[orders].sum())

    shortfall = max(1, instance.wave_min_units) - wave_units
    if shortfall > 0:
        return -shortfall, None
    return wave_units / int(chromosome.sum()), orders


def solve(instance: Instance, parameters: dict) -> tuple[Solution | None, dict]:
    """Run the genetic algorithm for a number of generations and return the best wave.

    Each generation builds ``population_size`` children. A child takes two
    parents chosen by tournament, mixes them by uniform crossover, flips each
    aisle bit with probability ``mutation_rate`` and goes through ``evaluate``.
    The run stops after ``max_generations`` generations, or earlier when the
    clock reaches ``time_limit_seconds`` minus a safety margin. A limit shorter
    than the margin is used whole, as the exact algorithm does.

    The time complexity uses O orders, A aisles, I items, E order lines, S aisle
    lines and P individuals. The steps below are NumPy vector operations.

    - Crossover and mutation cost O(A) each.
    - Evaluation costs O(S + I) for the stock, O(E + O) to accept orders and
      O(O) for the upper limit.
    - One generation has P children, so it costs O(P * (A + S + I + E + O)).

    Args:
        instance: The problem instance.
        parameters: ``population_size``, ``tournament_size``, ``mutation_rate``,
            ``max_generations``, ``seed`` and ``time_limit_seconds``.

    Returns:
        The best feasible solution seen during the run, or ``None`` when no
        individual was feasible, and a dictionary with ``generations`` (complete
        generations), ``best_found_seconds`` and ``history``, the
        ``[seconds, objective]`` pairs recorded at each improvement.
    """
    start = time.perf_counter()

    # Keeping the safety margin only when the limit is longer than it, like the
    # exact algorithm, so a short limit still leaves time for generations
    time_limit = parameters["time_limit_seconds"]
    stop_after_seconds = (
        time_limit - SAFETY_MARGIN_SECONDS
        if time_limit > SAFETY_MARGIN_SECONDS
        else time_limit
    )
    rng = np.random.default_rng(parameters["seed"])
    population_size = parameters["population_size"]
    n_aisles = len(instance.aisles)
    arrays = build_arrays(instance)
    best_fitness, best_solution = 0.0, None
    history: list[list[float]] = []

    def evaluate_and_keep_best(chromosome: np.ndarray) -> float:
        # Evaluating the aisles and keeping the best feasible wave apart,
        # so no generation can lose it
        nonlocal best_fitness, best_solution
        fitness, orders = evaluate(instance, arrays, chromosome)
        if orders is not None and fitness > best_fitness:
            best_fitness = fitness
            aisles = np.flatnonzero(chromosome).tolist()
            best_solution = Solution(sorted(orders.tolist()), aisles)
            history.append([time.perf_counter() - start, best_fitness])
        return fitness

    # Giving each individual its own share of visited aisles, drawn between
    # none and all, so the first generation tries waves of every size
    share_of_aisles = rng.random((population_size, 1))
    population = rng.random((population_size, n_aisles)) < share_of_aisles
    fitness = np.array([evaluate_and_keep_best(bits) for bits in population])

    generations = 0
    while generations < parameters["max_generations"]:
        children = np.empty_like(population)
        children_fitness = np.empty(population_size)
        for child in range(population_size):
            if time.perf_counter() - start > stop_after_seconds:
                return best_solution, report(generations, history)

            # Choosing each parent as the fittest of a random tournament
            mother, father = (
                max(
                    rng.choice(
                        population_size, parameters["tournament_size"], replace=False
                    ),
                    key=lambda individual: fitness[individual],
                )
                for _ in range(2)
            )

            # Taking each bit from either parent with chance 1/2 (uniform
            # crossover), then flipping each bit with the mutation rate
            from_father = rng.random(n_aisles) < 0.5  # noqa: PLR2004 (half of the bits come from each parent)
            children[child] = np.where(
                from_father, population[father], population[mother]
            )
            children[child] ^= rng.random(n_aisles) < parameters["mutation_rate"]
            children_fitness[child] = evaluate_and_keep_best(children[child])

        population, fitness = children, children_fitness
        generations += 1
    return best_solution, report(generations, history)


def report(generations: int, history: list[list[float]]) -> dict:
    """Build the run summary that ``solve`` returns next to the solution."""
    return {
        "generations": generations,
        "best_found_seconds": history[-1][0] if history else None,
        "history": history,
    }

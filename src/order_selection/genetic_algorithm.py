"""Genetic algorithm with a repair step (issue #13).

The chromosome is a list of bits with one bit per order, where bit 1 puts the
order in the wave. The aisles stay out of the chromosome because the repair
chooses them from the orders, so every individual becomes a feasible solution.
"""

import random
import time
from dataclasses import dataclass

from order_selection.instance import Instance, Solution, objective

# Stopping this many seconds before the time limit, to leave time to write the output
SAFETY_MARGIN_SECONDS = 5


@dataclass(frozen=True)
class RepairTables:
    """Data the repair reads many times, computed once per instance."""

    order_units: list[int]
    item_stock: dict[int, int]
    aisles_by_item: dict[int, list[tuple[int, int]]]


def build_repair_tables(instance: Instance) -> RepairTables:
    """Compute the units of each order, the stock of each item and its aisles."""
    # Listing, for each item, the aisles that store it and how many units each has
    aisles_by_item: dict[int, list[tuple[int, int]]] = {}
    for aisle, stored_units in enumerate(instance.aisles):
        for item, units in stored_units.items():
            aisles_by_item.setdefault(item, []).append((aisle, units))

    return RepairTables(
        order_units=[sum(order.values()) for order in instance.orders],
        item_stock={
            item: sum(units for _, units in aisle_units)
            for item, aisle_units in aisles_by_item.items()
        },
        aisles_by_item=aisles_by_item,
    )


def repair(
    instance: Instance, bits: list[int], rng: random.Random, tables: RepairTables
) -> Solution:
    """Turn any bit vector into a feasible solution, in the four steps of issue #13.

    Args:
        instance: The problem instance.
        bits: One bit per order, where 1 means the order is in the wave.
        rng: The random generator of the run, so the same seed repeats the result.
        tables: The precomputed data of ``build_repair_tables``.

    Returns:
        The selected orders and the visited aisles. Removing any of these aisles
        leaves some requested item without enough stock.
    """
    # Removing random orders while the wave passes the upper limit (step 1)
    selected_orders = [order for order, bit in enumerate(bits) if bit]
    rng.shuffle(selected_orders)
    wave_units = sum(tables.order_units[order] for order in selected_orders)
    while wave_units > instance.wave_max_units:
        wave_units -= tables.order_units[selected_orders.pop()]

    # Adding orders up to the lower limit (step 2), and starting again from an
    # empty wave when the orders already selected leave no way to reach it
    selected_orders = drop_orders_without_stock(instance, selected_orders, tables)
    selected_orders = fill_up_to_lower_limit(instance, selected_orders, rng, tables)
    wave_units = sum(tables.order_units[order] for order in selected_orders)
    if wave_units < instance.wave_min_units:
        selected_orders = fill_up_to_lower_limit(instance, [], rng, tables)

    # Choosing aisles greedily (step 3), then dropping the unneeded ones (step 4)
    requested = requested_units(instance, selected_orders)
    aisles = choose_aisles(instance, requested, tables)
    aisles = drop_unneeded_aisles(instance, requested, aisles)
    return Solution(orders=sorted(selected_orders), aisles=sorted(aisles))


def requested_units(instance: Instance, orders: list[int]) -> dict[int, int]:
    """Return, item by item, the units the given orders request together."""
    requested: dict[int, int] = {}
    for order in orders:
        for item, units in instance.orders[order].items():
            requested[item] = requested.get(item, 0) + units
    return requested


def drop_orders_without_stock(
    instance: Instance, selected_orders: list[int], tables: RepairTables
) -> list[int]:
    """Remove orders while some item is requested beyond the stock of all aisles.

    Args:
        instance: The problem instance.
        selected_orders: The orders of the wave, already in random order.
        tables: The precomputed data of ``build_repair_tables``.

    Returns:
        The orders that remain, whose items all fit in the total stock.
    """
    requested = requested_units(instance, selected_orders)
    kept_orders = []
    for order in selected_orders:
        # Dropping the order when one of its items still lacks stock, so each
        # short item loses orders only until its demand fits the stock
        order_items = instance.orders[order]
        if any(
            requested[item] > tables.item_stock.get(item, 0) for item in order_items
        ):
            for item, units in order_items.items():
                requested[item] -= units
        else:
            kept_orders.append(order)
    return kept_orders


def fill_up_to_lower_limit(
    instance: Instance,
    selected_orders: list[int],
    rng: random.Random,
    tables: RepairTables,
) -> list[int]:
    """Add random orders until the wave reaches ``wave_min_units``.

    An order enters only when the wave stays within ``wave_max_units`` and every
    item it requests still fits in the total stock of the aisles.

    Args:
        instance: The problem instance.
        selected_orders: The orders already in the wave.
        rng: The random generator of the run.
        tables: The precomputed data of ``build_repair_tables``.

    Returns:
        The orders of the wave, which may still fall short of the lower limit
        when no remaining order fits.
    """
    requested = requested_units(instance, selected_orders)
    wave_units = sum(requested.values())
    already_selected = set(selected_orders)
    candidates = [
        order for order in range(len(instance.orders)) if order not in already_selected
    ]
    rng.shuffle(candidates)

    for order in candidates:
        if wave_units >= instance.wave_min_units:
            break
        order_items = instance.orders[order]
        fits_upper_limit = (
            wave_units + tables.order_units[order] <= instance.wave_max_units
        )
        if fits_upper_limit and all(
            requested.get(item, 0) + units <= tables.item_stock.get(item, 0)
            for item, units in order_items.items()
        ):
            selected_orders = [*selected_orders, order]
            wave_units += tables.order_units[order]
            for item, units in order_items.items():
                requested[item] = requested.get(item, 0) + units
    return selected_orders


def choose_aisles(
    instance: Instance, requested: dict[int, int], tables: RepairTables
) -> list[int]:
    """Choose, one at a time, the aisle that covers the most missing units.

    Args:
        instance: The problem instance.
        requested: The units the wave requests of each item.
        tables: The precomputed data of ``build_repair_tables``.

    Returns:
        The chosen aisles, in the order they were chosen.
    """
    missing = {item: units for item, units in requested.items() if units > 0}
    chosen_aisles: list[int] = []
    while missing:
        # Adding up, for each aisle not chosen yet, the missing units it covers,
        # where an aisle covers at most the units still missing of each item
        covered_units: dict[int, int] = {}
        for item, missing_units in missing.items():
            for aisle, units in tables.aisles_by_item[item]:
                if aisle not in chosen_aisles:
                    covered_units[aisle] = covered_units.get(aisle, 0) + min(
                        missing_units, units
                    )

        # Taking the best aisle and keeping only the items it did not fully cover
        best_aisle = max(covered_units, key=covered_units.__getitem__)
        chosen_aisles.append(best_aisle)
        best_aisle_units = instance.aisles[best_aisle]
        missing = {
            item: missing_units - best_aisle_units.get(item, 0)
            for item, missing_units in missing.items()
            if missing_units > best_aisle_units.get(item, 0)
        }
    return chosen_aisles


def drop_unneeded_aisles(
    instance: Instance, requested: dict[int, int], aisles: list[int]
) -> list[int]:
    """Remove each aisle whose stock the wave does not need.

    The aisles chosen last are tried first. Once an aisle stays, it stays needed,
    because later removals only lower the stock of the remaining aisles.

    Args:
        instance: The problem instance.
        requested: The units the wave requests of each item.
        aisles: The aisles chosen by ``choose_aisles``.

    Returns:
        The aisles kept, where removing any one leaves some item short.
    """
    available = units_stored_in_aisles(instance, aisles)
    kept_aisles = []
    for aisle in reversed(aisles):
        stored_units = instance.aisles[aisle]
        if all(
            available[item] - units >= requested.get(item, 0)
            for item, units in stored_units.items()
        ):
            for item, units in stored_units.items():
                available[item] -= units
        else:
            kept_aisles.append(aisle)
    return kept_aisles


def units_stored_in_aisles(instance: Instance, aisles: list[int]) -> dict[int, int]:
    """Return, item by item, the units the given aisles store together."""
    available: dict[int, int] = {}
    for aisle in aisles:
        for item, units in instance.aisles[aisle].items():
            available[item] = available.get(item, 0) + units
    return available


def solve(instance: Instance, parameters: dict) -> tuple[Solution, dict]:
    """Run the genetic algorithm until the time limit and return the best solution.

    Each generation builds ``population_size`` children. A child takes two
    parents chosen by tournament, mixes them by uniform crossover, flips each
    bit with probability ``mutation_rate`` and goes through ``repair``.

    Time complexity, with O orders, A aisles, I items and P individuals:

    - Repair: steps 1 and 2 go through the bit vector and the requested items,
      O(O * I) in the worst case. Step 3 chooses at most A aisles, and each choice
      goes through the aisles of every missing item, O(A * I), so O(A² * I).
      Step 4 costs O(A * I). In total, O(O * I + A² * I).
    - One generation: P children, each with O(O) for crossover and mutation and
      one repair, so O(P * (O * I + A² * I)).

    Args:
        instance: The problem instance.
        parameters: ``population_size``, ``tournament_size``, ``mutation_rate``,
            ``seed`` and ``time_limit_seconds``.

    Returns:
        The best solution seen during the whole run, and a dictionary with
        ``generations`` (complete generations), ``best_found_seconds`` and
        ``history``, the ``[seconds, objective]`` pairs recorded at each
        improvement of the best solution.
    """
    start = time.perf_counter()
    stop_after_seconds = parameters["time_limit_seconds"] - SAFETY_MARGIN_SECONDS
    rng = random.Random(parameters["seed"])  # noqa: S311 (search heuristic, not cryptography)
    tables = build_repair_tables(instance)
    n_orders = len(instance.orders)

    # Starting each bit at 1 with the chance that puts the wave halfway between
    # the limits, so the individuals are born close to feasible
    middle_units = (instance.wave_min_units + instance.wave_max_units) / 2
    chance_of_one = min(1, middle_units / sum(tables.order_units))
    population = [
        evaluate(
            instance,
            [int(rng.random() < chance_of_one) for _ in range(n_orders)],
            rng,
            tables,
        )
        for _ in range(parameters["population_size"])
    ]
    best = max(population, key=fitness)
    history = [[time.perf_counter() - start, best[0]]]

    generations = 0
    while time.perf_counter() - start < stop_after_seconds:
        children = []
        for _ in range(parameters["population_size"]):
            # Choosing each parent as the fittest of a random tournament
            mother, father = (
                max(rng.sample(population, parameters["tournament_size"]), key=fitness)
                for _ in range(2)
            )

            # Taking each bit from either parent with the same chance (uniform
            # crossover), then flipping it with chance mutation_rate (mutation)
            child_bits = [
                (mother_bit if rng.random() < 0.5 else father_bit)  # noqa: PLR2004 (half of the bits come from each parent)
                ^ (rng.random() < parameters["mutation_rate"])
                for mother_bit, father_bit in zip(mother[1], father[1], strict=True)
            ]
            children.append(evaluate(instance, child_bits, rng, tables))

        population = children
        generations += 1
        champion = max(population, key=fitness)
        if champion[0] > best[0]:
            best = champion
            history.append([time.perf_counter() - start, best[0]])

    return best[2], {
        "generations": generations,
        "best_found_seconds": history[-1][0],
        "history": history,
    }


def evaluate(
    instance: Instance, bits: list[int], rng: random.Random, tables: RepairTables
) -> tuple[float, list[int], Solution]:
    """Repair the bits and return the fitness, the repaired bits and the solution."""
    solution = repair(instance, bits, rng, tables)
    repaired_bits = [0] * len(bits)
    for order in solution.orders:
        repaired_bits[order] = 1
    return objective(instance, solution), repaired_bits, solution


def fitness(individual: tuple[float, list[int], Solution]) -> float:
    """Return the objective value stored first in each individual."""
    return individual[0]

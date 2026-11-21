"""Instance and solution files of the wave order picking problem.

The file formats follow sections 3.1 and 3.2 of the official challenge rules.
The objective and the constraints follow the official problem description.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Instance:
    """Orders, aisles and wave size limits of one problem instance."""

    orders: list[dict[int, int]]
    aisles: list[dict[int, int]]
    n_items: int
    wave_min_units: int
    wave_max_units: int


@dataclass(frozen=True)
class Solution:
    """Indices of the selected orders and of the visited aisles."""

    orders: list[int]
    aisles: list[int]


def read_instance(path: Path) -> Instance:
    """Read an instance file in the format of section 3.1 of the official rules.

    Args:
        path: Path of the instance file.

    Returns:
        The instance, where ``orders[o][item]`` holds the units order ``o``
        requests and ``aisles[a][item]`` holds the units aisle ``a`` stores.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    n_orders, n_items, n_aisles = map(int, lines[0].split())
    last_line = n_orders + n_aisles + 1

    # Turning each order and aisle line into a dictionary from item to units,
    # skipping the leading count because the pairs already tell how many there are
    item_units = [
        dict(zip(numbers[1::2], numbers[2::2], strict=True))
        for numbers in (list(map(int, line.split())) for line in lines[1:last_line])
    ]

    wave_min_units, wave_max_units = map(int, lines[last_line].split())
    return Instance(
        orders=item_units[:n_orders],
        aisles=item_units[n_orders : n_orders + n_aisles],
        n_items=n_items,
        wave_min_units=wave_min_units,
        wave_max_units=wave_max_units,
    )


def read_solution(path: Path) -> Solution:
    """Read a solution file in the format of section 3.2 of the official rules."""
    numbers = list(map(int, path.read_text(encoding="utf-8").split()))
    n_orders = numbers[0]
    return Solution(
        orders=numbers[1 : n_orders + 1],
        aisles=numbers[n_orders + 2 :],
    )


def write_solution(solution: Solution, path: Path) -> None:
    """Write a solution file in the format of section 3.2 of the official rules."""
    lines = [
        len(solution.orders),
        *solution.orders,
        len(solution.aisles),
        *solution.aisles,
    ]
    path.write_text("".join(f"{number}\n" for number in lines), encoding="utf-8")


def objective(instance: Instance, solution: Solution) -> float:
    """Return the units of the selected orders divided by the visited aisles."""
    units = sum(sum(instance.orders[order].values()) for order in solution.orders)
    return units / len(solution.aisles)


def is_feasible(instance: Instance, solution: Solution) -> bool:
    """Check constraints (2), (3) and (4) of the official description.

    Args:
        instance: The problem instance.
        solution: The selected orders and visited aisles.

    Returns:
        True when the wave units lie between the limits, at least one aisle is
        visited, and the visited aisles store every unit the orders request.
    """
    # Summing, item by item, what the selected orders request
    requested: dict[int, int] = {}
    for order in solution.orders:
        for item, units in instance.orders[order].items():
            requested[item] = requested.get(item, 0) + units

    # Summing, item by item, what the visited aisles store
    available: dict[int, int] = {}
    for aisle in solution.aisles:
        for item, units in instance.aisles[aisle].items():
            available[item] = available.get(item, 0) + units

    wave_units = sum(requested.values())
    return (
        instance.wave_min_units <= wave_units <= instance.wave_max_units
        and len(solution.aisles) >= 1
        and all(units <= available.get(item, 0) for item, units in requested.items())
    )

"""Runs every combination of instances, methods and parameters (issue #14).

A configuration file lists the instances, the methods and, for the genetic
algorithm, one list of values per parameter. The batch takes the Cartesian
product of these lists with ``itertools.product`` and runs each combination
once. The exact algorithm has no parameters besides the time limit, so it runs
once per instance. Each run writes the solution in the official format
(``.txt``) and a summary of the run (``.json``) next to it.
"""

import csv
import itertools
import json
import subprocess
import time
from pathlib import Path

from order_selection import exact_algorithm, genetic_algorithm
from order_selection.instance import (
    Instance,
    Solution,
    objective,
    read_instance,
    write_solution,
)

# Official best objectives, looked up by data set and original instance name
BEST_OBJECTIVES_PATH = Path(__file__).parents[2] / "data" / "best_objectives.csv"

SOLVERS = {"exact": exact_algorithm.solve, "genetic": genetic_algorithm.solve}

# Short name of each genetic parameter in the file name, in this order.
# max_generations stays out because it only matters when the time limit does not
TAG_PARTS = {
    "population_size": "pop",
    "tournament_size": "tour",
    "mutation_rate": "mut",
    "seed": "seed",
}


def run_batch(config_path: Path) -> list[Path]:
    """Run every combination of the configuration file.

    Args:
        config_path: JSON file with ``instances``, ``methods``,
            ``time_limit_seconds``, ``results_dir`` and the ``genetic`` lists.

    Returns:
        The paths of the ``.json`` files written, one per run.
    """
    config = json.loads(config_path.read_text(encoding="utf-8"))
    results_dir = Path(config["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for instance_name, method in itertools.product(
        config["instances"], config["methods"]
    ):
        for parameters in parameter_combinations(config, method):
            written.append(
                run_one(Path(instance_name), method, parameters, results_dir)
            )
    return written


def parameter_combinations(config: dict, method: str) -> list[dict]:
    """Return one parameter dictionary per combination of the method's lists.

    Args:
        config: The parsed configuration file.
        method: ``exact`` or ``genetic``.

    Returns:
        A single dictionary with the time limit for the exact algorithm, or one
        dictionary per element of the product of the ``genetic`` lists.
    """
    time_limit = {"time_limit_seconds": config["time_limit_seconds"]}
    if method == "exact":
        return [time_limit]

    # Crossing every value of every genetic parameter with every other
    names = list(config["genetic"])
    return [
        dict(zip(names, values, strict=True)) | time_limit
        for values in itertools.product(*config["genetic"].values())
    ]


def parameter_tag(parameters: dict) -> str:
    """Return the part of the file name that identifies the genetic parameters."""
    return "_".join(f"{short}{parameters[name]}" for name, short in TAG_PARTS.items())


def run_one(
    instance_path: Path, method: str, parameters: dict, results_dir: Path
) -> Path:
    """Solve one instance with one method and write the ``.txt`` and ``.json``.

    Args:
        instance_path: Path of the instance file.
        method: ``exact`` or ``genetic``.
        parameters: Parameters passed to the solver, including
            ``time_limit_seconds``.
        results_dir: Directory where both files are written.

    Returns:
        The path of the ``.json`` file. The ``.txt`` is written only when the
        solver returned a solution.
    """
    instance = read_instance(instance_path)

    # Measuring the whole solver call, including building the model or the arrays
    start = time.perf_counter()
    solution, report = SOLVERS[method](instance, parameters)
    elapsed_seconds = time.perf_counter() - start

    stem = f"{instance_path.stem}_{method}"
    if method == "genetic":
        stem += f"_{parameter_tag(parameters)}"
    if solution is not None:
        write_solution(solution, results_dir / f"{stem}.txt")

    summary = build_summary(instance_path, instance, method, parameters, solution)
    summary |= method_fields(method, report, elapsed_seconds)
    json_path = results_dir / f"{stem}.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return json_path


def build_summary(
    instance_path: Path,
    instance: Instance,
    method: str,
    parameters: dict,
    solution: Solution | None,
) -> dict:
    """Build the ``.json`` fields that both methods share.

    Args:
        instance_path: Path of the instance file, used for its name.
        instance: The instance that was solved.
        method: ``exact`` or ``genetic``.
        parameters: Parameters passed to the solver.
        solution: The solution found, or ``None``.

    Returns:
        The instance sizes, the method, the parameters, the commit, the
        objective and its percentage of the official best value.
    """
    best = best_official(instance_path.stem)
    value = objective(instance, solution) if solution is not None else None
    return {
        "instance": instance_path.stem,
        "n_orders": len(instance.orders),
        "n_items": instance.n_items,
        "n_aisles": len(instance.aisles),
        "wave_min_units": instance.wave_min_units,
        "wave_max_units": instance.wave_max_units,
        "method": method,
        "parameters": parameters,
        "source_commit": source_commit(),
        "objective": value,
        "aisles_visited": len(solution.aisles) if solution is not None else None,
        "best_official": best,
        "percent_of_best": (
            round(100 * value / best, 2) if value is not None and best else None
        ),
    }


def method_fields(method: str, report: dict, elapsed_seconds: float) -> dict:
    """Return the ``.json`` fields that only one of the methods has."""
    if method == "exact":
        return {
            "lower_bound": report["objective_lower_bound"],
            "upper_bound": report["objective_upper_bound"],
            "status": report["status"],
            "elapsed_seconds": round(elapsed_seconds, 3),
        }
    best_found = report["best_found_seconds"]
    return {
        "generations": report["generations"],
        "best_found_seconds": round(best_found, 3) if best_found is not None else None,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "history": report["history"],
    }


def best_official(instance_name: str) -> float | None:
    """Return the official best objective of ``b_instance_0001``-style names."""
    dataset, _, original_name = instance_name.partition("_")
    with BEST_OBJECTIVES_PATH.open(encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["dataset"] == dataset and row["instance"] == f"{original_name}.txt":
                return float(row["best_objective"])
    return None


def source_commit() -> str | None:
    """Return the short hash of the current commit, or ``None`` outside git."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607 (git is on PATH)
            capture_output=True,
            text=True,
            check=True,
            cwd=BEST_OBJECTIVES_PATH.parent,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()

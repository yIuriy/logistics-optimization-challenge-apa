import json
from pathlib import Path

from order_selection.charts import evolution_picks, main

MAIN_FIGURES = {
    "percent_by_instance.png",
    "mean_by_dataset.png",
    "distance_to_optimum.png",
    "genetic_evolution.png",
    "complexity.png",
}


def genetic_run(instance: str, n_orders: int, mutation_rate: float = 0.01) -> dict:
    return {
        "instance": instance,
        "method": "genetic",
        "n_orders": n_orders,
        "parameters": {"population_size": 10, "mutation_rate": mutation_rate},
        "objective": 9.0,
        "best_official": 10.0,
        "percent_of_best": 90.0,
        "generations": 4,
        "elapsed_seconds": 2.0,
        "history": [[0.1, 5.0], [1.0, 9.0]],
    }


def exact_run(instance: str, solved: bool) -> dict:
    return {
        "instance": instance,
        "method": "exact",
        "n_orders": 3,
        "parameters": {"time_limit_seconds": 5},
        "objective": 8.0 if solved else None,
        "best_official": 10.0,
        "percent_of_best": 80.0 if solved else None,
        "lower_bound": 8.0 if solved else None,
        "upper_bound": 12.0 if solved else None,
    }


def write_runs(directory: Path, runs: list[dict]) -> None:
    for index, run in enumerate(runs):
        path = directory / f"{run['instance']}_{index}.json"
        path.write_text(json.dumps(run), encoding="utf-8")


def test_main_draws_every_chart_of_a_small_batch(tmp_path):
    write_runs(
        tmp_path,
        [
            genetic_run("b_instance_0001", 3),
            exact_run("b_instance_0001", solved=True),
            genetic_run("x_instance_0001", 7),
            exact_run("x_instance_0001", solved=False),
        ],
    )

    main(tmp_path)

    written = {path.name for path in (tmp_path / "figures").glob("*.png")}
    assert written == MAIN_FIGURES


def test_main_adds_the_sensitivity_map_when_parameters_vary(tmp_path):
    write_runs(
        tmp_path,
        [
            genetic_run("b_instance_0001", 3, mutation_rate=0.01),
            genetic_run("b_instance_0001", 3, mutation_rate=0.05),
        ],
    )

    main(tmp_path)

    assert (tmp_path / "figures" / "sensitivity.png").exists()


def test_evolution_picks_the_smallest_and_largest_instance_of_each_set():
    grouped = {
        name: {"genetic": genetic_run(name, size)}
        for name, size in [
            ("b_instance_0001", 50),
            ("b_instance_0002", 10),
            ("b_instance_0003", 30),
            ("x_instance_0001", 5),
        ]
    }

    picks = [run["instance"] for run in evolution_picks(grouped)]

    assert picks == ["b_instance_0002", "b_instance_0001", "x_instance_0001"]

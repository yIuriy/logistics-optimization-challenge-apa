import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from order_selection.batch_runner import (
    best_official,
    parameter_combinations,
    parameter_tag,
    run_batch,
    run_one,
)

ROOT = Path(__file__).parents[1]
CHECKER = ROOT / "src" / "order_selection" / "checker.py"

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

GENETIC_LISTS = {
    "population_size": [6],
    "tournament_size": [2],
    "mutation_rate": [0.05, 0.1],
    "max_generations": [5],
    "seed": [1],
}


def write_example(directory: Path, name: str = "b_instance_9999") -> Path:
    path = directory / f"{name}.txt"
    path.write_text(EXAMPLE_INSTANCE_TEXT, encoding="utf-8")
    return path


def write_config(directory: Path, instances: list[Path], methods: list[str]) -> Path:
    config = {
        "instances": [str(path) for path in instances],
        "methods": methods,
        "time_limit_seconds": 30,
        "results_dir": str(directory / "results"),
        "genetic": GENETIC_LISTS,
    }
    path = directory / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def checker_accepts(instance_path: Path, solution_path: Path) -> bool:
    result = subprocess.run(  # noqa: S603 (runs the official checker on test files)
        [sys.executable, str(CHECKER), str(instance_path), str(solution_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return "Is solution feasible: True" in result.stdout


@given(
    st.dictionaries(
        st.sampled_from(["population_size", "tournament_size", "mutation_rate"]),
        st.lists(st.integers(1, 100), min_size=1, max_size=4, unique=True),
        min_size=1,
    )
)
def test_number_of_runs_is_product_of_list_sizes(lists):
    config = {"time_limit_seconds": 10, "genetic": lists}
    combinations = parameter_combinations(config, "genetic")
    assert len(combinations) == math.prod(len(values) for values in lists.values())
    assert all(c["time_limit_seconds"] == 10 for c in combinations)


def test_two_values_of_an_untagged_parameter_are_rejected():
    lists = GENETIC_LISTS | {"max_generations": [5, 10]}
    config = {"time_limit_seconds": 10, "genetic": lists}
    with pytest.raises(ValueError, match="max_generations"):
        parameter_combinations(config, "genetic")


def test_exact_algorithm_runs_once_and_ignores_genetic_lists():
    config = {"time_limit_seconds": 10, "genetic": GENETIC_LISTS}
    assert parameter_combinations(config, "exact") == [{"time_limit_seconds": 10}]


@given(
    st.tuples(st.integers(1, 500), st.integers(1, 10), st.floats(0, 1), st.integers()),
    st.tuples(st.integers(1, 500), st.integers(1, 10), st.floats(0, 1), st.integers()),
)
def test_parameter_tag_differs_for_different_parameters(first, second):
    names = ["population_size", "tournament_size", "mutation_rate", "seed"]
    tags = [
        parameter_tag(dict(zip(names, values, strict=True)))
        for values in (first, second)
    ]
    assert (tags[0] == tags[1]) == (first == second)


def test_parameter_tag_matches_existing_result_names():
    parameters = {
        "population_size": 50,
        "tournament_size": 3,
        "mutation_rate": 0.002,
        "max_generations": 1000000000,
        "seed": 1,
        "time_limit_seconds": 600,
    }
    assert parameter_tag(parameters) == "pop50_tour3_mut0.002_seed1"


def test_best_official_reads_csv():
    assert best_official("x_instance_0004") == 202.75
    assert best_official("example") is None


def test_run_one_writes_txt_and_json_that_checker_accepts(tmp_path):
    instance_path = write_example(tmp_path)
    parameters = {name: values[0] for name, values in GENETIC_LISTS.items()}
    parameters["time_limit_seconds"] = 30

    json_path = run_one(instance_path, "genetic", parameters, tmp_path)

    assert json_path.name == "b_instance_9999_genetic_pop6_tour2_mut0.05_seed1.json"
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["method"] == "genetic"
    assert summary["parameters"] == parameters
    assert summary["generations"] == 5
    assert summary["objective"] > 0
    assert checker_accepts(instance_path, json_path.with_suffix(".txt"))


def test_small_batch_writes_one_pair_per_run(tmp_path):
    instances = [write_example(tmp_path, "b_a"), write_example(tmp_path, "x_b")]
    config_path = write_config(tmp_path, instances, ["exact", "genetic"])

    written = run_batch(config_path)

    # Two instances times (one exact run plus two mutation rates)
    assert len(written) == 6
    for json_path in written:
        summary = json.loads(json_path.read_text(encoding="utf-8"))
        instance_path = tmp_path / f"{summary['instance']}.txt"
        assert checker_accepts(instance_path, json_path.with_suffix(".txt"))
        if summary["method"] == "exact":
            assert summary["status"] == "optimal"
            assert summary["lower_bound"] == summary["objective"]

import json
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from order_selection.cli import main, parse_config_path

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


def write_small_config(directory: Path) -> tuple[Path, Path, Path]:
    instance_path = directory / "b_instance_0001.txt"
    instance_path.write_text(EXAMPLE_INSTANCE_TEXT, encoding="utf-8")
    results_dir = directory / "results"
    config = {
        "instances": [str(instance_path)],
        "methods": ["genetic"],
        "time_limit_seconds": 30,
        "results_dir": str(results_dir),
        "genetic": {
            "population_size": [6],
            "tournament_size": [2],
            "mutation_rate": [0.05],
            "max_generations": [3],
            "seed": [1],
        },
    }
    config_path = directory / "run.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return instance_path, config_path, results_dir


@given(
    st.text(
        alphabet=st.characters(categories=("L", "N"), include_characters="_-./"),
        min_size=1,
        max_size=60,
    ).filter(lambda text: not text.startswith("-"))
)
def test_parse_config_path_returns_path_for_any_positional_argument(raw_path):
    assert parse_config_path([raw_path]) == Path(raw_path)


@pytest.mark.parametrize(
    "argv",
    [[], ["a.json", "b.json"], ["--unknown", "a.json"]],
)
def test_parse_config_path_rejects_missing_or_extra_arguments(argv):
    with pytest.raises(SystemExit) as error:
        parse_config_path(argv)
    assert error.value.code != 0


def test_help_shows_usage_in_one_line():
    result = subprocess.run(
        [sys.executable, "-m", "order_selection", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    usage_lines = [
        line for line in result.stdout.splitlines() if line.startswith("usage:")
    ]
    assert usage_lines == ["usage: python -m order_selection [-h] config"]


def test_module_cli_writes_valid_txt_and_json_pair(tmp_path):
    instance_path, config_path, results_dir = write_small_config(tmp_path)

    subprocess.run(  # noqa: S603 (invokes this package CLI with temporary test files)
        [sys.executable, "-m", "order_selection", str(config_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    stem = "b_instance_0001_genetic_pop6_tour2_mut0.05_seed1"
    solution_path = results_dir / f"{stem}.txt"
    json_path = results_dir / f"{stem}.json"
    assert solution_path.is_file()
    assert json_path.is_file()

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert "percent_of_best" in summary
    assert summary["objective"] > 0

    checker = subprocess.run(  # noqa: S603 (runs the official checker on test files)
        [sys.executable, str(CHECKER), str(instance_path), str(solution_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Is solution feasible: True" in checker.stdout


def test_main_runs_batch_from_argument_list(tmp_path):
    _, config_path, results_dir = write_small_config(tmp_path)

    main([str(config_path)])

    stem = "b_instance_0001_genetic_pop6_tour2_mut0.05_seed1"
    assert (results_dir / f"{stem}.txt").is_file()
    assert (results_dir / f"{stem}.json").is_file()

import json
import re
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from order_selection.results import (
    OVERALL,
    dataset_of,
    load_results,
    mean_percent_by_dataset,
    runs_by_instance,
)

ROOT = Path(__file__).parents[1]
SUMMARY_ROW = re.compile(
    r"^\| \**(Conjunto (\w)|Geral)[^|]*\| \**([\d.]+)%\** \| \**([\d.]+)%"
)


def make_run(instance: str, method: str, percent: float | None) -> dict:
    return {"instance": instance, "method": method, "percent_of_best": percent}


def summary_means(summary_path: Path) -> dict[str, dict[str, float]]:
    """Read the mean table of summary.md as {group: {method: mean}}."""
    means = {}
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        match = SUMMARY_ROW.match(line)
        if match:
            group = match.group(2) or OVERALL
            means[group] = {
                "genetic": float(match.group(3)),
                "exact": float(match.group(4)),
            }
    return means


def test_means_match_the_final_summary_table():
    results = load_results(ROOT / "results")
    if not results:
        pytest.skip("results/ has no batch to compare")

    expected = summary_means(ROOT / "results" / "summary.md")
    computed = mean_percent_by_dataset(results)

    assert set(expected) == set(computed)
    for group, methods in expected.items():
        for method, mean in methods.items():
            assert computed[group][method] == pytest.approx(mean, abs=0.005)


def test_means_on_a_small_set_of_example_files(tmp_path):
    runs = [
        make_run("b_instance_0001", "genetic", 100.0),
        make_run("b_instance_0001", "exact", 50.0),
        make_run("b_instance_0002", "genetic", 80.0),
        make_run("b_instance_0002", "exact", None),
        make_run("x_instance_0001", "genetic", 90.0),
    ]
    for index, run in enumerate(runs):
        (tmp_path / f"{index}.json").write_text(json.dumps(run), encoding="utf-8")

    means = mean_percent_by_dataset(load_results(tmp_path))

    assert means["B"] == {"genetic": 90.0, "exact": 25.0}
    assert means["X"] == {"genetic": 90.0, "exact": 0.0}
    assert means[OVERALL] == {"genetic": 90.0, "exact": 50.0 / 3}


def test_load_results_skips_subfolders(tmp_path):
    (tmp_path / "web").mkdir()
    run = make_run("b_instance_0001", "genetic", 1.0)
    (tmp_path / "web" / "run.json").write_text(json.dumps(run), encoding="utf-8")

    assert load_results(tmp_path) == []


def test_first_run_of_each_method_stays():
    first = make_run("b_instance_0001", "genetic", 10.0)
    second = make_run("b_instance_0001", "genetic", 20.0)

    assert runs_by_instance([first, second]) == {"b_instance_0001": {"genetic": first}}


def test_dataset_of_reads_the_prefix():
    assert dataset_of("b_instance_0001") == "B"
    assert dataset_of("x_instance_0015") == "X"
    assert dataset_of("a_instance_0001") is None


percents = st.one_of(st.none(), st.floats(min_value=0, max_value=100))


@given(st.lists(st.tuples(st.sampled_from("bx"), percents), min_size=1, max_size=20))
def test_mean_stays_between_zero_and_the_largest_percentage(entries):
    runs = [
        make_run(f"{prefix}_instance_{index:04d}", "genetic", percent)
        for index, (prefix, percent) in enumerate(entries)
    ]

    means = mean_percent_by_dataset(runs)
    largest = max((percent or 0.0) for _, percent in entries)

    for methods in means.values():
        assert 0.0 <= methods["genetic"] <= largest + 1e-9
        assert methods["exact"] == 0.0

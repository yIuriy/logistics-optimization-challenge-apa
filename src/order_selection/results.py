"""Reads the ``.json`` files of a batch and computes the numbers to compare (issue #17).

Each run of the batch runner (issue #14) writes one ``.json`` per instance and
method. This module loads those files and computes the averages that the charts
(issue #17) and the web interface (issue #18) show, so both read the same
numbers. A run without a solution counts as 0% of the official best value,
because the course scores an instance without a valid solution as zero.
"""

import json
from collections import defaultdict
from pathlib import Path

METHODS = ("genetic", "exact")

# Data sets in the order the charts show them, with the prefix of their file names
DATASETS = {"B": "b_", "X": "x_"}

# Name of the group that averages every instance of every data set
OVERALL = "Geral"


def load_results(results_dir: Path) -> list[dict]:
    """Return the content of every ``.json`` directly inside ``results_dir``.

    Subfolders are left out, so runs written elsewhere (for example by the web
    interface) do not mix with the batch. The files are read in name order,
    which keeps the charts the same from one call to the next.
    """
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(results_dir.glob("*.json"))
    ]


def dataset_of(instance_name: str) -> str | None:
    """Return ``B`` or ``X`` for ``b_instance_0001``-style names, else ``None``."""
    for dataset, prefix in DATASETS.items():
        if instance_name.startswith(prefix):
            return dataset
    return None


def runs_by_instance(results: list[dict]) -> dict[str, dict[str, dict]]:
    """Group the runs as ``{instance: {method: run}}``, sorted by instance name.

    When one instance has several runs of the same method, as in a sensitivity
    analysis, the first one in file name order stays, so the comparison uses a
    single run per method.
    """
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)
    for run in results:
        grouped[run["instance"]].setdefault(run["method"], run)
    return dict(sorted(grouped.items()))


def percent_or_zero(run: dict | None) -> float:
    """Return the run's percentage of the official best, or 0 without a solution."""
    if run is None or run["percent_of_best"] is None:
        return 0.0
    return run["percent_of_best"]


def mean_percent_by_dataset(results: list[dict]) -> dict[str, dict[str, float]]:
    """Average the percentage of the official best per data set and method.

    Args:
        results: The runs returned by ``load_results``.

    Returns:
        ``{group: {method: mean}}`` for the groups ``B``, ``X`` and ``Geral``,
        keeping only the groups that have instances. Every instance of a group
        counts once per method, and a missing run counts as 0%.
    """
    grouped = runs_by_instance(results)
    groups = {
        dataset: [name for name in grouped if dataset_of(name) == dataset]
        for dataset in DATASETS
    }
    groups[OVERALL] = [name for name in grouped if dataset_of(name) is not None]

    # Averaging over the instances of each group that has any
    return {
        group: {
            method: sum(percent_or_zero(grouped[name].get(method)) for name in names)
            / len(names)
            for method in METHODS
        }
        for group, names in groups.items()
        if names
    }

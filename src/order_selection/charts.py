"""Draws the result charts of the slides from the ``.json`` of a batch (issue #17).

Every chart reads the runs that ``results.load_results`` returns and writes one
PNG into ``results/figures/``. The comparison uses two references: the official
best values of ``data/best_objectives.csv`` (the target) and the lower and upper
bounds of the exact algorithm (how far from the optimum a solution can be).
Each method keeps the same color in every chart and in the slides.

Run with ``uv run python -m order_selection.charts``.
"""

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")  # Drawing to files only, so the module also runs without a display

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from order_selection.results import (
    DATASETS,
    METHODS,
    dataset_of,
    load_results,
    mean_percent_by_dataset,
    percent_or_zero,
    runs_by_instance,
)

# One fixed color per method, the same one used in the slides
COLORS = {"genetic": "#2a7ab0", "exact": "#e07b39", "official": "#2e8b57"}

LABELS = {
    "genetic": "algoritmo genético",
    "exact": "algoritmo exato",
    "official": "melhor oficial",
}

FIGURE_DPI = 150
BAR_WIDTH = 0.38

# Instances drawn in the evolution chart per data set: the smallest and the largest
EVOLUTION_PICKS = 2


def main(results_dir: Path) -> None:
    """Draw every chart from the ``.json`` in ``results_dir`` into ``figures/``."""
    results = load_results(results_dir)
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    grouped = runs_by_instance(results)
    save(plot_percent_by_instance(grouped), figures_dir / "percent_by_instance.png")
    save(plot_mean_by_dataset(results), figures_dir / "mean_by_dataset.png")
    save(plot_distance_to_optimum(grouped), figures_dir / "distance_to_optimum.png")
    save(plot_genetic_evolution(grouped), figures_dir / "genetic_evolution.png")
    save(plot_complexity(results), figures_dir / "complexity.png")

    # Drawing the sensitivity map only when the batch crossed several parameters
    sensitivity = plot_sensitivity(results)
    if sensitivity is not None:
        save(sensitivity, figures_dir / "sensitivity.png")


def save(figure: plt.Figure, path: Path) -> None:
    """Write the figure as PNG and free its memory."""
    figure.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(figure)


def instances_of(grouped: dict[str, dict[str, dict]], dataset: str) -> list[str]:
    """Return the instance names of one data set, in name order."""
    return [name for name in grouped if dataset_of(name) == dataset]


def plot_percent_by_instance(grouped: dict[str, dict[str, dict]]) -> plt.Figure:
    """Draw side by side bars of the percentage of the official best per instance.

    One panel per data set. A line marks 100%, and an instance where the exact
    algorithm found no solution shows "sem solução" in place of its bar.
    """
    figure, axes = plt.subplots(len(DATASETS), 1, figsize=(12, 8), squeeze=False)
    for ax, dataset in zip(axes[:, 0], DATASETS, strict=True):
        names = instances_of(grouped, dataset)
        positions = np.arange(len(names))
        for offset, method in zip((-0.5, 0.5), METHODS, strict=True):
            runs = [grouped[name].get(method) for name in names]
            x = positions + offset * BAR_WIDTH
            heights = [run_percent(run) for run in runs]
            ax.bar(x, heights, BAR_WIDTH, color=COLORS[method], label=LABELS[method])
            mark_missing(ax, x, heights)

        ax.axhline(100, color="black", linestyle="--", linewidth=1)
        ax.set_xticks(positions, [short_name(name) for name in names], rotation=45)
        ax.set_title(f"Conjunto {dataset}")
        ax.set_ylabel("% do melhor oficial")
        ax.set_ylim(0, 120)
    axes[0, 0].legend(loc="upper center", ncols=2)
    figure.suptitle("Porcentagem do melhor valor oficial por instância")
    figure.tight_layout()
    return figure


def run_percent(run: dict | None) -> float:
    """Return the run's percentage of the official best, or NaN when it has none."""
    if run is None or run["percent_of_best"] is None:
        return float("nan")
    return run["percent_of_best"]


def mark_missing(ax: Axes, x: np.ndarray, heights: list[float]) -> None:
    """Write "sem solução" over each position whose height is NaN."""
    for position, height in zip(x, heights, strict=True):
        if np.isnan(height):
            write_no_solution(ax, position)


def write_no_solution(ax: Axes, position: float) -> None:
    """Write "sem solução" near the bottom of the panel, above ``position``."""
    # Placing the text in panel coordinates on the vertical axis, so it stays
    # inside the panel on linear and logarithmic scales alike
    ax.text(
        position, 0.03, "sem solução", rotation=90, ha="center", va="bottom",
        fontsize=7, transform=ax.get_xaxis_transform(),
    )  # fmt: skip


def short_name(instance_name: str) -> str:
    """Turn ``b_instance_0001`` into ``b_0001`` for the axis labels."""
    return instance_name.replace("instance_", "")


def plot_mean_by_dataset(results: list[dict]) -> plt.Figure:
    """Draw one bar per method for B, X and the overall mean, with the values."""
    means = mean_percent_by_dataset(results)
    groups = list(means)
    positions = np.arange(len(groups))
    figure, ax = plt.subplots(figsize=(7, 4.5))
    for offset, method in zip((-0.5, 0.5), METHODS, strict=True):
        heights = [means[group][method] for group in groups]
        bars = ax.bar(
            positions + offset * BAR_WIDTH,
            heights,
            BAR_WIDTH,
            color=COLORS[method],
            label=LABELS[method],
        )
        ax.bar_label(bars, fmt="%.2f%%")

    ax.set_xticks(positions, [group_label(group) for group in groups])
    ax.set_ylabel("% do melhor oficial (média)")
    ax.set_ylim(0, 125)
    ax.set_title("Média da porcentagem do melhor valor oficial")
    ax.legend(loc="upper center", ncols=2)
    figure.tight_layout()
    return figure


def group_label(group: str) -> str:
    """Return ``Conjunto B`` for a data set and keep ``Geral`` as it is."""
    return f"Conjunto {group}" if group in DATASETS else group


def plot_distance_to_optimum(grouped: dict[str, dict[str, dict]]) -> plt.Figure:
    """Draw the exact algorithm's bound interval and the genetic and official points.

    A zero length interval means the exact algorithm proved the optimum. The
    vertical axis is logarithmic, because the upper bound can be a hundred
    times the objective.
    """
    figure, axes = plt.subplots(len(DATASETS), 1, figsize=(12, 8), squeeze=False)
    for ax, dataset in zip(axes[:, 0], DATASETS, strict=True):
        names = instances_of(grouped, dataset)
        for position, name in enumerate(names):
            draw_bounds(ax, position, grouped[name].get("exact"))
            genetic = grouped[name].get("genetic")
            if genetic is not None and genetic["objective"] is not None:
                ax.plot(position, genetic["objective"], "o", color=COLORS["genetic"])
            best = next(iter(grouped[name].values()))["best_official"]
            if best is not None:
                ax.plot(position, best, "_", color=COLORS["official"], markersize=14)

        ax.set_yscale("log")
        ax.set_xticks(range(len(names)), [short_name(n) for n in names], rotation=45)
        ax.set_title(f"Conjunto {dataset}")
        ax.set_ylabel("objetivo (escala log)")
    axes[0, 0].legend(handles=distance_legend(), loc="upper left", fontsize=8)
    figure.suptitle("Distância até o ótimo")
    figure.tight_layout()
    return figure


def draw_bounds(ax: Axes, position: int, exact: dict | None) -> None:
    """Draw the line from the exact lower bound to its upper bound."""
    if exact is None or exact["lower_bound"] is None:
        write_no_solution(ax, position)
        return
    ax.vlines(
        position, exact["lower_bound"], exact["upper_bound"], color=COLORS["exact"]
    )
    ax.plot(position, exact["lower_bound"], "v", color=COLORS["exact"], markersize=5)


def distance_legend() -> list:
    """Build the legend entries of the distance chart."""
    return [
        plt.Line2D(
            [], [], color=COLORS["exact"], marker="v",
            label="limites inferior e superior do algoritmo exato",
        ),
        plt.Line2D(
            [], [], color=COLORS["genetic"], marker="o", linestyle="",
            label=LABELS["genetic"],
        ),
        plt.Line2D(
            [], [], color=COLORS["official"], marker="_", linestyle="",
            markersize=14, label=LABELS["official"],
        ),
    ]  # fmt: skip


def evolution_picks(grouped: dict[str, dict[str, dict]]) -> list[dict]:
    """Return the genetic runs of the smallest and largest instance of each set."""
    picks = []
    for dataset in DATASETS:
        runs = [
            grouped[name]["genetic"]
            for name in instances_of(grouped, dataset)
            if grouped[name].get("genetic", {}).get("history")
        ]
        runs.sort(key=lambda run: run["n_orders"])
        if runs:
            picks += [runs[0], runs[-1]][: min(EVOLUTION_PICKS, len(runs))]
    return picks


def plot_genetic_evolution(grouped: dict[str, dict[str, dict]]) -> plt.Figure:
    """Draw the best objective over the seconds for a few genetic runs.

    Each panel is one instance, with a dashed line at the official best value.
    The time axis is logarithmic, because most improvements come in the first
    seconds and the rest of the run would hide them.
    """
    picks = evolution_picks(grouped)
    figure, axes = plt.subplots(
        1, max(1, len(picks)), figsize=(4 * max(1, len(picks)), 3.8), squeeze=False
    )
    for ax, run in zip(axes[0], picks, strict=False):
        seconds, values = zip(*run["history"], strict=True)
        # Extending the last value to the end of the run, to show the flat part
        seconds, values = [*seconds, run["elapsed_seconds"]], [*values, values[-1]]
        ax.step(seconds, values, where="post", color=COLORS["genetic"])
        if run["best_official"] is not None:
            ax.axhline(
                run["best_official"], color=COLORS["official"], linestyle="--",
                label=LABELS["official"],
            )  # fmt: skip
        ax.set_xscale("log")
        ax.set_title(f"{run['instance']} ({run['n_orders']} pedidos)", fontsize=9)
        ax.set_xlabel("segundos (escala log)")
    axes[0, 0].set_ylabel("melhor objetivo")
    axes[0, 0].legend(loc="lower right", fontsize=8)
    figure.suptitle("Evolução do algoritmo genético")
    figure.tight_layout()
    return figure


def seconds_per_generation(run: dict) -> float | None:
    """Return the run's seconds per complete generation, or ``None`` without any."""
    if not run.get("generations"):
        return None
    return run["elapsed_seconds"] / run["generations"]


def plot_complexity(results: list[dict]) -> plt.Figure:
    """Draw the seconds per generation against the number of orders.

    One generation costs O(P * (A + S + I + E + O)) (see ``genetic_algorithm``).
    With the population fixed, the time grows linearly with the size of the
    instance, so the chart adds a least squares line to compare against.
    """
    figure, ax = plt.subplots(figsize=(7, 4.5))
    points = []
    for dataset, marker in zip(DATASETS, ("o", "s"), strict=True):
        runs = [
            run
            for run in results
            if run["method"] == "genetic"
            and dataset_of(run["instance"]) == dataset
            and seconds_per_generation(run) is not None
        ]
        x = [run["n_orders"] for run in runs]
        y = [seconds_per_generation(run) for run in runs]
        ax.scatter(
            x, y, marker=marker, color=COLORS["genetic"], label=f"Conjunto {dataset}"
        )
        points += zip(x, y, strict=True)

    # Fitting a straight line only when there are two different sizes to fit
    if len({x for x, _ in points}) > 1:
        x, y = np.array(points).T
        slope, intercept = np.polyfit(x, y, 1)
        line_x = np.linspace(x.min(), x.max(), 50)
        ax.plot(
            line_x,
            slope * line_x + intercept,
            "--",
            color="gray",
            label="ajuste linear",
        )

    ax.set_xlabel("número de pedidos")
    ax.set_ylabel("segundos por geração")
    ax.set_title("Complexidade na prática do algoritmo genético")
    ax.legend()
    figure.tight_layout()
    return figure


def plot_sensitivity(results: list[dict]) -> plt.Figure | None:
    """Draw the mean percentage of the best per population size and mutation rate.

    Returns:
        The heat map, or ``None`` when the batch tried a single pair, because a
        map with one cell says nothing.
    """
    cells: dict[tuple[int, float], list[float]] = {}
    for run in results:
        if run["method"] != "genetic":
            continue
        key = (run["parameters"]["population_size"], run["parameters"]["mutation_rate"])
        cells.setdefault(key, []).append(percent_or_zero(run))
    if len(cells) < 2:  # noqa: PLR2004 (a map needs at least two cells)
        return None

    sizes = sorted({size for size, _ in cells})
    rates = sorted({rate for _, rate in cells})
    grid = np.full((len(sizes), len(rates)), np.nan)
    for (size, rate), values in cells.items():
        grid[sizes.index(size), rates.index(rate)] = sum(values) / len(values)

    figure, ax = plt.subplots(figsize=(6, 4.5))
    image = ax.imshow(grid, cmap="viridis", aspect="auto")
    for row, col in np.argwhere(~np.isnan(grid)):
        ax.text(
            col, row, f"{grid[row, col]:.1f}", ha="center", va="center", color="white"
        )
    ax.set_xticks(range(len(rates)), [str(rate) for rate in rates])
    ax.set_yticks(range(len(sizes)), [str(size) for size in sizes])
    ax.set_xlabel("taxa de mutação")
    ax.set_ylabel("tamanho da população")
    ax.set_title("Análise de sensibilidade do algoritmo genético")
    figure.colorbar(image, label="% do melhor oficial (média)")
    figure.tight_layout()
    return figure


if __name__ == "__main__":
    main(Path("results"))

# logistics-optimization-challenge-apa

Solver for the **Wave Order Picking** problem of the [SBPO 2025 / Mercado Livre optimization challenge](https://github.com/mercadolibre/challenge-sbpo-2025), developed for the APA course (Algorithm Design and Analysis).

**Goal:** choose a subset of orders (the _wave_) and a subset of warehouse aisles that maximize _units picked per aisle visited_, respecting the wave size limits and the stock of each item. Details in [docs/problem.md](docs/problem.md).

**Approach:** an exact model solved by HiGHS with the Dinkelbach method as the reference, and a genetic algorithm with a repair step as the proposed solution. The full plan, with every decision, is in [docs/plano-implementacao.md](docs/plano-implementacao.md).

## Quick start

```bash
uv sync
uv run pytest
uv run python src/order_selection/checker.py <instance> <solution>
```

## Repository

```
src/order_selection/   package (instance files, exact model, genetic algorithm, batch runner, CLI)
tests/                 unit and property tests
data/                  the 30 instances of datasets B and X (prefix b_ or x_) and best_objectives.csv
configs/               batch configuration files
results/               one .txt and .json pair per run
docs/                  problem, plan, figures and official PDFs
```

Team workflow and rules: [docs/workflow.md](docs/workflow.md).

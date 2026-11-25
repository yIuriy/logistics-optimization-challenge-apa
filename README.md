# logistics-optimization-challenge-apa

Solver for the **Wave Order Picking** problem of the [SBPO 2025 / Mercado Livre optimization challenge](https://github.com/mercadolibre/challenge-sbpo-2025), developed for the APA course (Algorithm Design and Analysis).

**Goal:** choose a subset of orders (the _wave_) and a subset of warehouse aisles that maximize _units picked per aisle visited_, respecting the wave size limits and the stock of each item. Details in [docs/problem.md](docs/problem.md).

**Approach:** an exact algorithm solved by HiGHS with the Dinkelbach method as the reference, and a genetic algorithm that chooses aisles as the proposed solution. The full plan, with every decision, is in [docs/plano-implementacao.md](docs/plano-implementacao.md).

## Quick start

```bash
uv sync
uv run pytest
uv run python src/order_selection/checker.py <instance> <solution>
uv run python -m order_selection.charts   # PNG charts of results/ into results/figures/
```

## Web interface

```bash
cd frontend && npm ci && npm run build && cd ..
uv run python -m order_selection.server   # open http://localhost:8000
```

The page shows the final batch of `results/` and runs the genetic algorithm with parameters chosen on screen. Those runs go to `results/web/` (ignored by git), so they never overwrite the final batch. For development, `npm run dev` in `frontend/` forwards `/api` to the server on port 8000.

## Repository

```
src/order_selection/   package (instance files, exact algorithm, genetic algorithm, batch runner, CLI, charts, web server)
frontend/              React web interface (Vite, TypeScript, Recharts)
tests/                 unit and property tests
data/                  the 30 instances of datasets B and X (prefix b_ or x_) and best_objectives.csv
configs/               batch configuration files
results/               one .txt and .json pair per run
docs/                  problem, plan, figures and official PDFs
```

Team workflow and rules: [docs/workflow.md](docs/workflow.md).

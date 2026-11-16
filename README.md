# logistics-optimization-challenge-apa

Heuristic solver for the **Wave Order Picking** problem of the
[SBPO 2025 / Mercado Livre optimization challenge](https://github.com/mercadolibre/challenge-sbpo-2025),
developed for the APA course (Algorithm Design and Analysis).

**Goal:** choose a subset of orders (the *wave*) and a subset of warehouse aisles that
maximize *units picked per aisle visited*, respecting the wave size limits and the
stock of each item. Details in [docs/problem.md](docs/problem.md).

**Approach:** greedy construction (choose aisles → fill orders) + local search over
the aisle set. Details in [docs/strategy.md](docs/strategy.md).

**Status:** infrastructure ready (reading, validation, benchmark runner, tests); the
heuristic itself is being implemented — see [docs/issues.md](docs/issues.md).
Results appear in `results/summary.md` after the first `python -m wop.run`.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
pytest
python -m wop.run --time-limit 60  # solve all instances, keep the best solutions
python -m wop.check                # validate solutions/ with the official checker
```

## Repository

```
wop/            solver package (instance, solution, rankings, construct, local_search, solver, run, check)
tests/          unit tests (uses the 5x5x5 example from the problem description)
data/           official instances (datasets a, b, x) and best_objectives.csv  — read-only
tools/          official checker.py  — read-only
solutions/      best solution found for each instance
results/        comparison with the best known values
docs/           problem, strategy, team workflow, official PDFs
```

Team workflow and rules: [docs/workflow.md](docs/workflow.md).

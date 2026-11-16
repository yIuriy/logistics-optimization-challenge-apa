# CLAUDE.md

Course project (APA, UNIPAMPA): solve the SBPO 2025 / Mercado Livre **Wave Order
Picking** problem with a greedy + local search heuristic in Python. Five students,
11-day deadline, graded on solution quality vs. other groups **and** on each member
defending the code in a 5-minute presentation.

Read first: `docs/problem.md` (the problem), `docs/strategy.md` (our approach),
`docs/workflow.md` (team rules).

## Commands

```bash
pip install -r requirements.txt
pytest                                           # unit tests (fast)
python -m wop.run --instances a/instance_0003    # solve some instances
python -m wop.run --time-limit 60                # solve all 50, update solutions/ and results/
python -m wop.check                              # official checker over solutions/
```

## Layout

| Path | What |
|---|---|
| `wop/instance.py` | `Instance` + `read_instance` |
| `wop/solution.py` | `Solution`, `objective`, `violations`, solution file I/O |
| `wop/rankings.py` | ranking rules for orders / aisles (registries `ORDER_RANKINGS`, `AISLE_RANKINGS`) — stubs |
| `wop/construct.py` | `fill_orders` (aisles fixed → orders) and `greedy_prefix` (choose k) — stubs |
| `wop/local_search.py` | `improve` — local search over aisle sets — stub |
| `wop/solver.py` | pipeline: every ranking pair → best → `improve` |
| `wop/run.py`, `wop/check.py` | benchmark runner and final validation |
| `wop/official.py` | loads the untouched official checker from `tools/checker.py` |
| `data/` | official instances and `best_objectives.csv` (read-only) |
| `solutions/`, `results/` | best solutions found so far and the comparison table |

Status: only the infrastructure is done. Functions that raise
`NotImplementedError("issue: ...")` belong to an open issue (`docs/issues.md`);
their docstrings describe the intended algorithm.

## Hard rules

* **Do not modify `tools/checker.py` or `data/`.** They are the official files.
* A solution must pass the official checker; infeasible = zero points. Never write to
  `solutions/` by hand — only `wop.run` does it, and only when feasible and strictly better.
* Do not add a MIP solver or heavy dependency without the team asking for it. Current
  dependencies: `numpy`, `pytest`.
* Keep `solve(inst, time_limit, seed)` and `improve(inst, sol, order_rank, deadline)`
  signatures stable — other members build on them. Respect the deadline/time limit.

## How to help this team

* **The students must understand and defend the code.** Prefer short, readable loops
  over clever vectorization; add a docstring explaining the *idea* of each function.
  After a change, explain in plain words what it does and why it should improve the
  objective, so the member can present it.
* Measure before claiming an improvement: run `wop.run` on the affected instances with
  the same time limit and compare with `results/summary.md`.
* Make small changes scoped to one issue; add/adjust tests in `tests/`.
* Code, comments, docs and commit messages in **English**. The team speaks Portuguese:
  reply to them in Portuguese.

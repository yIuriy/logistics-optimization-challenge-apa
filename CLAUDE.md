# CLAUDE.md

Course project (APA, UNIPAMPA): solve the SBPO 2025 / Mercado Livre **Wave Order Picking** problem in Python with an exact algorithm (HiGHS and the Dinkelbach method) as the reference and a genetic algorithm as the proposed solution. Five students, graded on solution quality against other groups **and** on each member defending the code in a 5-minute presentation.

Read first: `docs/plano-implementacao.md` (every decision and the task split), `docs/problem.md` (the problem), `docs/workflow.md` (team rules). The course statement overrides the challenge rules. Where it says nothing, the challenge README and rules apply (official output format). The professor confirmed that the course evaluation has no time limit, so `time_limit_seconds` is a run parameter, set to 600 seconds in `configs/`.

## Commands

```bash
uv sync
uv run ruff check . && uv run complexipy . && uv run vulture . && uv run pytest
uv run python src/order_selection/checker.py <instance> <solution>
```

## Layout

| Path                                       | What                                                                     |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `src/order_selection/instance.py`          | `Instance`, `Solution`, file reading and writing, objective, feasibility |
| `src/order_selection/exact_algorithm.py`   | Dinkelbach with HiGHS (issue #12)                                        |
| `src/order_selection/genetic_algorithm.py` | genetic algorithm over aisles (issue #13)                                |
| `src/order_selection/batch_runner.py`      | runs every combination of a configuration file (issue #14)               |
| `src/order_selection/cli.py`               | command line interface (issue #15)                                       |
| `src/order_selection/checker.py`           | official checker, untouched                                              |
| `data/`                                    | official instances and `best_objectives.csv`, read-only                  |

## Hard rules

- **Do not modify `src/order_selection/checker.py` or `data/`.** They are the official files.
- A solution must pass the official checker. An infeasible solution scores zero.
- Every change keeps the objective (1), the constraints (2), (3) and (4) and the file formats of `docs/reference/pt_problem_description.pdf`, and the rules of the course statement (Moodle page). When a rule changes, the issue, `docs/plano-implementacao.md` and the code change in the same pull request.
- Portuguese text writes "algoritmo exato" and "algoritmo genético" in full, never "exato" or "genético" alone.
- Keep the `instance.py` interface stable, because every other module builds on it.
- Every random draw uses a seeded generator (`random.Random(seed)` or `np.random.default_rng(seed)`), and every duration uses `time.perf_counter()`.

## How to help this team

- **The students must understand and defend the code.** Prefer short, readable loops over clever tricks, and explain the idea of each function in its docstring.
- Make small changes scoped to one issue and add tests in `tests/`.
- Code, comments, docs and commit messages in **English**. The team speaks Portuguese, so reply to them in Portuguese.

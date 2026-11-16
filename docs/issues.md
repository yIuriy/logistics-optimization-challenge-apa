# Issue proposal (5 members, 11 days)

Everyone reads `docs/problem.md` + `docs/strategy.md` and runs the project on day 1.
Each member owns 1–2 issues, reviews one other member's PR, and must be able to
explain their part in the presentation.

Already done (infrastructure): instance reader, solution checks and file I/O, bridge to
the official checker, benchmark runner (`wop.run`), validation (`wop.check`), tests.

| # | Issue | Owner | Files | Depends on |
|---|---|---|---|---|
| 1 | Greedy construction (base heuristic) | Member 1 | `wop/construct.py`, `wop/rankings.py` | — |
| 2 | Local search over aisles | Member 1 | `wop/local_search.py` | 1 |
| 3 | New order ranking rules | Member 2 | `wop/rankings.py` (orders) | 1 |
| 4 | Adaptive aisle selection | Member 3 | `wop/rankings.py` (aisles), `wop/construct.py` | 1 |
| 5 | Multi-start / randomization (GRASP) + speed-up of `fill_orders` | Member 4 | `wop/solver.py`, `wop/construct.py` | 1 |
| 6 | Final benchmark + results charts | Member 5 | `wop/run.py`, `results/` | all |
| 7 | Presentation | Member 5 (lead) + all | slides | 6 |

Issue 1 is on the critical path: it should land in the first 2–3 days. Meanwhile the
others study the code, prepare their ideas, and Member 5 starts the presentation's
problem part (it does not depend on code).

Timeline: days 1–3 issue 1 · days 3–7 issues 2–5 · day 7 integration ·
days 8–9 long final runs (issue 6) · days 10–11 presentation rehearsal.

---

### 1. Greedy construction (base heuristic)
**Goal:** implement the stubs in `wop/construct.py` and `wop/rankings.py`
(their docstrings describe the algorithm; see also `docs/strategy.md`).
- `orders_by_units`: biggest orders first.
- `aisles_by_useful_stock`: aisles with most useful stock first.
- `fill_orders`: aisles fixed → take orders in ranking order while they fit in stock and ≤ UB.
- `greedy_prefix`: try the first k aisles for k = 1, 2, …, keep the best feasible ratio,
  with the UB / k pruning.
**Done when:** the two `xfail` tests in `tests/test_basics.py` pass (remove the markers),
`python -m wop.run` gives 50/50 feasible and `python -m wop.check` passes.
Target from the prototype: ~90% mean of best known, a few seconds per instance.
Commit the first `solutions/` and `results/` — this is the baseline for everybody else.

### 2. Local search over aisles
**Goal:** implement `improve()` in `wop/local_search.py`.
- Moves on the aisle set: **remove** one aisle, **add** one aisle, **swap** one in/one out.
  After each move re-fill orders with `fill_orders`; accept if feasible and the ratio improves.
- First-improvement is enough; stop at the deadline or when no move improves.
- On big instances limit candidates (e.g. only the top-N aisles by useful stock) to stay fast.
**Done when:** tests pass, every solution stays feasible, mean % on dataset A improves
(targets: `a/instance_0003`, `a/instance_0009`, `a/instance_0011`).

### 3. New order ranking rules
**Goal:** add rules to `ORDER_RANKINGS` (the solver tries every combination automatically).
Ideas: units per distinct item (compact orders first), orders whose items are scarce last,
orders using items from few aisles first, small orders first (helps reach LB with few aisles).
**Done when:** each rule is measured on all instances; keep the ones that improve some
instance, document the results in the PR.

### 4. Adaptive aisle selection
**Goal:** replace the fixed aisle order by a smarter construction.
- New `AISLE_RANKINGS` rules (e.g. stock of the items most demanded, distinct items covered).
- An adaptive greedy: start empty, at each step add the aisle that gives the best ratio
  after `fill_orders` (evaluate only the top-N candidates to stay fast).
**Done when:** measured on all instances, better than the baseline on dataset A.

### 5. Multi-start / randomization (GRASP) + speed-up
**Goal:** use the remaining time.
- In `solve()`, loop until the deadline: build a solution with randomized rankings
  (e.g. choose randomly among the top 3 candidates, using `seed`), run `improve`,
  keep the best. Results must be reproducible with the same seed.
- Multi-start calls `fill_orders` thousands of times; on 68k-order instances each call
  is slow. Profile and speed it up while keeping it readable (skip orders that use an
  item absent from the chosen aisles, precompute per-order data, ...). Report before/after
  on `x/instance_0014`.
**Done when:** with `--time-limit 60` the overall mean is ≥ the single-run result.

### 6. Final benchmark + results charts
**Goal:** run the final long benchmark (`--time-limit 300` or more), make sure
`python -m wop.check` passes with 50/50, and produce the comparison for the presentation:
table and a bar chart of `% of best known` per instance/dataset, plus "baseline vs. final".
**Done when:** `results/` has the final table and chart images, all solutions validated.

### 7. Presentation (5 min)
- 0:00–2:00 problem: the warehouse story + the 5×5 example (`docs/problem.md`), animated.
- 2:00–5:00 approach (construction → local search → multi-start) and results vs. best known.
- Each member prepares one slide/answer about their own issue for the Q&A.

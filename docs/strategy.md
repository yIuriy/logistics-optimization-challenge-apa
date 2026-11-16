# Strategy

We use a **greedy constructive heuristic followed by local search**, optionally
wrapped in random restarts (GRASP-like). No MIP solver: the team must be able to
explain every step during the presentation.

## Key observation

**Once the aisles are fixed, the rest is easy.** If we know which aisles we visit,
the denominator `|A'|` is fixed and we only need to pick orders that fit in the
stock of those aisles (a knapsack-like problem, solved greedily by `fill_orders`).
So the search really happens over **sets of aisles**; orders are derived from them.

## Pipeline (`wop/solver.py`)

```
for each aisle ranking × order ranking:          (wop/rankings.py)
    greedy_prefix  → candidate solution           (wop/construct.py)
keep the best candidate
local search on it until the deadline            (wop/local_search.py)
```

### 1. `fill_orders(aisles, order_rank)` — aisles fixed, choose orders
1. Sum the stock of the chosen aisles.
2. Walk through orders in ranking order (default: biggest first).
3. Take an order if all its items are still in stock **and** the wave stays ≤ UB;
   subtract its units from the stock.
4. The caller checks that the wave reached LB.

### 2. `greedy_prefix(aisle_rank, order_rank)` — choose how many aisles
Try the first `k` aisles of the ranking for `k = 1, 2, 3, …`, fill orders for
each, keep the best feasible ratio.

**Pruning:** with `k` aisles the ratio is at most `min(UB, stock of those k aisles) / k`.
Once `UB / k` cannot beat the best ratio found, no larger `k` can either, so we stop.
On large instances this stops after ~10 aisles, which is why it runs in seconds.

Steps 1 and 2 are issue "Greedy construction"; the function skeletons and
docstrings are already in `wop/construct.py` and `wop/rankings.py`.

### 3. Local search (to do — issue "Local search")
Moves over the aisle set, re-filling orders after each move:
* **remove** a visited aisle,
* **add** a non-visited aisle,
* **swap** a visited aisle for a non-visited one.

Accept a move if the solution stays feasible and the ratio improves; repeat until
no move helps or time runs out.

### 4. Diversification (to do — issue "Multi-start")
Randomize rankings slightly (e.g. pick among the top-3 candidates at random),
build + improve again, keep the best. Repeat until the time limit.

## Expected results (prototype measurement)

A throw-away prototype of steps 1 + 2 with one ranking pair (`useful_stock` +
`units_desc`) reached **mean 90.7% of the best known values, 50/50 feasible,
~5 s on the largest instance** — use it as the target for issue "Greedy construction".

Weak spots seen in the prototype: small dataset-A instances where LB forces many
aisles (e.g. `a/instance_0009` ≈ 41%, `a/instance_0003` ≈ 52%) — a fixed aisle order
picks poor aisles there. Local search and better aisle rules should fix most of it.

## Ideas backlog (not assigned)
* Exact MIP (Dinkelbach) with HiGHS on small instances, as a quality check.
* Order rules that favour orders using items already well covered by visited aisles.

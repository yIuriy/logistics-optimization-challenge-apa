# The problem: Wave Order Picking (SBPO 2025)

Official sources (Portuguese): `docs/reference/pt_problem_description.pdf`,
`docs/reference/pt_challenge_rules.pdf`. Reference results: `docs/reference/final_phase.pdf`
and `data/best_objectives.csv`.

## In plain words

A Mercado Livre warehouse has **aisles**, each holding some units of some items.
Customers place **orders** (a list of items and quantities) that wait in a **backlog**.
A picker will go out once and collect a group of orders, called a **wave**.

We must choose:

1. **which orders** go into the wave, and
2. **which aisles** the picker visits to collect them,

so that the picker collects **as many units as possible per aisle visited**.

## Formal model

| Symbol | Meaning |
|---|---|
| `O` | orders in the backlog |
| `A` | aisles |
| `u_oi` | units of item `i` requested by order `o` |
| `u_ai` | units of item `i` stored in aisle `a` |
| `LB`, `UB` | minimum / maximum total units in the wave |

Choose `O' ⊆ O` and `A' ⊆ A` to

```
maximize   ( Σ_{o∈O'} Σ_i u_oi ) / |A'|        (units per visited aisle)

subject to LB ≤ Σ_{o∈O'} Σ_i u_oi ≤ UB          (wave size)
           Σ_{o∈O'} u_oi ≤ Σ_{a∈A'} u_ai  ∀ i    (enough stock for every item)
```

Orders are all-or-nothing (no partial orders). There is no routing or distance:
the only cost is the **number** of aisles visited.

## Worked example (`data/instances/a/instance_0020.txt`)

5 orders, 5 items, 5 aisles, LB = 5, UB = 12.

| Wave (orders) | Aisles | Units | Objective |
|---|---|---|---|
| {0, 4} | {0, 1} | 5 | 2.5 |
| {0, 2, 3} | {1, 3, 4} | 12 | 4.0 |
| **{0, 1, 2, 4}** | **{1, 3}** | **10** | **5.0 (optimal)** |

The best wave is *not* the one with most units: it wins because it needs only two
aisles. That trade-off (more units vs. more aisles) is the heart of the problem.

## File formats

Instance:

```
<n_orders> <n_items> <n_aisles>
<k> <item> <qty> ... (k pairs)      one line per order
<k> <item> <qty> ... (k pairs)      one line per aisle
<LB> <UB>
```

Solution:

```
<number of orders>
<order index>        one per line
<number of aisles>
<aisle index>        one per line
```

## Instance sizes

| Dataset | Instances | Orders | Aisles |
|---|---|---|---|
| A | 20 | 5 – 12k | 5 – 413 |
| B | 15 | 1.8k – 45k | 163 – 483 |
| X | 15 | 2k – 68k | 164 – 483 |

## How we are graded (course assignment)

* Solution score = 10 × (our performance / best group in class).
* A solution rejected by the official checker (`src/order_selection/checker.py`) scores **zero** on that instance.
* 5-minute presentation: 2 min problem, 3 min approach + results vs. best known values.

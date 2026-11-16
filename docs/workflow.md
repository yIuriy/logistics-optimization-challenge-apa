# Team workflow

## Setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Daily loop

1. Create a branch for your issue: `git switch -c <issue-number>-short-name`.
2. Change code under `wop/`. Add or update a test in `tests/` when you add behaviour.
3. Try it quickly on a few instances:
   ```bash
   python -m wop.run --instances a/instance_0003 a/instance_0009 b/instance_0008 --time-limit 30
   ```
4. Run the full benchmark when you think it helps:
   ```bash
   python -m wop.run --time-limit 60
   ```
5. `pytest` and `python -m wop.check` must pass. Open a pull request; somebody else reviews it.

## Rules

* **Never edit** `tools/checker.py` or anything in `data/` — they are the official files.
* `solutions/` only ever improves: `wop.run` overwrites a file only when the new
  solution passes the official checker **and** has a strictly better objective.
  On a merge conflict in `solutions/`, keep the version with the higher objective
  (run `python -m wop.check` on both and compare), then re-run `python -m wop.run`
  to regenerate `results/`.
* Commit `solutions/` and `results/` together, so the table always matches the files.
* Keep the code simple. Every member must be able to explain every part during the
  presentation — prefer a clear loop over a clever trick.
* Every new idea is registered so it can be compared: a new ranking goes in
  `ORDER_RANKINGS` / `AISLE_RANKINGS`; record what helped (and what did not) in the PR.

## Measuring

`results/summary.md` reports, per dataset, the mean of `ours / best_known`.
When comparing two versions, use the same `--time-limit` and compare the summary.

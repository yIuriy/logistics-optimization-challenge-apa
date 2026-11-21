# Team workflow

## Setup

```bash
uv sync
uv run pytest
```

## Daily loop

1. Create a branch for your issue from `main`: `git switch -c <issue-number>-short-name main`.
2. Change code under `src/order_selection/`. Add or update a test in `tests/` when you add behaviour.
3. Before opening a pull request, run `uv run ruff check .`, `uv run complexipy .`, `uv run vulture .` and `uv run pytest`. All four must pass.
4. Open a pull request into `main`. Somebody else reviews it.

## Rules

- **Never edit** `src/order_selection/checker.py` or anything in `data/`. They are the official files.
- Every solution written to `results/` must pass the official checker.
- Keep the code simple. Every member must be able to explain every part during the presentation.
- Disagreements with a decision of `docs/plano-implementacao.md` go to the issue first, before the code changes.

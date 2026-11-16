"""Run the solver on many instances, validate, and keep the best solutions.

    python -m wop.run                         # all datasets
    python -m wop.run --datasets a            # only dataset A
    python -m wop.run --instances a/instance_0003 x/instance_0014
    python -m wop.run --time-limit 120 --jobs 6

For every instance:
  1. solve it;
  2. validate the result with the OFFICIAL checker;
  3. overwrite solutions/<dataset>/<instance>.txt only if the new solution is
     feasible AND strictly better than the one already saved.

Then rewrite results/results.csv and results/summary.md from the saved
solutions, comparing them with the reference values in data/best_objectives.csv.
"""

import argparse
import csv
import os
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from wop.instance import read_instance
from wop.official import ROOT, official_check
from wop.solver import solve
from wop.solution import objective, violations, write_solution

INSTANCES_DIR = ROOT / "data" / "instances"
SOLUTIONS_DIR = ROOT / "solutions"
RESULTS_DIR = ROOT / "results"
REFERENCE_CSV = ROOT / "data" / "best_objectives.csv"


def all_instances(datasets) -> list[str]:
    return [f"{ds}/{p.stem}" for ds in datasets for p in sorted((INSTANCES_DIR / ds).glob("*.txt"))]


def saved_value(key: str) -> float:
    """Objective of the solution already in solutions/ (0 if missing or infeasible)."""
    sol_file = SOLUTIONS_DIR / f"{key}.txt"
    if not sol_file.exists():
        return 0.0
    feasible, value = official_check(INSTANCES_DIR / f"{key}.txt", sol_file)
    return value if feasible else 0.0


def run_one(key: str, time_limit: float, seed: int) -> dict:
    inst_file = INSTANCES_DIR / f"{key}.txt"
    start = time.perf_counter()
    inst = read_instance(inst_file)
    try:
        sol = solve(inst, time_limit=time_limit, seed=seed)
    except Exception as exc:  # keep the benchmark going; report the error for this instance
        sol, error = None, f"ERROR {type(exc).__name__}: {exc}"
    else:
        error = "no solution"
    elapsed = time.perf_counter() - start

    row = {"instance": key, "run_value": 0.0, "time_s": round(elapsed, 2), "status": error}
    if sol is None:
        return row
    problems = violations(inst, sol)
    if problems:
        row["status"] = "INFEASIBLE (own check): " + "; ".join(problems)
        return row

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp) / "sol.txt"
        write_solution(tmp_file, sol)
        feasible, value = official_check(inst_file, tmp_file)
        if not feasible:
            row["status"] = "INFEASIBLE (official checker)"
            return row
        row["run_value"] = value
        previous = saved_value(key)
        if value > previous + 1e-9:
            write_solution(SOLUTIONS_DIR / f"{key}.txt", sol)
            row["status"] = f"improved ({previous:.2f} -> {value:.2f})"
        else:
            row["status"] = f"kept saved ({previous:.2f})"
    row["strategy"] = sol.info.get("construction", "")
    return row


def load_reference() -> dict[str, float]:
    with open(REFERENCE_CSV, newline="") as f:
        return {f"{r['dataset']}/{Path(r['instance']).stem}": float(r["best_objective"]) for r in csv.DictReader(f)}


def write_report() -> None:
    """Build results/results.csv and results/summary.md from solutions/."""
    reference = load_reference()
    rows = []
    for key, ref in reference.items():
        value = saved_value(key)
        rows.append({"instance": key, "ours": value, "reference": ref, "pct": 100 * value / ref if ref else 0.0})

    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / "results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["instance", "ours", "reference", "pct"])
        writer.writeheader()
        writer.writerows(rows)

    lines = ["# Results (best saved solutions vs. best known)", ""]
    for ds in ["a", "b", "x"]:
        part = [r for r in rows if r["instance"].startswith(ds + "/")]
        if part:
            mean = sum(r["pct"] for r in part) / len(part)
            lines.append(f"- Dataset {ds.upper()}: mean {mean:.1f}% of best known ({len(part)} instances)")
    mean_all = sum(r["pct"] for r in rows) / len(rows)
    solved = sum(r["ours"] > 0 for r in rows)
    lines += [f"- **Overall: mean {mean_all:.1f}% of best known, {solved}/{len(rows)} instances with a feasible solution**", ""]
    lines += ["| Instance | Ours | Best known | % |", "|---|---:|---:|---:|"]
    lines += [f"| {r['instance']} | {r['ours']:.2f} | {r['reference']:.2f} | {r['pct']:.1f}% |" for r in rows]
    (RESULTS_DIR / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"\nOverall: mean {mean_all:.1f}% of best known, {solved}/{len(rows)} feasible -> results/summary.md")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--datasets", nargs="+", default=["a", "b", "x"])
    parser.add_argument("--instances", nargs="+", help="e.g. a/instance_0003 (overrides --datasets)")
    parser.add_argument("--time-limit", type=float, default=60.0, help="seconds per instance")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    args = parser.parse_args()

    keys = args.instances or all_instances(args.datasets)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, k, args.time_limit, args.seed) for k in keys]
        for fut in futures:
            r = fut.result()
            print(f"{r['instance']:<20} {r['run_value']:>10.2f}  {r['time_s']:>7.1f}s  {r['status']}", flush=True)
    write_report()


if __name__ == "__main__":
    main()

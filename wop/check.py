"""Validate every file in solutions/ with the official checker.

    python -m wop.check

Exits with code 1 if any solution is missing or infeasible. Run it before
every merge to main and before the final delivery.
"""

import sys

from wop.official import official_check
from wop.run import INSTANCES_DIR, SOLUTIONS_DIR, all_instances


def main() -> None:
    bad = 0
    for key in all_instances(["a", "b", "x"]):
        sol_file = SOLUTIONS_DIR / f"{key}.txt"
        if not sol_file.exists():
            print(f"{key:<20} MISSING")
            bad += 1
            continue
        feasible, value = official_check(INSTANCES_DIR / f"{key}.txt", sol_file)
        print(f"{key:<20} {'OK' if feasible else 'INFEASIBLE':<10} {value:.4f}")
        bad += not feasible
    print(f"\n{bad} problem(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

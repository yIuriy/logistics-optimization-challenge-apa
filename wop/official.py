"""Bridge to the official, unmodified checker in tools/checker.py.

Our own `wop.solution.violations` is used while searching; this module is the
final word on whether a solution file would be accepted.
"""

import importlib.util
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "tools" / "checker.py"


@lru_cache(maxsize=1)
def _checker_class():
    spec = importlib.util.spec_from_file_location("official_checker", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WaveOrderPicking


def official_check(instance_file: str | Path, solution_file: str | Path) -> tuple[bool, float]:
    """Return (feasible, objective) exactly as the official checker computes them."""
    checker = _checker_class()()
    checker.read_input(str(instance_file))
    orders, aisles = checker.read_output(str(solution_file))
    if not aisles:
        return False, 0.0
    feasible = bool(checker.is_solution_feasible(orders, aisles))
    value = float(checker.compute_objective_function(orders, aisles)) if feasible else 0.0
    return feasible, value

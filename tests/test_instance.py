import subprocess
import sys
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from order_selection.instance import (
    Solution,
    is_feasible,
    objective,
    read_instance,
    read_solution,
    write_solution,
)

CHECKER = Path(__file__).parents[1] / "src" / "order_selection" / "checker.py"

# Example of section 3.1 of the official rules (5 orders, 5 items, 5 aisles)
EXAMPLE_INSTANCE = """5 5 5
2 0 3 2 1
2 1 1 3 1
2 2 1 4 2
4 0 1 2 2 3 1 4 1
1 1 1
4 0 2 1 1 2 1 4 1
4 0 2 1 1 2 2 4 1
3 1 2 3 1 4 2
4 0 2 1 1 3 1 4 1
4 1 1 2 2 3 1 4 2
5 12
"""

# Solution of section 3.2 of the official rules, written by hand
EXAMPLE_SOLUTION = "4\n0\n1\n2\n4\n2\n1\n3\n"


def test_example_solution_has_objective_five_and_passes_the_checker(tmp_path):
    instance_path = tmp_path / "instance.txt"
    solution_path = tmp_path / "solution.txt"
    instance_path.write_text(EXAMPLE_INSTANCE, encoding="utf-8")
    solution_path.write_text(EXAMPLE_SOLUTION, encoding="utf-8")

    instance = read_instance(instance_path)
    solution = read_solution(solution_path)
    checker = subprocess.run(  # noqa: S603 (runs the official checker with paths created by this test)
        [sys.executable, CHECKER, instance_path, solution_path],
        capture_output=True,
        text=True,
        check=True,
    )

    assert solution == Solution(orders=[0, 1, 2, 4], aisles=[1, 3])
    assert objective(instance, solution) == 5
    assert is_feasible(instance, solution)
    assert "Is solution feasible: True" in checker.stdout
    assert "Objective function value: 5.0" in checker.stdout


@given(
    orders=st.lists(st.integers(min_value=0, max_value=70_000)),
    aisles=st.lists(st.integers(min_value=0, max_value=500)),
)
def test_writing_then_reading_a_solution_returns_the_same_solution(orders, aisles):
    solution = Solution(orders=orders, aisles=aisles)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "solution.txt"
        write_solution(solution, path)
        assert read_solution(path) == solution

"""Exact algorithm solved by HiGHS with the Dinkelbach method (issue #12).

The model uses binary variables x[o] for selecting order o and y[a] for
visiting aisle a, subject to the official wave size bounds, item stock
balance, and at least one visited aisle. Because the objective is a fraction
(units divided by visited aisles), the Dinkelbach method solves a sequence of
linear integer problems maximizing ``units - lam * aisles`` on the same model,
updating only the aisle objective coefficients between iterations.
"""

import math
import time
from dataclasses import dataclass

import highspy
import numpy as np

from order_selection.instance import Instance, Solution, is_feasible

# Stopping this many seconds before the time limit, to leave time to write the output
SAFETY_MARGIN_SECONDS = 5.0

# Treating F(lam) at or below this value as zero to absorb floating-point rounding
OPTIMALITY_TOLERANCE = 1e-6

# Threshold for reading binary variable values back from the MIP solution
BINARY_THRESHOLD = 0.5

# Zero relative gap and tight absolute gap so each Dinkelbach round proves optimality
MIP_REL_GAP = 0.0
MIP_ABS_GAP = 1e-7


@dataclass
class ExactModel:
    """HiGHS MIP model and metadata built once per instance."""

    instance: Instance
    highs: highspy.Highs
    n_orders: int
    n_aisles: int
    order_units: np.ndarray
    aisle_columns: np.ndarray


@dataclass
class SearchState:
    """Best feasible wave and bounds tracked across Dinkelbach iterations."""

    best_solution: Solution | None
    lam: float
    upper_bound: float
    iterations: int


def collect_stock_entries(
    instance: Instance,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Flatten order demand and aisle stock into item, column and coefficient arrays."""
    n_orders = len(instance.orders)
    item_ids: list[int] = []
    col_ids: list[int] = []
    coeffs: list[float] = []

    # Collecting positive demand coefficients u[o][i] for order variables x[o]
    for order_index, requested in enumerate(instance.orders):
        for item, units in requested.items():
            item_ids.append(item)
            col_ids.append(order_index)
            coeffs.append(float(units))

    # Collecting negative stock coefficients -u[a][i] for aisle variables y[a]
    for aisle_index, stored in enumerate(instance.aisles):
        column = n_orders + aisle_index
        for item, units in stored.items():
            item_ids.append(item)
            col_ids.append(column)
            coeffs.append(-float(units))

    return (
        np.array(item_ids, dtype=np.int32),
        np.array(col_ids, dtype=np.int32),
        np.array(coeffs, dtype=np.float64),
    )


def build_constraint_matrix(
    instance: Instance, order_units: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build CSR rows for wave bounds, aisle lower bound and item stock balance.

    Args:
        instance: The problem instance.
        order_units: Total units requested by each order.

    Returns:
        Five arrays ``(row_lower, row_upper, starts, indices, values)`` ready
        for ``highspy.Highs.addRows``.
    """
    n_orders = len(instance.orders)
    n_aisles = len(instance.aisles)

    # Enforcing constraints (2) and (3) in row 0: wave_min_units <= units <= max
    wave_cols = np.flatnonzero(order_units > 0).astype(np.int32)
    wave_vals = order_units[wave_cols]

    # Enforcing at least one visited aisle in row 1: sum(y_a) >= 1
    aisle_cols = np.arange(n_orders, n_orders + n_aisles, dtype=np.int32)
    aisle_vals = np.ones(n_aisles, dtype=np.float64)

    # Grouping stock balance entries by item so each item becomes one CSR row
    items_arr, cols_arr, vals_arr = collect_stock_entries(instance)
    by_item = np.argsort(items_arr, kind="stable")
    stock_starts = np.zeros(instance.n_items, dtype=np.int32)
    if instance.n_items > 1:
        counts = np.bincount(items_arr, minlength=instance.n_items)
        stock_starts[1:] = np.cumsum(counts[:-1])

    row_lower = np.concatenate(
        (
            np.array([float(instance.wave_min_units), 1.0], dtype=np.float64),
            np.full(instance.n_items, -highspy.kHighsInf, dtype=np.float64),
        )
    )
    row_upper = np.concatenate(
        (
            np.array(
                [float(instance.wave_max_units), highspy.kHighsInf], dtype=np.float64
            ),
            np.zeros(instance.n_items, dtype=np.float64),
        )
    )
    offset = len(wave_cols) + len(aisle_cols)
    starts = np.concatenate(
        (np.array([0, len(wave_cols)], dtype=np.int32), stock_starts + offset)
    )
    indices = np.concatenate((wave_cols, aisle_cols, cols_arr[by_item]))
    values = np.concatenate((wave_vals, aisle_vals, vals_arr[by_item]))
    return row_lower, row_upper, starts, indices, values


def build_model(instance: Instance) -> ExactModel:
    """Create and configure the HiGHS binary MIP model for an instance.

    Args:
        instance: The problem instance.

    Returns:
        An ``ExactModel`` holding the configured solver and column metadata.
    """
    n_orders = len(instance.orders)
    n_aisles = len(instance.aisles)
    n_vars = n_orders + n_aisles
    order_units = np.array(
        [sum(requested.values()) for requested in instance.orders], dtype=np.float64
    )
    aisle_columns = np.arange(n_orders, n_vars, dtype=np.int32)

    highs = highspy.Highs()
    highs.setOptionValue("log_to_console", False)
    highs.setOptionValue("mip_rel_gap", MIP_REL_GAP)
    highs.setOptionValue("mip_abs_gap", MIP_ABS_GAP)

    # Adding binary variables x[0..n_orders-1] and y[0..n_aisles-1] with initial lam = 0
    costs = np.concatenate((order_units, np.zeros(n_aisles, dtype=np.float64)))
    empty_int = np.empty(0, dtype=np.int32)
    empty_float = np.empty(0, dtype=np.float64)
    highs.addCols(
        n_vars,
        costs,
        np.zeros(n_vars, dtype=np.float64),
        np.ones(n_vars, dtype=np.float64),
        0,
        empty_int,
        empty_int,
        empty_float,
    )
    highs.changeColsIntegrality(
        n_vars,
        np.arange(n_vars, dtype=np.int32),
        np.full(n_vars, int(highspy.HighsVarType.kInteger), dtype=np.uint8),
    )

    # Adding all linear constraints in a single sparse batch and setting maximization
    row_lower, row_upper, starts, indices, values = build_constraint_matrix(
        instance, order_units
    )
    highs.addRows(
        len(row_lower),
        row_lower,
        row_upper,
        len(values),
        starts,
        indices,
        values,
    )
    highs.changeObjectiveSense(highspy.ObjSense.kMaximize)
    return ExactModel(instance, highs, n_orders, n_aisles, order_units, aisle_columns)


def extract_solution(model: ExactModel) -> tuple[Solution, float] | None:
    """Read the current primal feasible wave and its objective ratio from HiGHS."""
    primal_status = model.highs.getInfo().primal_solution_status
    if primal_status != int(highspy.SolutionStatus.kSolutionStatusFeasible):
        return None
    col_values = np.asarray(model.highs.getSolution().col_value, dtype=np.float64)
    orders = np.flatnonzero(col_values[: model.n_orders] > BINARY_THRESHOLD).tolist()
    aisles = np.flatnonzero(col_values[model.n_orders :] > BINARY_THRESHOLD).tolist()
    solution = Solution(orders, aisles)
    # Guarding against rare MIP numerical tolerances before accepting any wave
    if not is_feasible(model.instance, solution):
        return None
    units = float(model.order_units[orders].sum())
    return solution, units / len(aisles)


def compute_upper_bound(
    lam_round: float, best_lam: float, dual_bound: float, max_units: int
) -> float:
    """Compute a valid objective upper bound from a Dinkelbach round's dual bound.

    For any feasible wave, ``units - lam_round * aisles <= F_bar`` where
    ``F_bar`` is the HiGHS ``mip_dual_bound``. Dividing by ``aisles >= 1`` gives
    ``units / aisles <= lam_round + F_bar / aisles <= lam_round + F_bar``
    because ``aisles >= 1`` and ``F_bar >= 0``. Moreover, every feasible wave
    has at most ``max_units`` units and at least one aisle, so
    ``units / aisles <= max_units`` is also always valid.
    """
    cap = float(max_units)
    if math.isfinite(dual_bound):
        # Combining the Dinkelbach dual bound with the trivial upper bound UB / 1
        candidate = lam_round + max(0.0, dual_bound)
        cap = min(cap, candidate)
    return max(best_lam, cap)


def build_report(
    status: str,
    iterations: int,
    lower_bound: float | None,
    upper_bound: float | None,
) -> dict:
    """Build the run metadata dictionary returned alongside the solution."""
    return {
        "status": status,
        "iterations": iterations,
        "objective_lower_bound": lower_bound,
        "objective_upper_bound": upper_bound,
    }


def finalize_interrupted(
    model: ExactModel, state: SearchState, max_units: int
) -> tuple[Solution | None, dict]:
    """Collect any improved wave from an interrupted round and compute final bounds."""
    lam_round = state.lam
    candidate = extract_solution(model)
    if candidate is not None:
        solution, ratio = candidate
        if state.best_solution is None or ratio > state.lam:
            state.best_solution = solution
            state.lam = ratio

    if state.best_solution is None:
        return None, build_report("no_solution", state.iterations, None, None)

    dual_bound = float(model.highs.getInfo().mip_dual_bound)
    upper_bound = min(
        state.upper_bound,
        compute_upper_bound(lam_round, state.lam, dual_bound, max_units),
    )
    upper_bound = max(state.lam, upper_bound)
    return state.best_solution, build_report(
        "time_limit", state.iterations, state.lam, upper_bound
    )


def run_dinkelbach_round(
    model: ExactModel, state: SearchState, remaining: float, max_units: int
) -> tuple[Solution | None, dict] | None:
    """Execute one HiGHS round for the current lambda and return a result if done.

    Returns ``None`` when ``F(lam) > OPTIMALITY_TOLERANCE`` and the search
    should advance to the next lambda, or the final ``(solution, report)`` pair
    when optimality, infeasibility or the time limit is reached.
    """
    # Updating only aisle objective costs to -lam while reusing the same MIP model
    aisle_costs = np.full(model.n_aisles, -state.lam, dtype=np.float64)
    model.highs.changeColsCost(model.n_aisles, model.aisle_columns, aisle_costs)
    model.highs.setOptionValue("time_limit", remaining)
    model.highs.run()
    state.iterations += 1

    model_status = model.highs.getModelStatus()
    if model_status == highspy.HighsModelStatus.kInfeasible:
        return None, build_report("no_solution", state.iterations, None, None)
    if model_status != highspy.HighsModelStatus.kOptimal:
        return finalize_interrupted(model, state, max_units)

    candidate = extract_solution(model)
    if candidate is None:
        return None, build_report("no_solution", state.iterations, None, None)

    lam_round = state.lam
    solution, ratio = candidate
    dual_bound = float(model.highs.getInfo().mip_dual_bound)
    reached_optimum = model.highs.getObjectiveValue() <= OPTIMALITY_TOLERANCE or (
        state.best_solution is not None and ratio <= state.lam
    )
    if reached_optimum:
        # Keeping the optimal wave at lam, or adopting the wave found at lam = 0
        if state.best_solution is None or ratio > state.lam:
            state.best_solution, state.lam = solution, ratio
        return state.best_solution, build_report(
            "optimal", state.iterations, state.lam, state.lam
        )

    state.best_solution, state.lam = solution, ratio
    state.upper_bound = min(
        state.upper_bound,
        compute_upper_bound(lam_round, state.lam, dual_bound, max_units),
    )
    return None


def solve(instance: Instance, parameters: dict) -> tuple[Solution | None, dict]:
    """Solve the wave order picking problem with HiGHS and the Dinkelbach method.

    Builds the binary MIP model once and solves a sequence of linear problems
    ``max units - lam * aisles`` starting from ``lam = 0``. Stops with status
    ``"optimal"`` once ``F(lam) <= 1e-6``, with ``"time_limit"`` and valid
    lower/upper bounds if the time budget runs out after finding a feasible
    wave, or with ``"no_solution"`` if no feasible wave is found.

    Args:
        instance: The problem instance.
        parameters: Dictionary containing ``time_limit_seconds``.

    Returns:
        A pair ``(solution, report)`` where ``solution`` is the best feasible
        ``Solution`` found (or ``None``) and ``report`` holds ``status``,
        ``iterations``, ``objective_lower_bound`` and ``objective_upper_bound``.
    """
    start = time.perf_counter()
    time_limit = float(parameters["time_limit_seconds"])
    budget = (
        time_limit - SAFETY_MARGIN_SECONDS
        if time_limit > SAFETY_MARGIN_SECONDS
        else time_limit
    )

    if not instance.orders or not instance.aisles:
        return None, build_report("no_solution", 0, None, None)

    model = build_model(instance)
    state = SearchState(
        best_solution=None,
        lam=0.0,
        upper_bound=float(instance.wave_max_units),
        iterations=0,
    )

    while True:
        remaining = budget - (time.perf_counter() - start)
        if remaining <= 0.0:
            if state.best_solution is None:
                return None, build_report("no_solution", state.iterations, None, None)
            return state.best_solution, build_report(
                "time_limit", state.iterations, state.lam, state.upper_bound
            )

        finished = run_dinkelbach_round(
            model, state, remaining, instance.wave_max_units
        )
        if finished is not None:
            return finished

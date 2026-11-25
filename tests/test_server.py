import json
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from order_selection.run_request import parse_run_request
from order_selection.server import AppServer, default_parameters

ROOT = Path(__file__).parents[1]
CHECKER = ROOT / "src" / "order_selection" / "checker.py"
INSTANCE = "b_instance_9999"

# Example of section 3.1 of the official rules (5 orders, 5 items, 5 aisles)
EXAMPLE_INSTANCE_TEXT = """5 5 5
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

VALID_PARAMETERS = {
    "population_size": 6,
    "tournament_size": 2,
    "mutation_rate": 0.05,
    "max_generations": 5,
    "seed": 1,
    "time_limit_seconds": 10,
}


@pytest.fixture
def data_dir(tmp_path):
    directory = tmp_path / "data"
    directory.mkdir()
    (directory / f"{INSTANCE}.txt").write_text(EXAMPLE_INSTANCE_TEXT, encoding="utf-8")
    return directory


@pytest.fixture
def server(tmp_path, data_dir):
    app = AppServer(("127.0.0.1", 0), data_dir, tmp_path / "results")
    thread = threading.Thread(target=app.serve_forever, daemon=True)
    thread.start()
    yield app
    app.shutdown()
    app.server_close()


def request(server: AppServer, path: str, body: object = None) -> tuple[int, object]:
    """Send a GET, or a POST when there is a body, and return status and JSON."""
    url = f"http://127.0.0.1:{server.server_address[1]}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=data, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def run_body(**changes: object) -> dict:
    return {
        "instance": INSTANCE,
        "method": "genetic",
        "parameters": VALID_PARAMETERS | changes,
    }


@pytest.mark.parametrize(
    "body",
    [
        run_body(population_size=0),
        run_body(population_size=2.5),
        run_body(tournament_size=7),
        run_body(mutation_rate=1.5),
        run_body(mutation_rate=-0.1),
        run_body(max_generations=0),
        run_body(seed=True),
        run_body(time_limit_seconds=601),
        run_body(time_limit_seconds=0),
        run_body() | {"instance": "../../etc/passwd"},
        run_body() | {"method": "greedy"},
        run_body() | {"parameters": [1, 2]},
        [1, 2],
    ],
)
def test_invalid_run_returns_400(server, body):
    status, content = request(server, "/api/runs", body)

    assert status == 400
    assert content["error"]


def test_body_that_is_not_json_returns_400(server):
    url = f"http://127.0.0.1:{server.server_address[1]}/api/runs"
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(url, data=b"{not json", timeout=30)
    assert error.value.code == 400


def test_run_writes_a_pair_that_the_checker_accepts(server, data_dir):
    status, run = request(server, "/api/runs", run_body())

    assert status == 200
    assert run["source"] == "web"
    assert run["generations"] == 5
    stem = f"{INSTANCE}_genetic_pop6_tour2_mut0.05_seed1"
    web_dir = server.results_dir / "web"
    assert (web_dir / f"{stem}.json").exists()
    result = subprocess.run(  # noqa: S603 (runs the official checker on test files)
        [sys.executable, str(CHECKER), str(data_dir / f"{INSTANCE}.txt"),
         str(web_dir / f"{stem}.txt")],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    assert "Is solution feasible: True" in result.stdout

    status, results = request(server, "/api/results")
    assert status == 200
    assert [entry["source"] for entry in results] == ["web"]


def test_second_run_while_one_is_running_returns_409(server):
    with server.run_lock:
        status, _ = request(server, "/api/runs", run_body())

    assert status == 409


def test_instances_lists_name_dataset_and_orders(server):
    status, instances = request(server, "/api/instances")

    assert status == 200
    assert instances == [
        {
            "instance": INSTANCE,
            "dataset": "B",
            "n_orders": 5,
            "best_official": None,
        }
    ]


def test_unknown_api_route_returns_404(server):
    status, _ = request(server, "/api/nothing")

    assert status == 404


def test_defaults_come_from_the_batch_configuration():
    config = json.loads((ROOT / "configs" / "batch.json").read_text(encoding="utf-8"))

    defaults = default_parameters(ROOT / "configs" / "batch.json")

    assert (
        defaults["parameters"]["population_size"]
        == (config["genetic"]["population_size"][0])
    )
    assert defaults["parameters"]["time_limit_seconds"] == 30


# The data folder is only read, so sharing it between examples is safe
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    population=st.integers(1, 1000),
    tournament=st.integers(1, 1000),
    rate=st.floats(0, 1),
)
def test_tournament_is_accepted_only_up_to_the_population(
    data_dir, population, tournament, rate
):
    body = run_body(
        population_size=population, tournament_size=tournament, mutation_rate=rate
    )
    if tournament <= population:
        assert parse_run_request(body, data_dir).parameters["tournament_size"] == (
            tournament
        )
    else:
        with pytest.raises(ValueError, match="tournament_size"):
            parse_run_request(body, data_dir)

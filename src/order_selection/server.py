"""HTTP server of the web interface, built on the standard library (issue #18).

The server hands the compiled React page of ``frontend/dist`` to the browser
and answers four JSON routes:

- ``GET /api/results``: every ``.json`` of ``results/`` (``source`` ``batch``)
  and of ``results/web/`` (``source`` ``web``).
- ``GET /api/instances``: name, data set, number of orders and official best
  value of each instance of ``data/``.
- ``GET /api/defaults``: the genetic parameters of the final batch, read from
  ``configs/batch.json``, so the form starts from the group's configuration.
- ``POST /api/runs``: checks the request, runs ``batch_runner.run_one`` and
  returns the ``.json`` it wrote.

Runs from the page go to ``results/web/``, so they never overwrite the final
batch that the charts and ``summary.md`` use. Only one run goes at a time,
because two solvers on the same machine would slow each other down.

Run with ``uv run python -m order_selection.server`` and open
``http://localhost:8000``.
"""

import json
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from order_selection import batch_runner
from order_selection.results import dataset_of, load_results
from order_selection.run_request import (
    MAX_TIME_LIMIT_SECONDS,
    instance_paths,
    parse_run_request,
)

ROOT = Path(__file__).parents[2]
FRONTEND_DIST = ROOT / "frontend" / "dist"
BATCH_CONFIG = ROOT / "configs" / "batch.json"

# Folder inside results/ for runs started from the page
WEB_RUNS_FOLDER = "web"

DEFAULT_PORT = 8000

# Keeping a run from the page short, because the presentation lasts 5 minutes
WEB_TIME_LIMIT_SECONDS = 30


class AppServer(ThreadingHTTPServer):
    """HTTP server that knows where the data and the results are."""

    def __init__(self, address: tuple[str, int], data_dir: Path, results_dir: Path):
        super().__init__(address, RequestHandler)
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.run_lock = threading.Lock()


class RequestHandler(SimpleHTTPRequestHandler):
    """Answers the ``/api/`` routes and serves the page for every other path."""

    server: AppServer

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIST), **kwargs)

    def do_GET(self) -> None:
        """Answer a data route, or hand the request to the static file server."""
        path = urlsplit(self.path).path
        routes = {
            "/api/results": lambda: list_results(self.server.results_dir),
            "/api/instances": lambda: list_instances(self.server.data_dir),
            "/api/defaults": lambda: default_parameters(BATCH_CONFIG),
        }
        if path in routes:
            self.send_json(HTTPStatus.OK, routes[path]())
        elif path.startswith("/api/"):
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "rota desconhecida"})
        else:
            super().do_GET()

    def do_POST(self) -> None:
        """Check and execute a run asked by the page."""
        if urlsplit(self.path).path != "/api/runs":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "rota desconhecida"})
            return

        # Checking the request before taking the lock, so a bad request never waits
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"null")
            request = parse_run_request(body, self.server.data_dir)
        except ValueError as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        if not self.server.run_lock.acquire(blocking=False):
            self.send_json(HTTPStatus.CONFLICT, {"error": "já existe uma execução"})
            return
        try:
            web_dir = self.server.results_dir / WEB_RUNS_FOLDER
            web_dir.mkdir(parents=True, exist_ok=True)
            json_path = batch_runner.run_one(
                request.instance_path, request.method, request.parameters, web_dir
            )
        finally:
            self.server.run_lock.release()
        run = json.loads(json_path.read_text(encoding="utf-8"))
        self.send_json(HTTPStatus.OK, run | {"source": WEB_RUNS_FOLDER})

    def send_json(self, status: HTTPStatus, content: object) -> None:
        """Write ``content`` as the JSON body of the response."""
        body = json.dumps(content).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def list_results(results_dir: Path) -> list[dict]:
    """Return the batch runs and the page runs, each tagged with its source."""
    batch = [run | {"source": "batch"} for run in load_results(results_dir)]
    web_dir = results_dir / WEB_RUNS_FOLDER
    web = [run | {"source": WEB_RUNS_FOLDER} for run in load_results(web_dir)]
    return batch + web


def list_instances(data_dir: Path) -> list[dict]:
    """Return the name, data set, orders and official best of each instance."""
    return [
        {
            "instance": name,
            "dataset": dataset_of(name),
            "n_orders": count_orders(path),
            "best_official": batch_runner.best_official(name),
        }
        for name, path in instance_paths(data_dir).items()
    ]


def count_orders(instance_path: Path) -> int:
    """Read the number of orders from the first line, without loading the file."""
    with instance_path.open(encoding="utf-8") as file:
        return int(file.readline().split()[0])


def default_parameters(config_path: Path) -> dict:
    """Return the first value of each genetic list of the batch configuration.

    The time limit is the short one of the page, and the maximum the form
    accepts goes along, so the page and the server agree on both.
    """
    config = json.loads(config_path.read_text(encoding="utf-8"))
    genetic = {name: values[0] for name, values in config["genetic"].items()}
    return {
        "parameters": genetic | {"time_limit_seconds": WEB_TIME_LIMIT_SECONDS},
        "max_time_limit_seconds": MAX_TIME_LIMIT_SECONDS,
    }


def main(port: int = DEFAULT_PORT) -> None:
    """Serve the page and the data routes until Ctrl+C."""
    if not FRONTEND_DIST.exists():
        print("frontend/dist não existe: rode `npm ci && npm run build` em frontend/")
    server = AppServer(("127.0.0.1", port), ROOT / "data", ROOT / "results")
    print(f"Abra http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()

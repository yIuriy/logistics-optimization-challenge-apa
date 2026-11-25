"""Checks the run that the web interface asks for, before any solver starts (issue #18).

The browser sends a JSON object with the instance name, the method and the
parameters. ``parse_run_request`` turns it into a ``RunRequest`` or raises
``ValueError`` with a message in Portuguese that the page shows as it is. The
instance must be one of the files of ``data/``, so a request can never point
the solver at another path of the machine.
"""

from dataclasses import dataclass
from pathlib import Path

METHODS = ("genetic", "exact")

# Matching the time limit of the batch, so a web run never exceeds the official one
MAX_TIME_LIMIT_SECONDS = 600

# Integer parameters of the genetic algorithm and the smallest value each accepts.
# The seed accepts zero because numpy's default_rng takes any non negative integer
GENETIC_INTEGERS = {
    "population_size": 1,
    "tournament_size": 1,
    "max_generations": 1,
    "seed": 0,
}


@dataclass(frozen=True)
class RunRequest:
    """One run asked by the web interface, ready for ``batch_runner.run_one``."""

    instance_path: Path
    method: str
    parameters: dict


def instance_paths(data_dir: Path) -> dict[str, Path]:
    """Return the instance files of ``data_dir`` by name, sorted by name."""
    return {path.stem: path for path in sorted(data_dir.glob("*_instance_*.txt"))}


def parse_run_request(body: object, data_dir: Path) -> RunRequest:
    """Check the request body and return the run it describes.

    Args:
        body: The JSON object sent by the browser.
        data_dir: Directory with the instance files.

    Returns:
        The instance path, the method and the parameters, with
        ``time_limit_seconds`` among them.

    Raises:
        ValueError: If a field is missing, has the wrong type or is out of range.
    """
    if not isinstance(body, dict):
        raise ValueError("o corpo da requisição deve ser um objeto JSON")

    instances = instance_paths(data_dir)
    if body.get("instance") not in instances:
        raise ValueError("instância desconhecida")
    if body.get("method") not in METHODS:
        raise ValueError(f"método deve ser um de {list(METHODS)}")

    parameters = body.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parâmetros devem ser um objeto JSON")

    checked = {"time_limit_seconds": time_limit(parameters)}
    if body["method"] == "genetic":
        checked |= genetic_parameters(parameters)
    return RunRequest(instances[body["instance"]], body["method"], checked)


def time_limit(parameters: dict) -> float:
    """Return the time limit if it is a number in (0, MAX_TIME_LIMIT_SECONDS]."""
    value = parameters.get("time_limit_seconds")
    if not is_number(value) or not 0 < value <= MAX_TIME_LIMIT_SECONDS:
        message = f"time_limit_seconds deve estar entre 0 e {MAX_TIME_LIMIT_SECONDS}"
        raise ValueError(message)
    return value


def genetic_parameters(parameters: dict) -> dict:
    """Check the parameters of the genetic algorithm and return them.

    Args:
        parameters: The ``parameters`` object of the request.

    Returns:
        The integer parameters and ``mutation_rate``, without other keys.

    Raises:
        ValueError: If an integer is below its minimum, the tournament is larger
            than the population or the mutation rate is outside [0, 1].
    """
    checked = {}
    for name, minimum in GENETIC_INTEGERS.items():
        value = parameters.get(name)
        if not is_integer(value) or value < minimum:
            raise ValueError(f"{name} deve ser um inteiro maior ou igual a {minimum}")
        checked[name] = value

    # Drawing the tournament without replacement needs enough individuals
    if checked["tournament_size"] > checked["population_size"]:
        raise ValueError("tournament_size deve ser menor ou igual a population_size")

    rate = parameters.get("mutation_rate")
    if not is_number(rate) or not 0 <= rate <= 1:
        raise ValueError("mutation_rate deve estar entre 0 e 1")
    checked["mutation_rate"] = rate
    return checked


def is_integer(value: object) -> bool:
    """Tell whether the value is an int, leaving out booleans."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    """Tell whether the value is an int or a float, leaving out booleans."""
    return is_integer(value) or isinstance(value, float)

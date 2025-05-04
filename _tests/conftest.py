"""
Pytest fixtures for ephemeral Loki, Grafana Alloy, and OpenTelemetry Collector environments.
Spins up containers using Docker Compose for integration/E2E tests.
Ensures all test data is cleaned up after each test.
Also loads and sets environment variables from canonical Loki config for all tests.
"""
import subprocess
import time
import os
from pathlib import Path

import pytest
from app.core.loki import config

DOCKER_COMPOSE_FILE = Path(__file__).parent.parent / "docker" / "docker-compose.test.yml"

@pytest.fixture(scope="session", autouse=True)
def set_loki_env_vars():
    """
    Load and set all Loki/Grafana/Redis/OTEL env variables from config for all tests.
    Ensures subprocesses and Docker Compose inherit correct settings.
    """
    os.environ["LOKI_URL"] = config.LOKI_URL
    os.environ["LOKI_PORT"] = str(config.LOKI_PORT)
    os.environ["GRAFANA_URL"] = config.GRAFANA_URL
    os.environ["GRAFANA_PORT"] = str(config.GRAFANA_PORT)
    os.environ["GRAFANA_ADMIN_USER"] = config.GRAFANA_ADMIN_USER
    os.environ["GRAFANA_ADMIN_PASSWORD"] = config.GRAFANA_ADMIN_PASSWORD
    os.environ["REDIS_HOST"] = config.REDIS_HOST
    os.environ["REDIS_PORT"] = str(config.REDIS_PORT)
    os.environ["REDIS_PASSWORD"] = config.REDIS_PASSWORD
    os.environ["FASTAPI_PORT"] = str(config.FASTAPI_PORT)
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = config.OTEL_EXPORTER_OTLP_ENDPOINT
    os.environ["OTEL_EXPORTER_OTLP_INSECURE"] = str(config.OTEL_EXPORTER_OTLP_INSECURE)
    # Add more as needed
    yield

@pytest.fixture(scope="session", autouse=True)
def start_observability_stack(set_loki_env_vars):
    """
    Start Loki, Alloy, and Otel Collector via Docker Compose for integration tests.
    Ensures env vars are set before containers start.
    """
    # Start containers
    subprocess.run([
        "docker-compose", "-f", str(DOCKER_COMPOSE_FILE), "up", "-d"
    ], check=True)
    # Wait for services to be healthy
    for _ in range(30):
        result = subprocess.run([
            "docker", "inspect", "--format=\"{{.State.Health.Status}}\"", "loki"
        ], capture_output=True, text=True)
        if 'healthy' in result.stdout:
            break
        time.sleep(2)
    else:
        raise RuntimeError("Loki did not become healthy in time.")
    yield
    # Tear down containers
    subprocess.run([
        "docker-compose", "-f", str(DOCKER_COMPOSE_FILE), "down", "-v"
    ], check=True)

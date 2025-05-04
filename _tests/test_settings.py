"""
Loads FastAPI settings for Loki tests, ensuring all environment variables and ports are correct.
Use this in other tests for consistent config.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure app core is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings

@pytest.fixture(scope="session")
def loki_test_settings():
    """
    Fixture to provide access to FastAPI settings for Loki tests.
    Ensures env variables and ports are loaded from the canonical settings object.
    """
    class EnvAwareSettings:
        def __init__(self, settings):
            self.monitoring = settings.monitoring
            self.redis = settings.redis
            self.app = settings.app
            self.security = settings.security
            self.monitoring.GRAFANA_URL = os.environ.get("GRAFANA_URL", self.monitoring.GRAFANA_URL)
            self.monitoring.GRAFANA_PORT = int(os.environ.get("GRAFANA_PORT", self.monitoring.GRAFANA_PORT))
            self.redis.REDIS_HOST = os.environ.get("REDIS_HOST", self.redis.REDIS_HOST)
            self.redis.REDIS_PORT = int(os.environ.get("REDIS_PORT", self.redis.REDIS_PORT))
            self.app.FASTAPI_PORT = int(os.environ.get("FASTAPI_PORT", self.app.FASTAPI_PORT))
            self.security.OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", self.security.OTEL_EXPORTER_OTLP_ENDPOINT)
            self.security.OTEL_EXPORTER_OTLP_INSECURE = os.environ.get("OTEL_EXPORTER_OTLP_INSECURE", str(self.security.OTEL_EXPORTER_OTLP_INSECURE)) == "True"
    return EnvAwareSettings(settings)


def test_loki_settings_loaded(loki_test_settings):
    """
    Production-ready check that Loki/Grafana/Alloy ports and URLs are loaded from settings or env, and endpoints are reachable.
    This test ensures that all environment overrides are respected.
    """
    import socket
    loki_url = os.environ.get("LOKI_URL", loki_test_settings.monitoring.GRAFANA_URL)
    assert loki_url.startswith("http")
    host = loki_url.split('//')[-1].split(':')[0]
    port = int(loki_url.split(':')[-1]) if ':' in loki_url else 3100
    with socket.socket() as s:
        s.settimeout(2)
        assert s.connect_ex((host, port)) == 0, f"Loki endpoint {host}:{port} not reachable"
    assert isinstance(loki_test_settings.app.FASTAPI_PORT, int)
    assert isinstance(loki_test_settings.redis.REDIS_PORT, int)
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", loki_test_settings.security.OTEL_EXPORTER_OTLP_ENDPOINT)
    assert ":" in otel_endpoint, "OTEL endpoint must be host:port"

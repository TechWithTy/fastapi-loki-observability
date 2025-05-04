"""
Loki/Grafana/Redis config for tests and runtime, with values loaded directly from FastAPI settings.
All values are exported as module-level constants for easy import/use in tests, scripts, or other modules.
"""
import os
import sys
from pathlib import Path
from typing import Any

# Ensure app core is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.core.config import settings

# Loki
LOKI_URL = settings.monitoring.GRAFANA_URL
LOKI_PORT = settings.monitoring.GRAFANA_PORT

# Grafana
GRAFANA_URL = settings.monitoring.GRAFANA_URL
GRAFANA_PORT = settings.monitoring.GRAFANA_PORT
GRAFANA_ADMIN_USER = settings.monitoring.GRAFANA_ADMIN_USER
GRAFANA_ADMIN_PASSWORD = settings.monitoring.GRAFANA_ADMIN_PASSWORD

# Redis
REDIS_HOST = settings.redis.REDIS_HOST or "localhost"
REDIS_PORT = settings.redis.REDIS_PORT
REDIS_PASSWORD = settings.redis.REDIS_PASSWORD or ""

# FastAPI App
FASTAPI_PORT = settings.app.FASTAPI_PORT

# OTEL Exporter
OTEL_EXPORTER_OTLP_ENDPOINT = settings.security.OTEL_EXPORTER_OTLP_ENDPOINT
OTEL_EXPORTER_OTLP_INSECURE = settings.security.OTEL_EXPORTER_OTLP_INSECURE

# Add additional config values as needed for observability stack

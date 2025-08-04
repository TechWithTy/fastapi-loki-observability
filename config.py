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

# Try to import settings, but provide defaults if they fail (for testing)
try:
    from app.core.config import settings
    
    # Loki
    LOKI_URL = settings.monitoring.LOKI_URL
    LOKI_PORT = settings.monitoring.LOKI_PORT
    LOKI_TENANT_ID = settings.monitoring.LOKI_TENANT_ID

    # Grafana
    GRAFANA_URL = settings.monitoring.GRAFANA_URL
    GRAFANA_PORT = settings.monitoring.GRAFANA_PORT
    GRAFANA_ADMIN_USER = settings.monitoring.GRAFANA_ADMIN_USER
    GRAFANA_ADMIN_PASSWORD = settings.monitoring.GRAFANA_ADMIN_PASSWORD

    # OTEL Exporter
    OTEL_EXPORTER_OTLP_ENDPOINT = settings.monitoring.OTEL_EXPORTER_OTLP_ENDPOINT
    OTEL_EXPORTER_OTLP_INSECURE = settings.monitoring.OTEL_EXPORTER_OTLP_INSECURE
    
except Exception as e:
    # Fallback to environment variables or defaults for testing
    print(f"[WARNING] Failed to load settings, using defaults: {e}")
    
    # Loki
    LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
    LOKI_PORT = int(os.getenv("LOKI_PORT", "3100"))
    LOKI_TENANT_ID = os.getenv("LOKI_TENANT_ID", "")

    # Grafana
    GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
    GRAFANA_PORT = int(os.getenv("GRAFANA_PORT", "3000"))
    GRAFANA_ADMIN_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
    GRAFANA_ADMIN_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "admin")

    # OTEL Exporter
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    OTEL_EXPORTER_OTLP_INSECURE = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() in ("true", "1", "yes")

# # Redis
# REDIS_HOST = settings.redis.REDIS_HOST or "localhost"
# REDIS_PORT = settings.redis.REDIS_PORT
# REDIS_PASSWORD = settings.redis.REDIS_PASSWORD or ""

# FastAPI App
FASTAPI_PORT = 8000

# Add additional config values as needed for observability stack

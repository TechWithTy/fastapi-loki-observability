"""
Loki observability module for FastAPI applications.

This module provides log aggregation and querying capabilities using Grafana Loki,
integrated with the existing telemetry and tracing infrastructure.

Key components:
    - LokiClient: Core client for log ingestion and querying
    - FastAPILokiHandler: Custom logging handler for automatic log shipping
    - init_loki: Easy integration with FastAPI applications
    - add_request_logging_middleware: HTTP request logging middleware

Example usage:
    from app.core.loki import init_loki, add_request_logging_middleware
    
    app = FastAPI()
    
    # Initialize Loki integration
    loki_client = init_loki(app)
    
    # Add request logging (optional)
    add_request_logging_middleware(app)
"""

from .core import (
    LokiClient,
    LokiQueryResponse,
    FastAPILokiHandler,
    init_loki,
    get_loki_client,
    add_request_logging_middleware
)
from .health import LokiHealthCheck, GrafanaHealthCheck, RedisHealthCheck
from .models.index import LokiConfig, AlloyConfig, OtelCollectorConfig

__all__ = [
    "LokiClient",
    "LokiQueryResponse", 
    "FastAPILokiHandler",
    "init_loki",
    "get_loki_client",
    "add_request_logging_middleware",
    "LokiHealthCheck",
    "GrafanaHealthCheck", 
    "RedisHealthCheck",
    "LokiConfig",
    "AlloyConfig",
    "OtelCollectorConfig"
]

__version__ = "1.0.0"


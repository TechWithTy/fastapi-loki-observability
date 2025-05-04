"""
Unit tests for configuration parsing and validation for Loki, Alloy, and Otel Collector.
Uses Pydantic models for strict type checking.
"""

import os

import pytest
from pydantic import ValidationError

from app.core.loki.models.index import AlloyConfig, LokiConfig, OtelCollectorConfig


def test_loki_config_valid():
    cfg = LokiConfig(
        url=os.environ.get("LOKI_URL", "http://localhost:3100"),
        tenant_id="tenantA",
        tls_enabled=True,
    )
    assert cfg.url == os.environ.get("LOKI_URL", "http://localhost:3100")
    assert cfg.tenant_id == "tenantA"
    assert cfg.tls_enabled is True


def test_loki_config_missing_url():
    with pytest.raises(ValidationError):
        LokiConfig(tenant_id="tenantA")


def test_alloy_config_valid():
    cfg = AlloyConfig(
        config_path=os.environ.get("ALLOY_CONFIG_PATH", "/etc/alloy.yaml"),
        relabel_rules=["env", "app"],
    )
    assert cfg.relabel_rules == ["env", "app"]


def test_otel_collector_config_valid():
    cfg = OtelCollectorConfig(
        endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "0.0.0.0:4317"),
        receivers=["filelog", "syslog"],
    )
    assert "filelog" in cfg.receivers

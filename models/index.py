from pydantic import BaseModel

class LokiConfig(BaseModel):
    url: str
    tenant_id: str | None
    tls_enabled: bool = False


class AlloyConfig(BaseModel):
    config_path: str
    relabel_rules: list[str]


class OtelCollectorConfig(BaseModel):
    endpoint: str
    receivers: list[str]

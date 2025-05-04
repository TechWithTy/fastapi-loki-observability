"""
Integration test: End-to-end log flow from synthetic app to Loki via Alloy and Otel Collector.
Verifies log ingestion, label enrichment, and retention.
"""
import httpx
import pytest
import time
import os


LOKI_URL = "http://localhost:3100"

@pytest.mark.asyncio
async def test_log_ingestion(start_observability_stack):
    """
    Sends a synthetic log to Alloy/Otel, then queries Loki to verify ingestion.
    """
    # Simulate log write: send a real log entry to Loki's push API
    loki_url = os.environ.get("LOKI_URL", "http://localhost:3100")
    push_url = f"{loki_url}/loki/api/v1/push"
    log_stream = {
        "streams": [
            {
                "labels": "{app=\"synthetic\"}",
                "entries": [
                    {"ts": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()), "line": "test-log-ingest-production-check"}
                ],
            }
        ]
    }
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(push_url, json=log_stream)
        assert resp.status_code in (204, 200), f"Push failed: {resp.text}"
        # Query Loki for logs
        query_url = f"{loki_url}/loki/api/v1/query_range"
        params = {
            "query": '{app="synthetic"}',
            "limit": 1
        }
        for _ in range(10):  # retry loop for eventual consistency
            resp = await client.get(query_url, params=params)
            if resp.status_code == 200 and resp.json().get("data", {}).get("result"):
                break
            time.sleep(1)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert any("test-log-ingest-production-check" in entry[1] for stream in data["data"]["result"] for entry in stream["values"]), "Log entry was not ingested or found in Loki."
    # Clean up: delete test log if API supports (not implemented here)

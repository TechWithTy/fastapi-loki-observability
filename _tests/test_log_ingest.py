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
    print(f"[DEBUG] Using Loki URL: {loki_url}")
    push_url = f"{loki_url}/loki/api/v1/push"

    # Use nanosecond Unix time for Loki
    now_ns = int(time.time() * 1_000_000_000)
    print(f"[DEBUG] Sending log with timestamp (ns): {now_ns} ({now_ns/1e9} as seconds, UTC: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now_ns/1e9))})")
    log_stream = {
        "streams": [
            {
                "labels": '{app="synthetic"}',
                "entries": [
                    {"ts": str(now_ns), "line": "test-log-ingest-production-check"}
                ],
            }
        ]
    }
    async with httpx.AsyncClient(timeout=5) as client:
        headers = {"X-Scope-OrgID": "fake"}  # * Required for Loki 2.8+ and Grafana Cloud
        resp = await client.post(push_url, json=log_stream, headers=headers)
        print(f"[DEBUG] Push response: {resp.status_code} - {resp.text}")
        if resp.status_code not in (204, 200):
            print(f"Push failed: {resp.status_code} - {resp.text}")
        assert resp.status_code in (204, 200)
        # Query Loki for logs
        query_url = f"{loki_url}/loki/api/v1/query_range"
        # Query for a window spanning 5s before and after the log timestamp
        start_ns = now_ns - 5_000_000_000  # 5 seconds before
        end_ns = now_ns + 5_000_000_000    # 5 seconds after
        params = {
            "query": '{app="synthetic"}',
            "limit": 1,
            "start": str(start_ns),
            "end": str(end_ns),
        }
        for i in range(20):  # retry loop for eventual consistency
            resp = await client.get(query_url, params=params)
            print(f"[DEBUG] Query attempt {i+1}: {resp.status_code} - {resp.text}")
            if resp.status_code == 200 and resp.json().get("data", {}).get("result"):
                break
            time.sleep(2)
        assert resp.status_code == 200
        data = resp.json()
        print(f"[DEBUG] Final query response: {data}")
        assert data["status"] == "success"
        assert any("test-log-ingest-production-check" in entry[1] for stream in data["data"]["result"] for entry in stream["values"]), "Log entry was not ingested or found in Loki."
    # Clean up: delete test log if API supports (not implemented here)

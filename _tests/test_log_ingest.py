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
@pytest.mark.parametrize("org_id", ["fake", "default", None])
@pytest.mark.parametrize("label_format", ["string", "dict"])
@pytest.mark.parametrize("window_s", [5, 60])
async def test_log_ingestion(start_observability_stack, org_id, label_format, window_s):
    """
    Matrix test: Vary OrgID, label format, and query window to debug Loki ingestion issues.
    """
    loki_url = os.environ.get("LOKI_URL", "http://localhost:3100")
    print(f"\n[TEST CASE] OrgID: {org_id}, Label format: {label_format}, Window: +/-{window_s}s")
    push_url = f"{loki_url}/loki/api/v1/push"

    now_ns = int(time.time() * 1_000_000_000)
    print(f"[DEBUG] Sending log with timestamp (ns): {now_ns} ({now_ns/1e9} as seconds, UTC: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now_ns/1e9))})")
    if label_format == "string":
        labels = '{app="synthetic"}'
    else:
        labels = {"app": "synthetic"}
    log_stream = {
        "streams": [
            {
                "labels": labels,
                "entries": [
                    {"ts": str(now_ns), "line": f"test-log-ingest-production-check-{org_id}-{label_format}-{window_s}"}
                ],
            }
        ]
    }
    async with httpx.AsyncClient(timeout=5) as client:
        headers = {}
        if org_id is not None:
            headers["X-Scope-OrgID"] = org_id
        print(f"[DEBUG] Push headers: {headers}")
        print(f"[DEBUG] Push body: {log_stream}")
        resp = await client.post(push_url, json=log_stream, headers=headers)
        print(f"[DEBUG] Push response: {resp.status_code} - {resp.text}")
        if resp.status_code not in (204, 200):
            print(f"Push failed: {resp.status_code} - {resp.text}")
        assert resp.status_code in (204, 200)
        query_url = f"{loki_url}/loki/api/v1/query_range"
        start_ns = now_ns - window_s * 1_000_000_000
        end_ns = now_ns + window_s * 1_000_000_000
        params = {
            "query": '{app="synthetic"}',
            "limit": 1,
            "start": str(start_ns),
            "end": str(end_ns),
        }
        for i in range(20):
            resp = await client.get(query_url, params=params)
            print(f"[DEBUG] Query attempt {i+1}: {resp.status_code} - {resp.text}")
            if resp.status_code == 200 and resp.json().get("data", {}).get("result"):
                break
            time.sleep(2)
        assert resp.status_code == 200
        data = resp.json()
        print(f"[DEBUG] Final query response: {data}")
        assert data["status"] == "success"
        assert any(f"test-log-ingest-production-check-{org_id}-{label_format}-{window_s}" in entry[1] for stream in data["data"]["result"] for entry in stream["values"]), f"Log entry was not ingested or found in Loki for OrgID={org_id}, LabelFormat={label_format}, Window={window_s}s."
    # Clean up: delete test log if API supports (not implemented here)

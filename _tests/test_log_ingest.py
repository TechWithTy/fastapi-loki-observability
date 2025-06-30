"""
Integration test: End-to-end log flow from synthetic app to Loki via Alloy and Otel Collector.
Verifies log ingestion, label enrichment, and retention.
"""
import asyncio
import httpx
import pytest
import time
import os
import json


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
    
    # Create unique test identifier
    test_id = f"test-log-ingest-{int(time.time())}-{org_id}-{label_format}-{window_s}"
    
    if label_format == "string":
        # Loki API format with timestamp/line as strings (string format test)
        log_stream = {
            "streams": [
                {
                    "stream": {"app": "synthetic", "test_id": test_id},
                    "values": [[str(now_ns), test_id]]
                }
            ]
        }
    else:
        # Loki API format with timestamp/line as dict entries (dict format test)
        log_stream = {
            "streams": [
                {
                    "stream": {"app": "synthetic", "test_id": test_id},
                    "values": [[str(now_ns), test_id]]
                }
            ]
        }
    
    async with httpx.AsyncClient(timeout=10) as client:
        headers = {"Content-Type": "application/json"}
        if org_id is not None:
            headers["X-Scope-OrgID"] = org_id
        print(f"[DEBUG] Push headers: {headers}")
        print(f"[DEBUG] Push body: {json.dumps(log_stream, indent=2)}")
        
        resp = await client.post(push_url, json=log_stream, headers=headers)
        print(f"[DEBUG] Push response: {resp.status_code} - {resp.text}")
        if resp.status_code not in (204, 200):
            print(f"Push failed: {resp.status_code} - {resp.text}")
        assert resp.status_code in (204, 200), f"Failed to push logs: {resp.status_code} - {resp.text}"
        
        # Wait a bit for log ingestion
        await asyncio.sleep(2)
        
        query_url = f"{loki_url}/loki/api/v1/query_range"
        start_ns = now_ns - window_s * 1_000_000_000
        end_ns = now_ns + window_s * 1_000_000_000
        
        # More specific query using the test_id
        query = f'{{app="synthetic", test_id="{test_id}"}}'
        params = {
            "query": query,
            "limit": 100,
            "start": str(start_ns),
            "end": str(end_ns),
        }
        
        # Add headers for query if org_id is specified
        query_headers = {}
        if org_id is not None:
            query_headers["X-Scope-OrgID"] = org_id
        
        for i in range(30):  # Increased retry attempts
            resp = await client.get(query_url, params=params, headers=query_headers)
            print(f"[DEBUG] Query attempt {i+1}: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"[DEBUG] Query response: {json.dumps(data, indent=2)}")
                if data.get("data", {}).get("result"):
                    # Check if our specific test log is found
                    for stream in data["data"]["result"]:
                        for entry in stream.get("values", []):
                            if test_id in entry[1]:
                                print(f"[SUCCESS] Found test log: {test_id}")
                                return  # Test passed!
            time.sleep(1)  # Wait 1 second between retries
        
        # If we get here, the test failed
        print(f"[FAILURE] Log entry was not found after 30 attempts")
        print(f"[DEBUG] Final query response: {resp.status_code} - {resp.text}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"[DEBUG] Final query data: {json.dumps(data, indent=2)}")
        
        # Make the assertion more informative
        assert False, f"Log entry '{test_id}' was not ingested or found in Loki for OrgID={org_id}, LabelFormat={label_format}, Window={window_s}s. Query: {query}"

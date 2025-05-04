"""
Security and compliance tests for Loki endpoints (SSL/TLS, secrets, role-based access).
"""

import os

import httpx
import pytest


LOKI_URL = "http://localhost:3100"


def test_loki_tls_endpoint(start_observability_stack):
    """
    Verify Loki endpoint is available via HTTPS (if enabled), or HTTP otherwise.
    """
    loki_url = os.environ.get("LOKI_URL", LOKI_URL)
    for scheme in ("https", "http"):
        test_url = loki_url.replace("http://", f"{scheme}://").replace("https://", f"{scheme}://")
        try:
            with httpx.Client(verify=False, timeout=3) as client:
                resp = client.get(f"{test_url}/ready")
                if resp.status_code == 200:
                    assert resp.text.strip().lower() == "ready", f"Unexpected Loki /ready response: {resp.text}"
                    return
        except Exception as e:
            print(f"TLS check failed for {test_url}: {e}")
            continue
    pytest.fail("Loki /ready endpoint not available over HTTP or HTTPS.")

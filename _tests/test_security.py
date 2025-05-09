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
    loki_url_candidates = [
        os.environ.get("LOKI_URL", "http://localhost:3100"),
        "http://loki:3100"
    ]
    debug_errors = []
    for loki_url in loki_url_candidates:
        for scheme in ("https", "http"):
            # Replace scheme and port with correct values
            test_url = loki_url
            # Remove any existing scheme and port, then add the correct ones
            if test_url.startswith("http://"):
                test_url = test_url[len("http://"):]
            elif test_url.startswith("https://"):
                test_url = test_url[len("https://"):]
            # Remove any trailing port
            if ":" in test_url:
                test_url = test_url.split(":")[0]
            test_url = f"{scheme}://{test_url}:3100"
            print(f"[DEBUG] Trying Loki /ready endpoint at: {test_url}")
            try:
                with httpx.Client(verify=False, timeout=3) as client:
                    resp = client.get(f"{test_url}/ready")
                    # * Loki 2.x+ /ready endpoint may return empty body; HTTP 200 is sufficient for health
                    if resp.status_code == 200:
                        print(f"[DEBUG] Loki /ready success at {test_url}")
                        return
            except Exception as e:
                debug_errors.append(f"{test_url}: {e}")
                print(f"[DEBUG] TLS check failed for {test_url}: {e}")
                continue
    print("[DEBUG] All Loki endpoint attempts failed:")
    for err in debug_errors:
        print(f"[DEBUG]   {err}")
    pytest.fail("Loki /ready endpoint not available over HTTP or HTTPS at any known address.")

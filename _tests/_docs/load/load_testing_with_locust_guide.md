# Load Testing Grafana Loki with Locust

## Overview
This guide explains how to perform production-grade load testing on your Loki deployment using [Locust](https://locust.io/), inspired by the k6-based approach in the [k6 load testing guide](./load_testing_with_k6guide.md). Locust allows you to simulate concurrent log ingestion and query scenarios using Python, offering flexibility for custom test logic and integration with your existing Python-based test stack.

## Why Use Locust for Loki?
- **Python-native**: Integrates with your FastAPI/Python ecosystem.
- **Customizable**: Write custom user behavior for log ingestion, queries, and authentication.
- **Distributed**: Easily scale to thousands of concurrent users.
- **Metrics**: Real-time metrics and reporting, with support for Prometheus/Grafana integration.

## Prerequisites
- A running Loki instance (local or remote)
- Python 3.9+
- `locust`, `httpx`, and `python-dotenv` installed:
  ```bash
  pip install locust httpx python-dotenv
  ```
- (Optional) Access to your FastAPI settings/config for dynamic environment and port loading

## Example Locustfile for Loki Write Path
```python
import os
from locust import HttpUser, task, between
import httpx
import random
import string

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

class LokiWriteUser(HttpUser):
    wait_time = between(0.1, 1)

    @task
    def push_logs(self):
        # Simulate log streams with random labels and content
        streams = [
            {
                "stream": {
                    "app": "loadtest",
                    "instance": f"vu-{self.environment.runner.user_count}",
                    "format": "json"
                },
                "values": [
                    [str(int(httpx.Timestamp.now().timestamp() * 1e9)), self._random_log_line()]
                    for _ in range(random.randint(5, 20))
                ]
            }
        ]
        payload = {"streams": streams}
        with self.client.post("/loki/api/v1/push", json=payload, catch_response=True) as resp:
            if resp.status_code != 204:
                resp.failure(f"Failed to push logs: {resp.text}")

    def _random_log_line(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=120))
```

## Example Locustfile for Loki Query Path
```python
from locust import HttpUser, task, between
import os
import random

LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")

class LokiQueryUser(HttpUser):
    wait_time = between(0.2, 2)

    @task
    def query_logs(self):
        query = '{app="loadtest"}'
        params = {"query": query, "limit": random.randint(1, 100)}
        with self.client.get("/loki/api/v1/query_range", params=params, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Query failed: {resp.text}")
```

## Running the Test
1. Export the correct Loki URL (or ensure your `.env` is loaded):
   ```bash
   export LOKI_URL=http://localhost:3100
   ```
2. Start Locust:
   ```bash
   locust -f locustfile_write.py --users 100 --spawn-rate 10
   # Or for query testing:
   locust -f locustfile_query.py --users 50 --spawn-rate 5
   ```
3. Open the Locust web UI at [http://localhost:8089](http://localhost:8089) to monitor and control the test.

## Best Practices (from k6 Reference)
- Simulate realistic log ingestion rates and query patterns.
- Randomize labels, stream counts, and log sizes for each request.
- Monitor Loki resource usage and error rates during tests.
- Use environment variables or FastAPI settings to dynamically load correct ports and URLs.
- Clean up test data if possible.
- Combine with Prometheus/Grafana dashboards for real-time observability.

## Advanced Tips
- Use [locust-plugins](https://github.com/SvenskaSpel/locust-plugins) for more protocols or metrics.
- Parameterize test duration, user count, and log/query complexity via environment or CLI.
- Integrate with CI/CD for automated performance regression testing.

## References
- [k6 Loki Load Testing Guide](./load_testing_with_k6guide.md)
- [Locust Documentation](https://docs.locust.io/en/stable/)
- [Grafana Loki API](https://grafana.com/docs/loki/latest/api/)
- [xk6-loki](https://github.com/grafana/xk6-loki) (for Go/k6-based load testing)

# Loki Integration Usage Guide

This guide explains how to use the Loki integration in your FastAPI application for log aggregation and querying.

## Quick Start

### 1. Initialize Loki in your FastAPI app

```python
from fastapi import FastAPI
from app.core.loki import init_loki, add_request_logging_middleware

app = FastAPI()

# Initialize Loki integration
loki_client = init_loki(app, enable_handler=True)

# Optional: Add HTTP request logging
add_request_logging_middleware(app)
```

### 2. Use Loki for logging

```python
import logging
from app.core.loki import get_loki_client

# Standard logging (automatically sent to Loki)
logger = logging.getLogger(__name__)
logger.info("This log will be sent to Loki")
logger.error("Error logs are also captured")

# Direct Loki client usage
loki_client = get_loki_client()
await loki_client.push_logs([
    {
        "timestamp": datetime.now(timezone.utc),
        "message": "Direct log to Loki",
        "custom_field": "custom_value"
    }
], labels={"service": "my-service", "environment": "production"})
```

## API Endpoints

The Loki integration provides several API endpoints under `/api/v1/loki/`:

### Health Check
```bash
GET /api/v1/loki/health
```
Returns health status of Loki and Grafana services.

### Query Logs
```bash
# Simple query
GET /api/v1/loki/query/simple?query={service="fastapi-connect"}&hours=1&limit=100

# Advanced query
POST /api/v1/loki/query
{
    "query": "{service=\"fastapi-connect\"} |= \"ERROR\"",
    "start": "2023-01-01T00:00:00Z",
    "end": "2023-01-01T23:59:59Z",
    "limit": 1000,
    "direction": "backward"
}
```

### Push Logs
```bash
POST /api/v1/loki/push
{
    "logs": [
        {
            "message": "Custom log message",
            "level": "INFO",
            "custom_field": "value"
        }
    ],
    "labels": {
        "service": "my-service",
        "environment": "production"
    }
}
```

### Get Labels
```bash
GET /api/v1/loki/labels
```
Returns available labels in Loki.

### Test Integration
```bash
GET /api/v1/loki/test
```
Tests the Loki integration and pushes a test log.

### Query Examples
```bash
GET /api/v1/loki/examples
```
Returns example LogQL queries and documentation.

## LogQL Query Examples

### Basic Filtering
```logql
# All logs from a service
{service="fastapi-connect"}

# Error logs only
{service="fastapi-connect"} |= "ERROR"

# Logs from specific endpoint
{service="fastapi-connect"} |= "/api/users"
```

### JSON Log Parsing
```logql
# Parse JSON and filter by field
{service="fastapi-connect"} | json | level="ERROR"

# Filter by JSON field value
{service="fastapi-connect"} | json | http_status_code > 400
```

### Time-based Queries
```logql
# Logs from last hour (handled by API time parameters)
{service="fastapi-connect"}[1h]

# Count logs per minute
count_over_time({service="fastapi-connect"}[1m])
```

### Regular Expressions
```logql
# Regex filter
{service="fastapi-connect"} |~ "user_id=\\d+"

# Negative regex
{service="fastapi-connect"} !~ "health.*check"
```

## Configuration

Configure Loki integration through environment variables:

```bash
# Loki settings
LOKI_URL=http://localhost:3100
LOKI_PORT=3100
LOKI_TENANT_ID=my-tenant  # Optional for multi-tenant setups

# Grafana settings (for health checks)
GRAFANA_URL=http://localhost:3000
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

## Docker Setup

Use the provided Docker Compose file to run Loki:

```bash
# Start Loki
docker-compose -f app/core/loki/docker/docker-compose.loki.yml up -d

# Verify Loki is running
curl http://localhost:3100/ready
```

## Integration with Existing Observability

The Loki integration works seamlessly with existing observability tools:

### Tempo (Distributed Tracing)
- Logs are automatically correlated with traces using trace IDs
- Each log operation is traced for performance monitoring

### Prometheus (Metrics)
- HTTP request metrics are collected alongside logs
- Loki client operations are instrumented with metrics

### Grafana (Visualization)
- Logs can be visualized in Grafana dashboards
- Correlation with metrics and traces in unified dashboards

## Log Labels

Default labels automatically added to logs:

- `service`: Service name (from SERVICE_NAME env var)
- `environment`: Environment (from ENVIRONMENT env var)
- `instance`: Instance identifier (from HOSTNAME env var)
- `log_type`: Type of log (e.g., "http_request", "application")

Additional labels can be added when pushing logs:

```python
await loki_client.push_logs(logs, labels={
    "module": "user_management",
    "version": "1.2.3",
    "region": "us-west-2"
})
```

## Best Practices

### 1. Structured Logging
Use structured logging with consistent field names:

```python
logger.info("User login", extra={
    "user_id": user.id,
    "email": user.email,
    "login_method": "password",
    "ip_address": request.client.host
})
```

### 2. Appropriate Log Levels
- `DEBUG`: Detailed debugging information
- `INFO`: General application flow
- `WARNING`: Potentially harmful situations
- `ERROR`: Error events that might still allow the application to continue

### 3. Performance Considerations
- Logs are batched automatically for performance
- Avoid logging sensitive information (passwords, tokens, etc.)
- Use appropriate log levels to control volume

### 4. Query Optimization
- Use specific labels to narrow down queries
- Avoid overly broad time ranges
- Use the `limit` parameter to control result size

## Troubleshooting

### Loki Not Available
If Loki is not running, the integration will:
- Log warnings but continue application startup
- Return appropriate HTTP error codes from API endpoints
- Buffer logs locally (limited capacity)

### Common Issues

1. **Connection Failed**: Check LOKI_URL and ensure Loki is running
2. **422 Validation Error**: Check log format and required fields
3. **No Logs Appearing**: Verify labels and time ranges in queries
4. **Performance Issues**: Check log volume and batch sizes

### Health Check
Use the health endpoint to verify integration:

```bash
curl http://localhost:8000/api/v1/loki/health
```

## Example Implementation

Complete example of integrating Loki in a FastAPI application:

```python
from fastapi import FastAPI, Request
from app.core.loki import init_loki, add_request_logging_middleware
import logging

app = FastAPI(title="My App")

# Initialize Loki
loki_client = init_loki(app, enable_handler=True)
add_request_logging_middleware(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

@app.post("/users")
async def create_user(user_data: dict):
    logger.info("Creating user", extra={
        "user_email": user_data.get("email"),
        "operation": "user_creation"
    })
    # ... user creation logic
    return {"status": "created"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This setup provides comprehensive logging with automatic log shipping to Loki, HTTP request logging, and full observability integration.

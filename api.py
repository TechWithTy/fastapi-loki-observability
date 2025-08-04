"""
API endpoints for Loki log management and querying.
Provides endpoints to query logs, check health, and manage log streaming.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.core.loki import get_loki_client, LokiQueryResponse
from app.core.loki.health import LokiHealthCheck, GrafanaHealthCheck


router = APIRouter()


class LogQuery(BaseModel):
    """Request model for log queries."""
    query: str = Field(description="LogQL query string")
    start: Optional[datetime] = Field(None, description="Start time for query range")
    end: Optional[datetime] = Field(None, description="End time for query range")
    limit: int = Field(100, description="Maximum number of entries to return", ge=1, le=5000)
    direction: str = Field("backward", description="Query direction", pattern="^(forward|backward)$")


class LogPushRequest(BaseModel):
    """Request model for pushing logs."""
    logs: List[Dict[str, Any]] = Field(description="List of log entries")
    labels: Optional[Dict[str, str]] = Field(None, description="Additional labels for logs")


class HealthResponse(BaseModel):
    """Response model for health checks."""
    service: str
    status: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


@router.get("/health", response_model=List[HealthResponse])
async def get_health_status():
    """
    Get health status of Loki and related services.
    
    Returns:
        List of health check results for each service
    """
    health_checks = []
    
    # Loki health check - call async method directly
    loki_health = await LokiHealthCheck._async_check()
    health_checks.append(HealthResponse(
        service="loki",
        status=loki_health.get("status", "unknown"),
        details=loki_health.get("details"),
        error=loki_health.get("error"),
        status_code=loki_health.get("status_code")
    ))
    
    # Grafana health check - call async method directly
    grafana_health = await GrafanaHealthCheck._async_check()
    health_checks.append(HealthResponse(
        service="grafana",
        status=grafana_health.get("status", "unknown"),
        details=grafana_health.get("details"),
        error=grafana_health.get("error"),
        status_code=grafana_health.get("status_code")
    ))
    
    return health_checks


@router.post("/query", response_model=Optional[LokiQueryResponse])
async def query_logs(query_request: LogQuery):
    """
    Query logs from Loki using LogQL.
    
    Args:
        query_request: Query parameters including LogQL query string and time range
        
    Returns:
        Query results from Loki
    """
    try:
        loki_client = get_loki_client()
        
        result = await loki_client.query_logs(
            query=query_request.query,
            start=query_request.start,
            end=query_request.end,
            limit=query_request.limit,
            direction=query_request.direction
        )
        
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to query logs from Loki")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")


@router.get("/query/simple")
async def simple_log_query(
    query: str = Query(description="LogQL query string"),
    hours: int = Query(1, description="Number of hours to look back", ge=1, le=168),
    limit: int = Query(100, description="Maximum number of entries", ge=1, le=1000)
):
    """
    Simple log query endpoint with time range specified in hours.
    
    Args:
        query: LogQL query string (e.g., '{service="fastapi-connect"}')
        hours: Number of hours to look back from now
        limit: Maximum number of log entries to return
        
    Returns:
        Query results from Loki
    """
    try:
        loki_client = get_loki_client()
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        result = await loki_client.query_logs(
            query=query,
            start=start_time,
            end=end_time,
            limit=limit,
            direction="backward"
        )
        
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to query logs from Loki")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")


@router.post("/push")
async def push_logs(push_request: LogPushRequest):
    """
    Push logs to Loki.
    
    Args:
        push_request: Logs and labels to push to Loki
        
    Returns:
        Success status
    """
    try:
        loki_client = get_loki_client()
        
        # Add timestamp to logs if not present
        processed_logs = []
        for log in push_request.logs:
            if "timestamp" not in log:
                log["timestamp"] = datetime.now(timezone.utc)
            processed_logs.append(log)
        
        result = await loki_client.push_logs(
            logs=processed_logs,
            labels=push_request.labels
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to push logs to Loki")
        
        return {"status": "success", "logs_pushed": len(processed_logs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pushing logs: {str(e)}")


@router.get("/labels")
async def get_available_labels():
    """
    Get available labels from Loki.
    
    Returns:
        List of available label names
    """
    try:
        loki_client = get_loki_client()
        
        labels = await loki_client.get_labels()
        
        if labels is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve labels from Loki")
        
        return {"labels": labels}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving labels: {str(e)}")


@router.get("/test")
async def test_loki_integration():
    """
    Test endpoint to verify Loki integration is working.
    
    Returns:
        Test results including health check and sample log push
    """
    try:
        loki_client = get_loki_client()
        
        # Health check
        healthy = await loki_client.health_check()
        
        # Push a test log
        test_logs = [{
            "timestamp": datetime.now(timezone.utc),
            "message": f"Test log from Loki API endpoint - {datetime.now().isoformat()}",
            "level": "INFO",
            "source": "loki_api_test"
        }]
        
        push_result = await loki_client.push_logs(
            logs=test_logs,
            labels={"test": "api", "source": "integration_test"}
        )
        
        return {
            "loki_healthy": healthy,
            "test_log_pushed": push_result,
            "test_timestamp": datetime.now().isoformat(),
            "message": "Loki integration test completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


# Example queries for documentation
EXAMPLE_QUERIES = {
    "all_logs": '{service="fastapi-connect"}',
    "error_logs": '{service="fastapi-connect"} |= "ERROR"',
    "api_requests": '{log_type="http_request"}',
    "recent_errors": '{service="fastapi-connect"} | json | level="ERROR"',
    "slow_requests": '{log_type="http_request"} | json | http_duration > 1.0'
}


@router.get("/examples")
async def get_query_examples():
    """
    Get example LogQL queries for common use cases.
    
    Returns:
        Dictionary of example queries with descriptions
    """
    return {
        "examples": EXAMPLE_QUERIES,
        "documentation": {
            "logql_guide": "https://grafana.com/docs/loki/latest/logql/",
            "common_patterns": {
                "filter_by_service": '{service="your-service"}',
                "search_text": '{service="your-service"} |= "search term"',
                "json_field": '{service="your-service"} | json | field="value"',
                "regex_filter": '{service="your-service"} |~ "regex.*pattern"',
                "time_range": "Use start/end parameters for time ranges"
            }
        }
    }

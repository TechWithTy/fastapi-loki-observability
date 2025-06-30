"""
Core Loki implementation for log aggregation and querying.
Integrates with existing telemetry, tempo, and FastAPI infrastructure.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import FastAPI, Request
from opentelemetry import trace
from pydantic import BaseModel, Field

from app.core.loki import config
from app.core.loki.exceptions.exceptions import APIError
from app.core.loki.models.index import LokiConfig


logger = logging.getLogger(__name__)


class LogEntry(BaseModel):
    """Individual log entry for Loki ingestion."""
    timestamp: str = Field(description="Timestamp in nanoseconds since epoch")
    line: str = Field(description="Log message content")


class LogStream(BaseModel):
    """Log stream with labels and entries for Loki push API."""
    stream: Dict[str, str] = Field(description="Labels for the log stream")
    values: List[List[str]] = Field(description="List of [timestamp, line] pairs")


class LokiPushRequest(BaseModel):
    """Loki push API request format."""
    streams: List[LogStream] = Field(description="List of log streams")


class LokiQueryResponse(BaseModel):
    """Loki query API response format."""
    status: str = Field(description="Query status")
    data: Dict[str, Any] = Field(description="Query result data")


class LokiClient:
    """
    Loki client for log ingestion and querying.
    Integrates with existing FastAPI telemetry infrastructure.
    """
    
    def __init__(
        self,
        loki_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Loki client.
        
        Args:
            loki_url: Loki base URL (defaults to config.LOKI_URL)
            tenant_id: Multi-tenant Loki tenant ID
            timeout: HTTP request timeout in seconds
            headers: Additional HTTP headers
        """
        self.loki_url = loki_url or config.LOKI_URL
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.headers = headers or {}
        
        # Add tenant header if specified
        if self.tenant_id:
            self.headers["X-Scope-OrgID"] = self.tenant_id
            
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers
        )
        
        # Get tracer for tracing Loki operations
        self.tracer = trace.get_tracer(__name__)
        
        logger.info(f"Initialized Loki client with URL: {self.loki_url}")
    
    async def push_logs(
        self,
        logs: List[Dict[str, Any]],
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Push logs to Loki.
        
        Args:
            logs: List of log entries with 'timestamp' and 'message' keys
            labels: Additional labels for the log stream
            
        Returns:
            True if successful, False otherwise
        """
        with self.tracer.start_as_current_span("loki_push_logs") as span:
            try:
                # Prepare default labels
                default_labels = {
                    "service": os.getenv("SERVICE_NAME", "fastapi-connect"),
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "instance": os.getenv("HOSTNAME", "unknown")
                }
                
                # Merge with provided labels
                stream_labels = {**default_labels, **(labels or {})}
                
                # Convert logs to Loki format
                values = []
                for log in logs:
                    timestamp = log.get("timestamp")
                    if isinstance(timestamp, datetime):
                        # Convert datetime to nanoseconds since epoch
                        timestamp_ns = str(int(timestamp.timestamp() * 1_000_000_000))
                    elif isinstance(timestamp, (int, float)):
                        # Assume it's already in seconds, convert to nanoseconds
                        timestamp_ns = str(int(timestamp * 1_000_000_000))
                    else:
                        # Use current time if timestamp is invalid
                        timestamp_ns = str(int(time.time() * 1_000_000_000))
                    
                    message = log.get("message", str(log))
                    values.append([timestamp_ns, message])
                
                # Create Loki push request
                push_request = LokiPushRequest(
                    streams=[
                        LogStream(
                            stream=stream_labels,
                            values=values
                        )
                    ]
                )
                
                # Send to Loki
                url = f"{self.loki_url}/loki/api/v1/push"
                response = await self.client.post(
                    url,
                    json=push_request.model_dump(),
                    headers={"Content-Type": "application/json"}
                )
                
                # Add span attributes
                span.set_attribute("loki.url", url)
                span.set_attribute("loki.logs_count", len(logs))
                span.set_attribute("loki.response_status", response.status_code)
                
                if response.status_code == 204:
                    logger.debug(f"Successfully pushed {len(logs)} logs to Loki")
                    return True
                else:
                    logger.error(f"Failed to push logs to Loki: {response.status_code} - {response.text}")
                    span.set_attribute("loki.error", response.text)
                    return False
                    
            except Exception as e:
                logger.error(f"Error pushing logs to Loki: {str(e)}")
                span.set_attribute("loki.error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return False
    
    async def query_logs(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
        direction: str = "backward"
    ) -> Optional[LokiQueryResponse]:
        """
        Query logs from Loki.
        
        Args:
            query: LogQL query string
            start: Start time for query range
            end: End time for query range
            limit: Maximum number of entries to return
            direction: Query direction ("forward" or "backward")
            
        Returns:
            Query response or None if failed
        """
        with self.tracer.start_as_current_span("loki_query_logs") as span:
            try:
                # Prepare query parameters
                params = {
                    "query": query,
                    "limit": limit,
                    "direction": direction
                }
                
                # Add time range if specified
                if start:
                    params["start"] = str(int(start.timestamp() * 1_000_000_000))
                if end:
                    params["end"] = str(int(end.timestamp() * 1_000_000_000))
                
                # Send query to Loki
                url = f"{self.loki_url}/loki/api/v1/query_range"
                response = await self.client.get(url, params=params)
                
                # Add span attributes
                span.set_attribute("loki.query", query)
                span.set_attribute("loki.limit", limit)
                span.set_attribute("loki.response_status", response.status_code)
                
                if response.status_code == 200:
                    # Parse JSON response asynchronously
                    result = await response.json()
                    logger.debug(f"Successfully queried Loki: {len(result.get('data', {}).get('result', []))} streams")
                    return LokiQueryResponse(
                        status=result.get("status", "success"),
                        data=result.get("data", {})
                    )
                else:
                    logger.error(f"Failed to query Loki: {response.status_code} - {response.text}")
                    span.set_attribute("loki.error", response.text)
                    return None
                    
            except Exception as e:
                logger.error(f"Error querying Loki: {str(e)}")
                span.set_attribute("loki.error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return None
    
    async def get_labels(self) -> Optional[List[str]]:
        """
        Get available labels from Loki.
        
        Returns:
            List of label names or None if failed
        """
        with self.tracer.start_as_current_span("loki_get_labels") as span:
            try:
                url = f"{self.loki_url}/loki/api/v1/labels"
                response = await self.client.get(url)
                
                span.set_attribute("loki.response_status", response.status_code)
                
                if response.status_code == 200:
                    # Parse JSON response asynchronously  
                    try:
                        if hasattr(response, 'json'):
                            json_method = response.json()
                            if hasattr(json_method, '__await__'):
                                result = await json_method
                            else:
                                result = json_method
                        else:
                            result = response.json()
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        return None
                        
                    labels = result.get("data", [])
                    logger.debug(f"Retrieved {len(labels)} labels from Loki")
                    return labels
                else:
                    logger.error(f"Failed to get labels from Loki: {response.status_code} - {response.text}")
                    span.set_attribute("loki.error", response.text)
                    return None
                    
            except Exception as e:
                logger.error(f"Error getting labels from Loki: {str(e)}")
                span.set_attribute("loki.error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return None
    
    async def health_check(self) -> bool:
        """
        Check Loki health status.
        
        Returns:
            True if Loki is healthy, False otherwise
        """
        try:
            url = f"{self.loki_url}/ready"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Loki health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class FastAPILokiHandler(logging.Handler):
    """
    Custom logging handler that sends logs to Loki.
    Integrates with FastAPI request context for enhanced logging.
    """
    
    def __init__(self, loki_client: LokiClient, level: int = logging.INFO):
        """
        Initialize the Loki logging handler.
        
        Args:
            loki_client: Loki client instance
            level: Minimum logging level
        """
        super().__init__(level)
        self.loki_client = loki_client
        self.log_buffer = []
        self.buffer_size = 100
        self.last_flush = time.time()
        self.flush_interval = 10  # seconds
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to Loki.
        
        Args:
            record: Log record to emit
        """
        try:
            # Format the log message
            message = self.format(record)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc),
                "message": message,
                "level": record.levelname,
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Flush if buffer is full or time interval exceeded
            if (len(self.log_buffer) >= self.buffer_size or 
                time.time() - self.last_flush >= self.flush_interval):
                self.flush_async()
                
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error in Loki handler: {str(e)}")
    
    def flush_async(self):
        """Flush log buffer to Loki asynchronously."""
        if self.log_buffer:
            # Create a copy of the buffer and clear it
            logs_to_send = self.log_buffer.copy()
            self.log_buffer.clear()
            self.last_flush = time.time()
            
            # Send logs in the background safely
            try:
                import asyncio
                # Check if we're in an async context
                try:
                    loop = asyncio.get_running_loop()
                    # Create task in the current event loop
                    asyncio.create_task(self.loki_client.push_logs(logs_to_send))
                except RuntimeError:
                    # No event loop running, create a new one for this operation
                    asyncio.run(self.loki_client.push_logs(logs_to_send))
            except Exception as e:
                print(f"Error flushing logs to Loki: {str(e)}")
                # Re-add logs to buffer for retry if sending failed
                self.log_buffer.extend(logs_to_send)


# Global Loki client instance
_loki_client: Optional[LokiClient] = None


def get_loki_client() -> LokiClient:
    """
    Get the global Loki client instance.
    
    Returns:
        Loki client instance
        
    Raises:
        RuntimeError: If Loki client is not initialized
    """
    global _loki_client
    if _loki_client is None:
        raise RuntimeError("Loki client not initialized. Call init_loki() first.")
    return _loki_client


def init_loki(
    app: FastAPI,
    loki_url: Optional[str] = None,
    tenant_id: Optional[str] = None,
    enable_handler: bool = True
) -> LokiClient:
    """
    Initialize Loki client and integrate with FastAPI application.
    
    Args:
        app: FastAPI application instance
        loki_url: Loki base URL (defaults to config)
        tenant_id: Multi-tenant Loki tenant ID
        enable_handler: Whether to enable the logging handler
        
    Returns:
        Initialized Loki client
    """
    global _loki_client
    
    # Initialize Loki client
    _loki_client = LokiClient(
        loki_url=loki_url,
        tenant_id=tenant_id
    )
    
    # Add to app state for cleanup
    app.state.loki_client = _loki_client
    
    # Set up logging handler if enabled
    if enable_handler:
        handler = FastAPILokiHandler(_loki_client)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        logger.info("Loki logging handler enabled")
    
    # Note: Startup and shutdown events should be handled in main.py
    # to avoid middleware registration issues
    
    logger.info("Loki integration initialized")
    return _loki_client


def add_request_logging_middleware(app: FastAPI):
    """
    Add middleware to log HTTP requests to Loki.
    
    Args:
        app: FastAPI application instance
    """
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log HTTP requests with timing and response info."""
        start_time = time.time()
        
        # Get request info
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request details
        log_data = {
            "timestamp": datetime.now(timezone.utc),
            "message": f"{method} {url} - {response.status_code} - {duration:.3f}s",
            "http_method": method,
            "http_url": url,
            "http_status_code": response.status_code,
            "http_duration": duration,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Send to Loki if client is available
        try:
            loki_client = get_loki_client()
            await loki_client.push_logs([log_data], labels={
                "log_type": "http_request",
                "method": method,
                "status_code": str(response.status_code)
            })
        except Exception as e:
            # Don't let logging errors affect the response
            logger.debug(f"Failed to log request to Loki: {str(e)}")
        
        return response

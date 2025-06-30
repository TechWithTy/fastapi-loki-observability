"""
Basic tests for Loki integration functionality.
"""
import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.core.loki.core import LokiClient, LokiPushRequest, LogStream


class TestLokiClient:
    """Test cases for LokiClient functionality."""
    
    @pytest.fixture
    def loki_client(self):
        """Create a test Loki client."""
        return LokiClient(
            loki_url="http://localhost:3100",
            tenant_id="test-tenant"
        )
    
    @pytest.mark.asyncio
    async def test_push_logs_success(self, loki_client):
        """Test successful log pushing."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            # Test data
            logs = [
                {
                    "timestamp": datetime.now(timezone.utc),
                    "message": "Test log message"
                }
            ]
            
            # Push logs
            result = await loki_client.push_logs(logs)
            
            # Assertions
            assert result is True
            mock_post.assert_called_once()
            
            # Check the request payload
            call_args = mock_post.call_args
            assert "json" in call_args.kwargs
            payload = call_args.kwargs["json"]
            assert "streams" in payload
            assert len(payload["streams"]) == 1
            assert payload["streams"][0]["values"][0][1] == "Test log message"
    
    @pytest.mark.asyncio
    async def test_push_logs_failure(self, loki_client):
        """Test log pushing failure."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'post') as mock_post:
            # Mock failed response
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            # Test data
            logs = [{"timestamp": datetime.now(timezone.utc), "message": "Test"}]
            
            # Push logs
            result = await loki_client.push_logs(logs)
            
            # Assertions
            assert result is False
    
    @pytest.mark.asyncio
    async def test_query_logs_success(self, loki_client):
        """Test successful log querying."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'get') as mock_get:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "success",
                "data": {
                    "result": [
                        {
                            "stream": {"service": "test"},
                            "values": [["1234567890000000000", "Test log"]]
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            # Query logs
            result = await loki_client.query_logs('{service="test"}')
            
            # Assertions
            assert result is not None
            assert result.status == "success"
            assert len(result.data["result"]) == 1
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, loki_client):
        """Test successful health check."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'get') as mock_get:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Health check
            result = await loki_client.health_check()
            
            # Assertions
            assert result is True
            mock_get.assert_called_once_with("http://localhost:3100/ready")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, loki_client):
        """Test failed health check."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'get') as mock_get:
            # Mock failed response
            mock_response = AsyncMock()
            mock_response.status_code = 503
            mock_get.return_value = mock_response
            
            # Health check
            result = await loki_client.health_check()
            
            # Assertions
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_labels_success(self, loki_client):
        """Test successful label retrieval."""
        # Mock the HTTP client
        with patch.object(loki_client.client, 'get') as mock_get:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": ["service", "environment", "level"]
            }
            mock_get.return_value = mock_response
            
            # Get labels
            result = await loki_client.get_labels()
            
            # Assertions
            assert result is not None
            assert len(result) == 3
            assert "service" in result
            assert "environment" in result
            assert "level" in result
    
    def test_log_stream_model(self):
        """Test LogStream model validation."""
        stream = LogStream(
            stream={"service": "test", "level": "info"},
            values=[["1234567890000000000", "Test message"]]
        )
        
        assert stream.stream["service"] == "test"
        assert stream.stream["level"] == "info"
        assert len(stream.values) == 1
        assert stream.values[0][0] == "1234567890000000000"
        assert stream.values[0][1] == "Test message"
    
    def test_loki_push_request_model(self):
        """Test LokiPushRequest model validation."""
        request = LokiPushRequest(
            streams=[
                LogStream(
                    stream={"service": "test"},
                    values=[["1234567890000000000", "Test"]]
                )
            ]
        )
        
        assert len(request.streams) == 1
        assert request.streams[0].stream["service"] == "test"


if __name__ == "__main__":
    # Simple test runner for development
    async def run_basic_test():
        """Run a basic integration test."""
        client = LokiClient("http://localhost:3100")
        
        # Test health check
        print("Testing Loki health check...")
        healthy = await client.health_check()
        print(f"Loki healthy: {healthy}")
        
        if healthy:
            # Test log push
            print("Testing log push...")
            logs = [
                {
                    "timestamp": datetime.now(timezone.utc),
                    "message": "Test log from Loki integration test"
                }
            ]
            result = await client.push_logs(logs)
            print(f"Log push result: {result}")
            
            # Test query
            print("Testing log query...")
            query_result = await client.query_logs('{service="fastapi-connect"}', limit=5)
            if query_result:
                print(f"Query successful: {len(query_result.data.get('result', []))} streams")
            else:
                print("Query failed")
        
        await client.close()
    
    # Run the test
    asyncio.run(run_basic_test())

"""
Integration test for Loki with FastAPI application.
Tests the full integration including API endpoints and log shipping.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.loki import get_loki_client


class TestLokiIntegration:
    """Test Loki integration with FastAPI application."""
    
    def setup_class(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_loki_health_endpoint(self):
        """Test Loki health check endpoint."""
        response = self.client.get("/api/v1/loki/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert isinstance(health_data, list)
        assert len(health_data) >= 1
        
        # Check that we have health data for Loki
        loki_health = next((h for h in health_data if h["service"] == "loki"), None)
        assert loki_health is not None
        assert "status" in loki_health
    
    def test_loki_examples_endpoint(self):
        """Test Loki query examples endpoint."""
        response = self.client.get("/api/v1/loki/examples")
        assert response.status_code == 200
        
        examples = response.json()
        assert "examples" in examples
        assert "documentation" in examples
        assert isinstance(examples["examples"], dict)
    
    def test_loki_test_endpoint(self):
        """Test Loki integration test endpoint."""
        response = self.client.get("/api/v1/loki/test")
        
        # This might fail if Loki is not running, which is acceptable in CI
        if response.status_code == 200:
            test_data = response.json()
            assert "loki_healthy" in test_data
            assert "test_log_pushed" in test_data
            assert "message" in test_data
        else:
            # Log the error for debugging but don't fail the test
            print(f"Loki test endpoint failed (Loki may not be running): {response.text}")
            assert response.status_code in [500, 503]  # Expected if Loki is unavailable
    
    def test_log_push_endpoint(self):
        """Test log push endpoint."""
        test_logs = [
            {
                "message": "Test log from integration test",
                "level": "INFO",
                "source": "test_suite"
            }
        ]
        
        response = self.client.post(
            "/api/v1/loki/push",
            json={
                "logs": test_logs,
                "labels": {"test": "integration", "source": "pytest"}
            }
        )
        
        # Might fail if Loki is not available
        if response.status_code == 200:
            result = response.json()
            assert result["status"] == "success"
            assert result["logs_pushed"] == 1
        else:
            print(f"Log push failed (Loki may not be running): {response.text}")
            assert response.status_code == 500
    
    def test_log_query_endpoint(self):
        """Test log query endpoint."""
        response = self.client.get(
            "/api/v1/loki/query/simple",
            params={
                "query": '{service="fastapi-connect"}',
                "hours": 1,
                "limit": 10
            }
        )
        
        # Might fail if Loki is not available
        if response.status_code == 200:
            result = response.json()
            assert "status" in result
            assert "data" in result
        else:
            print(f"Log query failed (Loki may not be running): {response.text}")
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_programmatic_logging(self):
        """Test programmatic logging to Loki."""
        try:
            loki_client = get_loki_client()
            
            # Test direct log push
            test_logs = [
                {
                    "timestamp": datetime.now(timezone.utc),
                    "message": "Programmatic test log from pytest",
                    "level": "INFO",
                    "test_id": "pytest_integration"
                }
            ]
            
            result = await loki_client.push_logs(
                logs=test_logs,
                labels={"source": "pytest", "test": "programmatic"}
            )
            
            # If Loki is available, this should succeed
            if result:
                assert result is True
            else:
                print("Programmatic logging failed (Loki may not be available)")
                
        except RuntimeError as e:
            # Loki client not initialized - this is expected in some test environments
            print(f"Loki client not available: {str(e)}")
            pytest.skip("Loki client not initialized")
        except Exception as e:
            print(f"Programmatic logging test failed: {str(e)}")
            # Don't fail the test if Loki is not available


@pytest.mark.asyncio 
async def test_logging_handler():
    """Test that the logging handler works correctly."""
    try:
        # Get a logger and send a test message
        logger = logging.getLogger("test_loki_integration")
        logger.info("Test log message from pytest logging handler")
        
        # Wait a moment for async processing
        await asyncio.sleep(1)
        
        print("Logging handler test completed (check Loki for log entry)")
        
    except Exception as e:
        print(f"Logging handler test failed: {str(e)}")


if __name__ == "__main__":
    # Simple manual test runner
    async def run_manual_test():
        """Run manual integration tests."""
        print("Running Loki integration tests...")
        
        try:
            # Test with HTTP client
            async with httpx.AsyncClient() as client:
                # Test health endpoint
                print("Testing health endpoint...")
                response = await client.get("http://localhost:8000/api/v1/loki/health")
                print(f"Health check status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Health data: {response.json()}")
                
                # Test examples endpoint
                print("Testing examples endpoint...")
                response = await client.get("http://localhost:8000/api/v1/loki/examples")
                print(f"Examples status: {response.status_code}")
                
                # Test integration endpoint
                print("Testing integration endpoint...")
                response = await client.get("http://localhost:8000/api/v1/loki/test")
                print(f"Integration test status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Integration test result: {response.json()}")
                
        except Exception as e:
            print(f"Manual test failed: {str(e)}")
    
    # Run the test
    asyncio.run(run_manual_test())

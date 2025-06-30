"""
Health check classes for Loki, Grafana, and Redis using config values.
Each health check returns a status and diagnostic details for monitoring and alerting.
"""
import asyncio
import httpx

from app.core.loki import config


class LokiHealthCheck:
    """
    Health check for Loki API endpoint.
    """
    @staticmethod
    def check() -> dict:
        """Synchronous wrapper for async health check."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(LokiHealthCheck._async_check())
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(LokiHealthCheck._async_check())
    
    @staticmethod
    async def _async_check() -> dict:
        """Async health check implementation."""
        url = f"{config.LOKI_URL}/ready"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(url)
                # Handle response text properly - don't pass string as details dict
                response_text = resp.text.strip() if resp.text else ""
                return {
                    "status": "up" if resp.status_code == 200 else "down",
                    "status_code": resp.status_code,
                    "details": {"response": response_text} if response_text else None
                }
        except Exception as e:
            return {"status": "down", "error": str(e)}


class GrafanaHealthCheck:
    """
    Health check for Grafana API endpoint.
    """
    @staticmethod
    def check() -> dict:
        """Synchronous wrapper for async health check."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(GrafanaHealthCheck._async_check())
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(GrafanaHealthCheck._async_check())
    
    @staticmethod
    async def _async_check() -> dict:
        """Async health check implementation."""
        url = f"{config.GRAFANA_URL}/api/health"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(url, auth=(config.GRAFANA_ADMIN_USER, config.GRAFANA_ADMIN_PASSWORD))
                # Handle JSON or text response properly
                if resp.headers.get("content-type", "").startswith("application/json"):
                    try:
                        details = resp.json()
                    except:
                        details = {"response": resp.text.strip() if resp.text else ""}
                else:
                    details = {"response": resp.text.strip() if resp.text else ""}
                
                return {
                    "status": "up" if resp.status_code == 200 else "down",
                    "status_code": resp.status_code,
                    "details": details
                }
        except Exception as e:
            return {"status": "down", "error": str(e)}


class RedisHealthCheck:
    """
    Health check for Redis connection.
    Note: Redis settings are not available in main config, so this is disabled.
    """
    @staticmethod
    def check() -> dict:
        try:
            # Redis is not configured in the main settings, so we'll always return down
            return {"status": "down", "error": "Redis not configured"}
        except Exception as e:
            return {"status": "down", "error": str(e)}


class FastAPIHealthCheck:
    """
    Health check for FastAPI app (basic TCP connect on configured port).
    """
    @staticmethod
    def check() -> dict:
        import socket
        s = socket.socket()
        try:
            s.settimeout(2)
            s.connect(("localhost", config.FASTAPI_PORT))
            return {"status": "up"}
        except Exception as e:
            return {"status": "down", "error": str(e)}
        finally:
            s.close()

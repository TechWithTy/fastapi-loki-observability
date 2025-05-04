"""
Health check classes for Loki, Grafana, and Redis using config values.
Each health check returns a status and diagnostic details for monitoring and alerting.
"""
import httpx
import redis

from app.core.loki import config


class LokiHealthCheck:
    """
    Health check for Loki API endpoint.
    """
    @staticmethod
    def check() -> dict:
        url = f"{config.LOKI_URL}/ready"
        try:
            resp = httpx.get(url, timeout=3)
            return {
                "status": "up" if resp.status_code == 200 else "down",
                "status_code": resp.status_code,
                "details": resp.text
            }
        except Exception as e:
            return {"status": "down", "error": str(e)}

class GrafanaHealthCheck:
    """
    Health check for Grafana API endpoint.
    """
    @staticmethod
    def check() -> dict:
        url = f"{config.GRAFANA_URL}/api/health"
        try:
            resp = httpx.get(url, timeout=3, auth=(config.GRAFANA_ADMIN_USER, config.GRAFANA_ADMIN_PASSWORD))
            return {
                "status": "up" if resp.status_code == 200 else "down",
                "status_code": resp.status_code,
                "details": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            }
        except Exception as e:
            return {"status": "down", "error": str(e)}

class RedisHealthCheck:
    """
    Health check for Redis connection.
    """
    @staticmethod
    def check() -> dict:
        try:
            r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD, socket_connect_timeout=3)
            pong = r.ping()
            return {"status": "up" if pong else "down"}
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

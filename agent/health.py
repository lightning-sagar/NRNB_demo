from __future__ import annotations

import json
from urllib import error, request

from agent.config import DEFAULT_MCP_HEALTH_URL, FALLBACK_SKILL_PATH


def get_mcp_health() -> dict[str, str]:
    try:
        with request.urlopen(DEFAULT_MCP_HEALTH_URL, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "status": "ok",
            "mode": "mcp",
            "detail": payload.get("status", "ok"),
            "health_url": DEFAULT_MCP_HEALTH_URL,
        }
    except error.URLError as exc:
        return {
            "status": "degraded",
            "mode": "skill.md",
            "detail": f"MCP health check failed: {exc.reason}",
            "health_url": DEFAULT_MCP_HEALTH_URL,
            "fallback": FALLBACK_SKILL_PATH,
        }
    except Exception as exc:
        return {
            "status": "degraded",
            "mode": "skill.md",
            "detail": f"MCP health check failed: {exc}",
            "health_url": DEFAULT_MCP_HEALTH_URL,
            "fallback": FALLBACK_SKILL_PATH,
        }

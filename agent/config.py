from __future__ import annotations

import os


AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", "9000"))
CARVEME_POLL_SECONDS = float(os.getenv("CARVEME_POLL_SECONDS", "2"))
CARVEME_TIMEOUT_SECONDS = float(os.getenv("CARVEME_TIMEOUT_SECONDS", "900"))
DEFAULT_AGENT_URL = os.getenv("AGENT_URL", "http://localhost:9000")
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "data/output")
DEFAULT_MCP_HEALTH_URL = os.getenv("MCP_HEALTH_URL", "http://localhost:8000/health")
FALLBACK_SKILL_PATH = os.getenv("FALLBACK_SKILL_PATH", "SKILL.md")

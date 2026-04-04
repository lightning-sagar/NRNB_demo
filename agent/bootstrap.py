from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER_DIR = PROJECT_ROOT / "mcp-server"


def ensure_project_paths() -> None:
    for path in (MCP_SERVER_DIR, PROJECT_ROOT):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

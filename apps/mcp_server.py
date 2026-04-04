from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    server_script = Path(__file__).resolve().parent.parent / "mcp-server" / "server.py"
    runpy.run_path(str(server_script), run_name="__main__")


if __name__ == "__main__":
    main()

from __future__ import annotations

try:
    from apps.bootstrap import ensure_project_root
except ModuleNotFoundError:
    from bootstrap import ensure_project_root

ensure_project_root()

from pipeline.pipeline import main


if __name__ == "__main__":
    main()

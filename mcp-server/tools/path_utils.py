import re
from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent.parent


def _normalize_slashes(raw_path: str) -> str:
    return raw_path.replace("\\", "/")


def _rewrite_windows_absolute_to_project(raw_path: str) -> Path | None:
    """Map a Windows absolute path to a project-local path when possible.

    Example:
    C:\\Users\\...\\demo\\data\\input\\genome.fna -> /app/data/input/genome.fna
    """
    normalized = _normalize_slashes(raw_path)
    match = re.match(r"^[A-Za-z]:/(.+)$", normalized)
    if not match:
        return None

    parts = Path(match.group(1)).parts
    parts_lower = [part.lower() for part in parts]

    if "demo" in parts_lower:
        idx = parts_lower.index("demo")
        return PROJECT_ROOT.joinpath(*parts[idx + 1 :])

    if "data" in parts_lower:
        idx = parts_lower.index("data")
        return PROJECT_ROOT.joinpath(*parts[idx:])

    if "outputs" in parts_lower:
        idx = parts_lower.index("outputs")
        return PROJECT_ROOT.joinpath(*parts[idx:])

    return None


def resolve_input_file_path(path_arg: str) -> Path:
    """Resolve an input file path from local or remote MCP clients.

    Supports:
    - absolute/relative paths local to the server runtime
    - Windows absolute paths coming from host clients while server runs in Linux/Docker
    """
    candidate = Path(path_arg)
    if candidate.is_absolute() and candidate.exists():
        return candidate.resolve()

    rewritten = _rewrite_windows_absolute_to_project(path_arg)
    if rewritten is not None and rewritten.exists():
        return rewritten.resolve()

    project_relative = (PROJECT_ROOT / path_arg).resolve()
    if project_relative.exists():
        return project_relative

    raise FileNotFoundError(
        "Input file not found from MCP server runtime: "
        f"'{path_arg}'. Use a path relative to project root, for example 'data/input/genome.fna'."
    )


def resolve_output_dir_path(path_arg: str) -> Path:
    """Resolve output directory path and keep writes within server-visible filesystem."""
    candidate = Path(path_arg)
    if candidate.is_absolute():
        rewritten = _rewrite_windows_absolute_to_project(path_arg)
        if rewritten is not None:
            return rewritten.resolve()
        return candidate.resolve()

    return (PROJECT_ROOT / path_arg).resolve()

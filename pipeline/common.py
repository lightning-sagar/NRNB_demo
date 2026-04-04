from __future__ import annotations

import subprocess


def format_command(cmd: list[str]) -> str:
    return " ".join(cmd)


def run_command(cmd: list[str], step_name: str) -> subprocess.CompletedProcess[str]:
    print(f"[{step_name}] Running: {format_command(cmd)}")
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode == 0:
        return completed

    details: list[str] = [f"{step_name} failed with exit code {completed.returncode}."]
    if completed.stdout.strip():
        details.append(f"stdout:\n{completed.stdout.strip()}")
    if completed.stderr.strip():
        details.append(f"stderr:\n{completed.stderr.strip()}")
    raise RuntimeError("\n".join(details))

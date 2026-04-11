from datetime import datetime, timezone
from threading import Lock, Thread
from uuid import uuid4
from collections.abc import Callable

_JOBS: dict[str, dict[str, str]] = {}
_JOBS_LOCK = Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_job_state(job_id: str, updates: dict[str, str]) -> None:
    with _JOBS_LOCK:
        if job_id not in _JOBS:
            _JOBS[job_id] = {}
        _JOBS[job_id].update(updates)


def start_background_job(
    *,
    kind: str,
    target: Callable[..., None],
    args: tuple[object, ...],
    initial_state: dict[str, str],
) -> dict[str, str]:
    job_id = uuid4().hex
    set_job_state(
        job_id,
        {
            "kind": kind,
            "status": "running",
            "started_at": utc_now(),
            **initial_state,
        },
    )
    worker = Thread(
        target=target,
        args=(job_id, *args),
        daemon=True,
        name=f"{kind}-{job_id[:8]}",
    )
    worker.start()
    return {
        "job_id": job_id,
        "status": "running",
        "message": f"{kind} started in background. Call a status tool with job_id.",
    }


def get_job_state(job_id: str, expected_kind_prefix: str | None = None) -> dict[str, str]:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise RuntimeError(f"Unknown job_id: {job_id}")
    if expected_kind_prefix and not job.get("kind", "").startswith(expected_kind_prefix):
        raise RuntimeError(
            f"Job '{job_id}' is kind '{job.get('kind')}', not '{expected_kind_prefix}'"
        )
    return {"job_id": job_id, **job}

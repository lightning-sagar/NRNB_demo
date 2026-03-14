from datetime import datetime, timezone
from threading import Lock, Thread
from uuid import uuid4

from pipeline.pipeline import build_output_paths, run_carveme

from .path_utils import resolve_input_file_path, resolve_output_dir_path

_JOBS: dict[str, dict[str, str]] = {}
_JOBS_LOCK = Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_job_state(job_id: str, updates: dict[str, str]) -> None:
    with _JOBS_LOCK:
        if job_id not in _JOBS:
            _JOBS[job_id] = {}
        _JOBS[job_id].update(updates)


def _run_carveme_job(job_id: str, faa_file: str, output_dir: str) -> None:
    try:
        proteins_faa = resolve_input_file_path(faa_file)
        outputs = build_output_paths(resolve_output_dir_path(output_dir))
        model_xml = run_carveme(proteins_faa, outputs.model_xml)
        if not model_xml.exists():
            raise RuntimeError(
                "CarveMe did not produce model.xml. Ensure DIAMOND is installed in the runtime."
            )
        _set_job_state(
            job_id,
            {
                "status": "completed",
                "input_proteins": str(proteins_faa),
                "model_xml": str(model_xml),
                "output_dir": str(outputs.model_xml.parent),
                "finished_at": _utc_now(),
            },
        )
    except Exception as exc:
        _set_job_state(
            job_id,
            {
                "status": "failed",
                "error": str(exc),
                "finished_at": _utc_now(),
            },
        )

def run_carveme_tool(faa_file: str, output_dir: str = "data/output") -> dict[str, str]:
    job_id = uuid4().hex
    _set_job_state(
        job_id,
        {
            "status": "running",
            "input_proteins": faa_file,
            "requested_output_dir": output_dir,
            "started_at": _utc_now(),
        },
    )

    worker = Thread(
        target=_run_carveme_job,
        args=(job_id, faa_file, output_dir),
        daemon=True,
        name=f"carveme-{job_id[:8]}",
    )
    worker.start()

    return {
        "job_id": job_id,
        "status": "running",
        "message": "CarveMe started in background. Call get_carveme_status with job_id.",
    }


def get_carveme_status_tool(job_id: str) -> dict[str, str]:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if job is None:
        raise RuntimeError(f"Unknown CarveMe job_id: {job_id}")
    return {"job_id": job_id, **job}
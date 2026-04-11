from pipeline.pipeline import build_output_paths, run_memote

from .job_store import get_job_state, set_job_state, start_background_job, utc_now
from .path_utils import resolve_input_file_path, resolve_output_dir_path


def _run_memote_job(job_id: str, model_xml: str, output_dir: str) -> None:
    try:
        model_path = resolve_input_file_path(model_xml)
        outputs = build_output_paths(resolve_output_dir_path(output_dir))
        report_path = run_memote(model_path, outputs.memote_report_html)
        set_job_state(
            job_id,
            {
                "status": "completed",
                "input_model": str(model_path),
                "memote_report_html": str(report_path),
                "output_dir": str(outputs.memote_report_html.parent),
                "finished_at": utc_now(),
            },
        )
    except Exception as exc:
        set_job_state(
            job_id,
            {
                "status": "failed",
                "error": str(exc),
                "finished_at": utc_now(),
            },
        )


def run_memote_tool(model_xml: str, output_dir: str = "data/output") -> dict[str, str]:
    return start_background_job(
        kind="memote",
        target=_run_memote_job,
        args=(model_xml, output_dir),
        initial_state={
            "input_model": model_xml,
            "requested_output_dir": output_dir,
        },
    )


def get_memote_status_tool(job_id: str) -> dict[str, str]:
    return get_job_state(job_id, expected_kind_prefix="memote")

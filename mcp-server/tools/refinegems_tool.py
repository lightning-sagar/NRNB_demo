from pipeline.pipeline import (
    build_output_paths,
    refine_biomass,
    refine_charges,
    run_refinegems_polish,
    save_json_result,
)

from .job_store import get_job_state, set_job_state, start_background_job, utc_now
from .path_utils import resolve_input_file_path, resolve_output_dir_path


def _job_failed(job_id: str, exc: Exception) -> None:
    set_job_state(
        job_id,
        {
            "status": "failed",
            "error": str(exc),
            "finished_at": utc_now(),
        },
    )


def _run_polish_job(
    job_id: str,
    model_xml: str,
    output_dir: str,
    email: str,
    id_db: str,
    protein_fasta: str | None,
    lab_strain: bool,
) -> None:
    try:
        model_path = resolve_input_file_path(model_xml)
        protein_path = resolve_input_file_path(protein_fasta) if protein_fasta else None
        outputs = build_output_paths(resolve_output_dir_path(output_dir))
        polished_model = run_refinegems_polish(
            model_path,
            outputs.polished_model_xml,
            email=email,
            id_db=id_db,
            protein_fasta=protein_path,
            lab_strain=lab_strain,
        )
        set_job_state(
            job_id,
            {
                "status": "completed",
                "input_model": str(model_path),
                "polished_model_xml": str(polished_model),
                "output_dir": str(outputs.polished_model_xml.parent),
                "finished_at": utc_now(),
            },
        )
    except Exception as exc:
        _job_failed(job_id, exc)


def _run_biomass_job(job_id: str, model_xml: str, output_dir: str) -> None:
    try:
        model_path = resolve_input_file_path(model_xml)
        outputs = build_output_paths(resolve_output_dir_path(output_dir))
        refined_model = refine_biomass(model_path, outputs.biomass_refined_model_xml)
        set_job_state(
            job_id,
            {
                "status": "completed",
                "input_model": str(model_path),
                "biomass_refined_model_xml": str(refined_model),
                "output_dir": str(outputs.biomass_refined_model_xml.parent),
                "finished_at": utc_now(),
            },
        )
    except Exception as exc:
        _job_failed(job_id, exc)


def _run_charges_job(job_id: str, model_xml: str, output_dir: str) -> None:
    try:
        model_path = resolve_input_file_path(model_xml)
        outputs = build_output_paths(resolve_output_dir_path(output_dir))
        result = refine_charges(
            model_path,
            outputs.charge_refined_model_xml,
            outputs.charge_multiple_options_json,
        )
        save_json_result(result, outputs.charge_refined_model_xml.with_suffix(".summary.json"))
        set_job_state(
            job_id,
            {
                "status": "completed",
                "input_model": str(model_path),
                "charge_refined_model_xml": str(result["model_xml"]),
                "multiple_charge_options_json": str(result["multiple_charge_options_json"]),
                "num_multiple_charge_options": str(result["num_multiple_charge_options"]),
                "output_dir": str(outputs.charge_refined_model_xml.parent),
                "finished_at": utc_now(),
            },
        )
    except Exception as exc:
        _job_failed(job_id, exc)


def run_refinegems_polish_tool(
    model_xml: str,
    output_dir: str = "data/output",
    email: str = "anonymous@example.com",
    id_db: str = "BIGG",
    protein_fasta: str | None = None,
    lab_strain: bool = False,
) -> dict[str, str]:
    return start_background_job(
        kind="refinegems-polish",
        target=_run_polish_job,
        args=(model_xml, output_dir, email, id_db, protein_fasta, lab_strain),
        initial_state={
            "input_model": model_xml,
            "requested_output_dir": output_dir,
            "id_db": id_db,
            "lab_strain": str(lab_strain),
        },
    )


def refine_biomass_tool(model_xml: str, output_dir: str = "data/output") -> dict[str, str]:
    return start_background_job(
        kind="refinegems-biomass",
        target=_run_biomass_job,
        args=(model_xml, output_dir),
        initial_state={
            "input_model": model_xml,
            "requested_output_dir": output_dir,
        },
    )


def refine_charges_tool(model_xml: str, output_dir: str = "data/output") -> dict[str, str]:
    return start_background_job(
        kind="refinegems-charges",
        target=_run_charges_job,
        args=(model_xml, output_dir),
        initial_state={
            "input_model": model_xml,
            "requested_output_dir": output_dir,
        },
    )


def get_refinegems_status_tool(job_id: str) -> dict[str, str]:
    return get_job_state(job_id, expected_kind_prefix="refinegems")

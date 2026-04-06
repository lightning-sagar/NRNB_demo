import re

from pipeline.pipeline import (
    build_output_paths,
    inspect_model_statistics,
    query_reaction_details,
    run_fba,
    run_fva,
    save_fba_result,
    save_json_result,
    simulate_gene_knockout_effects,
)
from .path_utils import resolve_input_file_path, resolve_output_dir_path


def _safe_file_fragment(raw_value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_value).strip("_")
    return sanitized or "result"


def run_fba_tool(model_xml: str, output_dir: str = "data/output") -> dict[str, str | float]:
    model_path = resolve_input_file_path(model_xml)
    outputs = build_output_paths(resolve_output_dir_path(output_dir))
    growth_rate = run_fba(model_path)
    result_path = save_fba_result(growth_rate, outputs.fba_result_txt)
    return {
        "input_model": str(model_path),
        "growth_rate": growth_rate,
        "fba_result_txt": str(result_path),
        "output_dir": str(outputs.fba_result_txt.parent),
    }


def inspect_model_statistics_tool(
    model_xml: str,
    output_dir: str = "data/output",
) -> dict[str, object]:
    model_path = resolve_input_file_path(model_xml)
    output_path = resolve_output_dir_path(output_dir) / "model_statistics.json"
    stats = inspect_model_statistics(model_path)
    save_json_result(stats, output_path)
    return {
        "input_model": str(model_path),
        "statistics": stats,
        "model_statistics_json": str(output_path),
        "output_dir": str(output_path.parent),
    }


def query_reaction_details_tool(
    model_xml: str,
    reaction_id: str,
    output_dir: str = "data/output",
) -> dict[str, object]:
    model_path = resolve_input_file_path(model_xml)
    safe_reaction_id = _safe_file_fragment(reaction_id)
    output_path = resolve_output_dir_path(output_dir) / f"reaction_{safe_reaction_id}_details.json"
    details = query_reaction_details(model_path, reaction_id)
    save_json_result(details, output_path)
    return {
        "input_model": str(model_path),
        "reaction_id": reaction_id,
        "reaction_details": details,
        "reaction_details_json": str(output_path),
        "output_dir": str(output_path.parent),
    }


def run_fva_tool(
    model_xml: str,
    reaction_ids: list[str],
    output_dir: str = "data/output",
    fraction_of_optimum: float = 1.0,
) -> dict[str, object]:
    model_path = resolve_input_file_path(model_xml)
    output_path = resolve_output_dir_path(output_dir) / "fva_results.json"
    fva_results = run_fva(
        model_path,
        reaction_ids=reaction_ids,
        fraction_of_optimum=fraction_of_optimum,
    )
    payload = {
        "fraction_of_optimum": fraction_of_optimum,
        "results": fva_results,
    }
    save_json_result(payload, output_path)
    return {
        "input_model": str(model_path),
        "reaction_ids": reaction_ids,
        "fraction_of_optimum": fraction_of_optimum,
        "fva_results": fva_results,
        "fva_results_json": str(output_path),
        "output_dir": str(output_path.parent),
    }


def simulate_gene_knockout_effects_tool(
    model_xml: str,
    gene_ids: list[str],
    output_dir: str = "data/output",
) -> dict[str, object]:
    model_path = resolve_input_file_path(model_xml)
    output_path = resolve_output_dir_path(output_dir) / "gene_knockout_results.json"
    knockout_summary = simulate_gene_knockout_effects(model_path, gene_ids=gene_ids)
    save_json_result(knockout_summary, output_path)
    return {
        "input_model": str(model_path),
        "gene_ids": gene_ids,
        "baseline_growth": knockout_summary["baseline_growth"],
        "knockout_results": knockout_summary["knockout_results"],
        "gene_knockout_results_json": str(output_path),
        "output_dir": str(output_path.parent),
    }

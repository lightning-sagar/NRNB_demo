from __future__ import annotations

import json
from pathlib import Path

from .path_utils import resolve_input_file_path, resolve_output_dir_path


def prepare_refinegems_handoff_tool(
    model_xml: str,
    output_dir: str = "data/output",
    memote_report_html: str | None = None,
    fba_result_txt: str | None = None,
) -> dict[str, str]:
    model_path = resolve_input_file_path(model_xml)
    output_path = resolve_output_dir_path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    memote_path = resolve_input_file_path(memote_report_html) if memote_report_html else None
    fba_path = resolve_input_file_path(fba_result_txt) if fba_result_txt else None
    manifest_path = output_path / "refinegems_handoff.json"

    manifest = {
        "status": "prepared",
        "tool": "refineGEMs",
        "model_xml": str(model_path),
        "memote_report_html": str(memote_path) if memote_path else "",
        "fba_result_txt": str(fba_path) if fba_path else "",
        "recommended_next_steps": [
            "Review biomass formulation and exchange bounds.",
            "Inspect dead-end metabolites and blocked reactions.",
            "Curate GPR rules and compartment assignments.",
            "Run refineGEMs-specific curation once that runtime is available.",
        ],
        "note": (
            "This repo currently prepares a handoff artifact for refineGEMs workflows. "
            "It does not bundle refineGEMs execution yet."
        ),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "status": "prepared",
        "tool": "refineGEMs",
        "model_xml": str(model_path),
        "handoff_manifest": str(manifest_path),
        "output_dir": str(output_path),
    }

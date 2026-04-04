from __future__ import annotations

import re
import time
from pathlib import Path

from agent.bootstrap import ensure_project_paths
from agent.config import CARVEME_POLL_SECONDS, CARVEME_TIMEOUT_SECONDS
from agent.health import get_mcp_health
from agent.models import PromptResponse


ensure_project_paths()

from tools.carveme_tool import get_carveme_status_tool, run_carveme_tool
from tools.cobra_tool import run_fba_tool
from tools.memote_tool import run_memote_tool
from tools.path_utils import resolve_input_file_path, resolve_output_dir_path
from tools.prodigal_tool import run_prodigal_tool


SUPPORTED_EXTENSIONS = (".fna", ".faa", ".xml")
PATH_PATTERN = re.compile(
    r'([A-Za-z]:[\\/][^"\']+?\.(?:fna|faa|xml)|[\w./\\-]+\.(?:fna|faa|xml))',
    re.IGNORECASE,
)


def extract_path(prompt: str) -> str | None:
    match = PATH_PATTERN.search(prompt)
    if not match:
        return None
    return match.group(1).strip().strip("\"'")


def wait_for_carveme(job_id: str) -> dict[str, str]:
    deadline = time.time() + CARVEME_TIMEOUT_SECONDS
    last_status: dict[str, str] | None = None
    while time.time() < deadline:
        status = get_carveme_status_tool(job_id)
        last_status = status
        if status["status"] == "completed":
            return status
        if status["status"] == "failed":
            raise RuntimeError(status.get("error", "CarveMe job failed."))
        time.sleep(CARVEME_POLL_SECONDS)
    raise RuntimeError(
        "Timed out waiting for CarveMe to finish."
        + (f" Last known status: {last_status}" if last_status else "")
    )


def wants_memote(prompt: str, extension: str) -> bool:
    lowered = prompt.lower()
    return extension != ".xml" or "memote" in lowered or "report" in lowered or "score" in lowered


def wants_fba(prompt: str, extension: str) -> bool:
    lowered = prompt.lower()
    return extension != ".xml" or "fba" in lowered or "growth" in lowered or "flux" in lowered


def run_prompt_workflow(prompt: str, output_dir: str) -> PromptResponse:
    health = get_mcp_health()
    raw_path = extract_path(prompt)
    if raw_path is None:
        return PromptResponse(
            reply=(
                "I can route `.fna`, `.faa`, and `.xml` requests. "
                "Include a file path in your prompt, for example: "
                "`Run the pipeline for data/input/genome.fna`."
            ),
            mcp_status=health["status"],
            mode=health["mode"],
        )

    input_path = resolve_input_file_path(raw_path)
    resolved_output_dir = resolve_output_dir_path(output_dir)
    extension = input_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise RuntimeError(f"Unsupported file type: {input_path.suffix}")

    summary_lines: list[str] = []
    if health["status"] == "ok":
        summary_lines.append("MCP health check is OK.")
    else:
        summary_lines.append(
            f"MCP is unavailable, so I switched to the fallback guide in `{health['fallback']}`."
        )
    summary_lines.append(f"Prompt routed using `{input_path.name}`.")
    model_xml: str | None = None

    if extension == ".fna":
        prodigal_result = run_prodigal_tool(str(input_path), str(resolved_output_dir))
        summary_lines.append(f"Prodigal produced `{Path(prodigal_result['proteins_faa']).name}`.")
        carveme_job = run_carveme_tool(prodigal_result["proteins_faa"], str(resolved_output_dir))
        carveme_result = wait_for_carveme(carveme_job["job_id"])
        model_xml = carveme_result["model_xml"]
        summary_lines.append(f"CarveMe produced `{Path(model_xml).name}`.")
    elif extension == ".faa":
        carveme_job = run_carveme_tool(str(input_path), str(resolved_output_dir))
        carveme_result = wait_for_carveme(carveme_job["job_id"])
        model_xml = carveme_result["model_xml"]
        summary_lines.append(f"CarveMe produced `{Path(model_xml).name}`.")
    else:
        model_xml = str(input_path)
        summary_lines.append("Using the supplied SBML model directly.")

    if model_xml is None:
        raise RuntimeError("Workflow did not resolve a model XML file.")

    if wants_memote(prompt, extension):
        memote_result = run_memote_tool(model_xml, str(resolved_output_dir))
        summary_lines.append(
            f"MEMOTE report saved to `{Path(memote_result['memote_report_html']).name}`."
        )

    if wants_fba(prompt, extension):
        fba_result = run_fba_tool(model_xml, str(resolved_output_dir))
        summary_lines.append(
            "FBA predicted growth rate "
            f"`{fba_result['growth_rate']}` and saved `{Path(fba_result['fba_result_txt']).name}`."
        )

    summary_lines.append(f"Outputs are in `{resolved_output_dir}`.")
    return PromptResponse(
        reply=" ".join(summary_lines),
        routed_file=str(input_path),
        output_dir=str(resolved_output_dir),
        mcp_status=health["status"],
        mode=health["mode"],
    )

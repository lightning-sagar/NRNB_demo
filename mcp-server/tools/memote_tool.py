"""FastMCP wrapper for MEMOTE."""

from pathlib import Path

from pipeline.pipeline import build_output_paths, run_memote


def run_memote_tool(model_xml: str, output_dir: str = "outputs") -> dict[str, str]:
    model_path = Path(model_xml).resolve()
    outputs = build_output_paths(Path(output_dir).resolve())
    report_path = run_memote(model_path, outputs.memote_report_html)
    return {
        "input_model": str(model_path),
        "memote_report_html": str(report_path),
        "output_dir": str(outputs.memote_report_html.parent),
    }
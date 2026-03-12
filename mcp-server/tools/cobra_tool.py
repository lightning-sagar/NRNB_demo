"""FastMCP wrapper for COBRApy FBA."""

from pathlib import Path

from pipeline.pipeline import build_output_paths, run_fba, save_fba_result


def run_fba_tool(model_xml: str, output_dir: str = "outputs") -> dict[str, str | float]:
    model_path = Path(model_xml).resolve()
    outputs = build_output_paths(Path(output_dir).resolve())
    growth_rate = run_fba(model_path)
    result_path = save_fba_result(growth_rate, outputs.fba_result_txt)
    return {
        "input_model": str(model_path),
        "growth_rate": growth_rate,
        "fba_result_txt": str(result_path),
        "output_dir": str(outputs.fba_result_txt.parent),
    }
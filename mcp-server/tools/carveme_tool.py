"""FastMCP wrapper for CarveMe."""

from pathlib import Path

from pipeline.pipeline import build_output_paths, run_carveme


def run_carveme_tool(faa_file: str, output_dir: str = "outputs") -> dict[str, str]:
    proteins_faa = Path(faa_file).resolve()
    outputs = build_output_paths(Path(output_dir).resolve())
    model_xml = run_carveme(proteins_faa, outputs.model_xml)
    return {
        "input_proteins": str(proteins_faa),
        "model_xml": str(model_xml),
        "output_dir": str(outputs.model_xml.parent),
    }
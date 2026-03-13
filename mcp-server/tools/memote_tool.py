from pipeline.pipeline import build_output_paths, run_memote
from .path_utils import resolve_input_file_path, resolve_output_dir_path

def run_memote_tool(model_xml: str, output_dir: str = "data/output") -> dict[str, str]:
    model_path = resolve_input_file_path(model_xml)
    outputs = build_output_paths(resolve_output_dir_path(output_dir))
    report_path = run_memote(model_path, outputs.memote_report_html)
    return {
        "input_model": str(model_path),
        "memote_report_html": str(report_path),
        "output_dir": str(outputs.memote_report_html.parent),
    }
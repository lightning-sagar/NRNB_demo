from pipeline.pipeline import build_output_paths, run_fba, save_fba_result
from .path_utils import resolve_input_file_path, resolve_output_dir_path

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
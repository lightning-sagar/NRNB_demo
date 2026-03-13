from pipeline.pipeline import build_output_paths, run_carveme
from .path_utils import resolve_input_file_path, resolve_output_dir_path

def run_carveme_tool(faa_file: str, output_dir: str = "data/output") -> dict[str, str]:
    proteins_faa = resolve_input_file_path(faa_file)
    outputs = build_output_paths(resolve_output_dir_path(output_dir))
    model_xml = run_carveme(proteins_faa, outputs.model_xml)
    if not model_xml.exists():
        raise RuntimeError(
            "CarveMe did not produce model.xml. Ensure DIAMOND is installed in the runtime "
            "and re-run with faa_file='outputs/proteins.faa'."
        )
    return {
        "input_proteins": str(proteins_faa),
        "model_xml": str(model_xml),
        "output_dir": str(outputs.model_xml.parent),
    }
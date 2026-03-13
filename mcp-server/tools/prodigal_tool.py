from pipeline.pipeline import build_output_paths, run_prodigal
from .path_utils import resolve_input_file_path, resolve_output_dir_path

def run_prodigal_tool(fna_file: str, output_dir: str = "data/output") -> dict[str, str]:
    genome_fna = resolve_input_file_path(fna_file)
    outputs = build_output_paths(resolve_output_dir_path(output_dir))
    proteins_faa = run_prodigal(genome_fna, outputs.proteins_faa)
    return {
        "input_genome": str(genome_fna),
        "proteins_faa": str(proteins_faa),
        "output_dir": str(outputs.proteins_faa.parent),
    }
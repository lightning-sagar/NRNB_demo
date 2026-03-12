"""FastMCP wrapper for Prodigal."""

from pathlib import Path

from pipeline.pipeline import build_output_paths, run_prodigal


def run_prodigal_tool(fna_file: str, output_dir: str = "outputs") -> dict[str, str]:
    genome_fna = Path(fna_file).resolve()
    outputs = build_output_paths(Path(output_dir).resolve())
    proteins_faa = run_prodigal(genome_fna, outputs.proteins_faa)
    return {
        "input_genome": str(genome_fna),
        "proteins_faa": str(proteins_faa),
        "output_dir": str(outputs.proteins_faa.parent),
    }
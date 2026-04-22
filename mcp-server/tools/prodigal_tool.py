from pipeline.pipeline import build_output_paths, prepare_protein_fasta_for_refinegems, run_prodigal
from .path_utils import resolve_input_file_path, resolve_output_dir_path


def run_prodigal_tool(
    fna_file: str,
    output_dir: str = "data/output",
    annotation_tsv: str | None = None,
    default_organism: str = "Bacteria sp.",
) -> dict[str, str]:
    genome_fna = resolve_input_file_path(fna_file)
    outputs = build_output_paths(resolve_output_dir_path(output_dir))
    annotation_path = resolve_input_file_path(annotation_tsv) if annotation_tsv else None
    proteins_faa = run_prodigal(genome_fna, outputs.proteins_faa)
    prep_summary = prepare_protein_fasta_for_refinegems(
        proteins_faa,
        outputs.proteins_refinegems_faa,
        annotation_tsv=annotation_path,
        default_organism=default_organism,
    )
    return {
        "input_genome": str(genome_fna),
        "proteins_faa": str(proteins_faa),
        "proteins_refinegems_faa": str(outputs.proteins_refinegems_faa),
        "annotation_tsv": str(annotation_path) if annotation_path else "",
        "fasta_preparation_status": str(prep_summary["status"]),
        "headers_processed": str(prep_summary["input_headers"]),
        "annotation_hits": str(prep_summary["annotation_hits"]),
        "output_dir": str(outputs.proteins_faa.parent),
    }
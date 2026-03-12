import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cobra   


DEFAULT_OUTPUT_DIR = Path("data/output")


@dataclass
class PipelineOutputs:
    proteins_faa: Path
    model_xml: Path
    memote_report_html: Path
    fba_result_txt: Path


def run_command(cmd: list[str], step_name: str):
    print(f"[{step_name}] Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"{step_name} failed with exit code {exc.returncode}") from exc


def ensure_output_dir(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_output_paths(output_dir: Path) -> PipelineOutputs:
    output_dir = ensure_output_dir(output_dir)
    return PipelineOutputs(
        proteins_faa=output_dir / "proteins.faa",
        model_xml=output_dir / "model.xml",
        memote_report_html=output_dir / "memote_report.html",
        fba_result_txt=output_dir / "fba_result.txt",
    )


def run_prodigal(genome_fna: Path, proteins_faa: Path):
    cmd = ["prodigal", "-i", str(genome_fna), "-a", str(proteins_faa), "-p", "single", "-q"]
    run_command(cmd, "Prodigal")
    return proteins_faa


def run_carveme(proteins_faa: Path, model_xml: Path):
    cmd = ["carve", str(proteins_faa), "-o", str(model_xml)]
    run_command(cmd, "CarveMe")
    return model_xml


def run_memote(model_xml: Path, memote_report_html: Path):
    cmd = ["memote", "run", str(model_xml), "--filename", str(memote_report_html)]
    run_command(cmd, "MEMOTE")
    return memote_report_html


def run_fba(model_xml: Path) -> float:
    print("[COBRApy] Loading model and running FBA")
    model = cobra.io.read_sbml_model(str(model_xml))
    solution = model.optimize()
    print(f"[COBRApy] FBA solution: {solution}")
    if solution.status != "optimal":
        raise RuntimeError(f"FBA failed: solution status is '{solution.status}'")
    return float(solution.objective_value)


def save_fba_result(growth_rate: float, output_file: Path):
    output_file.write_text(
        f"Predicted growth rate (objective value): {growth_rate:.6f}\n",
        encoding="utf-8",
    )
    return output_file


def run_pipeline(
    genome: Path | None = None,
    protein: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
):
    genome_path = genome.resolve() if genome else None
    protein_path = protein.resolve() if protein else None
    outputs = build_output_paths(output_dir.resolve())

    if not genome_path and not protein_path:
        raise FileNotFoundError("Provide either a genome FASTA file or a protein FASTA file")
    if genome_path and not genome_path.exists():
        raise FileNotFoundError(f"Genome FASTA not found")
    if protein_path and not protein_path.exists():
        raise FileNotFoundError(f"Protein FASTA not found")

    proteins_faa = protein_path if protein_path else outputs.proteins_faa
    if protein_path is None:
        run_prodigal(genome_path, proteins_faa)

    run_carveme(proteins_faa, outputs.model_xml)
    run_memote(outputs.model_xml, outputs.memote_report_html)
    
    growth_rate = run_fba(outputs.model_xml)
    
    print(f"Predicted growth rate: {growth_rate:.6f}")
    save_fba_result(growth_rate, outputs.fba_result_txt)
    
    print(f"Saved FBA result to: {outputs.fba_result_txt}")
    print("Pipeline completed successfully.")
    return outputs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prototype genome-scale metabolic model reconstruction pipeline"
    )
    parser.add_argument("--genome", type=Path, help="Genome FASTA input")
    parser.add_argument("--protein", type=Path, help="Protein FASTA input")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated pipeline outputs",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_pipeline(genome=args.genome, protein=args.protein, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
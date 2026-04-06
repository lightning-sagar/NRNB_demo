import argparse
import json
import subprocess
from dataclasses import dataclass
from math import isnan
from pathlib import Path
import cobra   
from cobra.flux_analysis import flux_variability_analysis, single_gene_deletion

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


def load_cobra_model(model_xml: Path) -> cobra.Model:
    print(f"[COBRApy] Loading model from {model_xml}")
    return cobra.io.read_sbml_model(str(model_xml))


def optimize_model(model: cobra.Model) -> float:
    solution = model.optimize()
    print(f"[COBRApy] FBA solution: {solution}")
    if solution.status != "optimal":
        raise RuntimeError(f"FBA failed: solution status is '{solution.status}'")
    return float(solution.objective_value)


def run_fba(model_xml: Path) -> float:
    print("[COBRApy] Running FBA")
    model = load_cobra_model(model_xml)
    return optimize_model(model)


def inspect_model_statistics(model_xml: Path) -> dict[str, object]:
    model = load_cobra_model(model_xml)
    return {
        "model_id": model.id,
        "model_name": model.name,
        "num_reactions": len(model.reactions),
        "num_metabolites": len(model.metabolites),
        "num_genes": len(model.genes),
        "num_compartments": len(model.compartments),
        "compartments": dict(sorted(model.compartments.items())),
        "num_boundary_reactions": len(model.boundary),
        "num_exchange_reactions": len(model.exchanges),
        "num_demand_reactions": len(model.demands),
        "num_sink_reactions": len(model.sinks),
        "objective_direction": model.objective.direction,
        "objective_expression": str(model.objective.expression),
    }


def query_reaction_details(model_xml: Path, reaction_id: str) -> dict[str, object]:
    model = load_cobra_model(model_xml)
    try:
        reaction = model.reactions.get_by_id(reaction_id)
    except KeyError as exc:
        raise ValueError(f"Reaction '{reaction_id}' was not found in the model") from exc

    metabolites = []
    for metabolite, coefficient in reaction.metabolites.items():
        metabolites.append(
            {
                "id": metabolite.id,
                "name": metabolite.name,
                "compartment": metabolite.compartment,
                "coefficient": float(coefficient),
            }
        )

    return {
        "reaction_id": reaction.id,
        "reaction_name": reaction.name,
        "equation": reaction.build_reaction_string(use_metabolite_names=False),
        "lower_bound": float(reaction.lower_bound),
        "upper_bound": float(reaction.upper_bound),
        "subsystem": reaction.subsystem,
        "gene_reaction_rule": reaction.gene_reaction_rule,
        "genes": sorted(gene.id for gene in reaction.genes),
        "metabolites": metabolites,
    }


def run_fva(
    model_xml: Path,
    reaction_ids: list[str],
    fraction_of_optimum: float = 1.0,
) -> list[dict[str, object]]:
    if not reaction_ids:
        raise ValueError("Provide at least one reaction ID for FVA")

    model = load_cobra_model(model_xml)
    missing_reactions = []
    for reaction_id in reaction_ids:
        try:
            model.reactions.get_by_id(reaction_id)
        except KeyError:
            missing_reactions.append(reaction_id)
    if missing_reactions:
        raise ValueError(f"Reactions not found in the model: {', '.join(missing_reactions)}")

    fva_frame = flux_variability_analysis(
        model,
        reaction_list=reaction_ids,
        fraction_of_optimum=fraction_of_optimum,
        processes=1,
    )

    results: list[dict[str, object]] = []
    for reaction_id, row in fva_frame.iterrows():
        results.append(
            {
                "reaction_id": reaction_id,
                "minimum_flux": float(row["minimum"]),
                "maximum_flux": float(row["maximum"]),
            }
        )
    return results


def simulate_gene_knockout_effects(
    model_xml: Path,
    gene_ids: list[str],
) -> dict[str, object]:
    if not gene_ids:
        raise ValueError("Provide at least one gene ID for knockout simulation")

    model = load_cobra_model(model_xml)
    missing_genes = []
    for gene_id in gene_ids:
        try:
            model.genes.get_by_id(gene_id)
        except KeyError:
            missing_genes.append(gene_id)
    if missing_genes:
        raise ValueError(f"Genes not found in the model: {', '.join(missing_genes)}")

    baseline_growth = optimize_model(model)
    knockout_frame = single_gene_deletion(model, gene_list=gene_ids, processes=1)

    results: list[dict[str, object]] = []
    for _, row in knockout_frame.iterrows():
        knockout_ids = sorted(row["ids"]) if row["ids"] else []
        growth = row["growth"]
        growth_value = None if growth is None or isnan(growth) else float(growth)
        relative_growth = None
        if growth_value is not None and baseline_growth != 0:
            relative_growth = growth_value / baseline_growth

        results.append(
            {
                "gene_ids": knockout_ids,
                "status": row["status"],
                "growth": growth_value,
                "relative_growth": relative_growth,
            }
        )

    return {
        "baseline_growth": baseline_growth,
        "knockout_results": results,
    }


def save_fba_result(growth_rate: float, output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        f"Predicted growth rate (objective value): {growth_rate:.6f}\n",
        encoding="utf-8",
    )
    return output_file


def save_json_result(data: dict[str, object] | list[dict[str, object]], output_file: Path):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
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

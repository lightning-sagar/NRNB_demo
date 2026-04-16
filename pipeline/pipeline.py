import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from math import isnan
from pathlib import Path
import cobra   
from cobra.flux_analysis import flux_variability_analysis, single_gene_deletion
import libsbml

DEFAULT_OUTPUT_DIR = Path("data/output")


def _ensure_refinegems_runtime_env() -> None:
    cache_root = Path(
        os.getenv("REFINEGEMS_CACHE_DIR", "data/output/.refinegems-cache")
    ).resolve()
    os.environ.setdefault("PYSTOW_HOME", str(cache_root / "pystow"))
    os.environ.setdefault("PYSTOW_CONFIG_HOME", str(cache_root / "pystow-config"))
    os.environ.setdefault("XDG_CONFIG_HOME", str(cache_root / "xdg-config"))


_ensure_refinegems_runtime_env()

_REFINEGEMS_IMPORT_ERROR: Exception | None = None
try:
    from refinegems.biomass import check_normalise_biomass
    from refinegems.charges import correct_charges_modelseed
    from refinegems.polish import polish as refinegems_polish
except Exception as exc:
    _REFINEGEMS_IMPORT_ERROR = exc


def _require_refinegems() -> None:
    if _REFINEGEMS_IMPORT_ERROR is None:
        return
    raise RuntimeError(
        "refineGEMs dependencies are not installed in this runtime. "
        "Install a refine-specific environment to use polish/biomass/charges tools."
    ) from _REFINEGEMS_IMPORT_ERROR


@dataclass
class PipelineOutputs:
    proteins_faa: Path
    model_xml: Path
    polished_model_xml: Path
    biomass_refined_model_xml: Path
    charge_refined_model_xml: Path
    charge_multiple_options_json: Path
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
        polished_model_xml=output_dir / "model_refinegems_polished.xml",
        biomass_refined_model_xml=output_dir / "model_refinegems_biomass.xml",
        charge_refined_model_xml=output_dir / "model_refinegems_charges.xml",
        charge_multiple_options_json=output_dir / "refinegems_charge_options.json",
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
    cmd = [
        "memote",
        "run",
        str(model_xml),
        "--filename",
        str(memote_report_html),
        "--ignore-git",
    ]
    run_command(cmd, "MEMOTE")
    return memote_report_html


def load_cobra_model(model_xml: Path) -> cobra.Model:
    print(f"[COBRApy] Loading model from {model_xml}")
    return cobra.io.read_sbml_model(str(model_xml))


def _load_libsbml_document(model_xml: Path) -> libsbml.SBMLDocument:
    reader = libsbml.SBMLReader()
    document = reader.readSBMLFromFile(str(model_xml))
    if document.getModel() is None:
        errors = [
            document.getError(index).getMessage()
            for index in range(document.getNumErrors())
        ]
        detail = "; ".join(errors[:3]) if errors else "no libSBML error details available"
        raise RuntimeError(f"Could not load SBML model '{model_xml}': {detail}")
    return document


def _write_libsbml_model(model: libsbml.Model, output_xml: Path) -> Path:
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    status = libsbml.writeSBMLToFile(model.getSBMLDocument(), str(output_xml))
    if status != 1:
        raise RuntimeError(f"libSBML failed to write model to '{output_xml}'")
    return output_xml


def run_refinegems_polish(
    model_xml: Path,
    output_xml: Path,
    *,
    email: str = "anonymous@example.com",
    id_db: str = "BIGG",
    protein_fasta: Path | None = None,
    lab_strain: bool = False,
    report_prefix: Path | None = None,
) -> Path:
    _require_refinegems()
    print("[refineGEMs] Polishing SBML model")
    model_xml = model_xml.resolve()
    output_xml = output_xml.resolve()
    document = _load_libsbml_document(model_xml)
    model = document.getModel()
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    report_base = report_prefix or (output_xml.parent / "refinegems_polish_")

    refined_model = refinegems_polish(
        model,
        email=email,
        id_db=id_db,
        protein_fasta=str(protein_fasta or ""),
        lab_strain=lab_strain,
        path=str(report_base),
    )

    if refined_model is None:
        raise RuntimeError("refineGEMs polish did not return a model")
    return _write_libsbml_model(refined_model, output_xml)


def refine_biomass(model_xml: Path, output_xml: Path) -> Path:
    _require_refinegems()
    print("[refineGEMs] Normalising biomass reactions")
    model_xml = model_xml.resolve()
    output_xml = output_xml.resolve()
    output_xml.parent.mkdir(parents=True, exist_ok=True)
    model = load_cobra_model(model_xml)
    current_dir = Path.cwd()
    try:
        os.chdir(output_xml.parent)
        refined_model = check_normalise_biomass(model)
    finally:
        os.chdir(current_dir)
    if refined_model is None:
        raise RuntimeError("refineGEMs did not find a biomass reaction to normalise")

    if isinstance(refined_model, cobra.Model):
        cobra.io.write_sbml_model(refined_model, str(output_xml))
    elif isinstance(refined_model, libsbml.Model):
        _write_libsbml_model(refined_model, output_xml)
    else:
        raise RuntimeError(
            "refineGEMs biomass returned an unsupported model type: "
            f"{type(refined_model).__name__}"
        )
    return output_xml


def refine_charges(
    model_xml: Path,
    output_xml: Path,
    multiple_charge_options_json: Path | None = None,
) -> dict[str, object]:
    _require_refinegems()
    print("[refineGEMs] Correcting missing metabolite charges")
    model_xml = model_xml.resolve()
    output_xml = output_xml.resolve()
    if multiple_charge_options_json is not None:
        multiple_charge_options_json = multiple_charge_options_json.resolve()
    document = _load_libsbml_document(model_xml)
    model = document.getModel()
    refined_model, multiple_charge_options = correct_charges_modelseed(model)
    if refined_model is None:
        raise RuntimeError("refineGEMs charge correction did not return a model")

    model_path = _write_libsbml_model(refined_model, output_xml)
    options_path = None
    if multiple_charge_options_json is not None:
        serializable_options = {
            str(key): [int(value) for value in list(values)]
            for key, values in multiple_charge_options.items()
        }
        save_json_result(serializable_options, multiple_charge_options_json)
        options_path = str(multiple_charge_options_json)

    return {
        "model_xml": str(model_path),
        "multiple_charge_options_json": options_path,
        "num_multiple_charge_options": len(multiple_charge_options),
    }


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
    refinegems_polish: bool = False,
    refinegems_biomass: bool = False,
    refinegems_charges: bool = False,
    refinegems_email: str = "anonymous@example.com",
    refinegems_id_db: str = "BIGG",
    refinegems_lab_strain: bool = False,
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
    analysis_model_xml = outputs.model_xml
    if refinegems_polish:
        run_refinegems_polish(
            analysis_model_xml,
            outputs.polished_model_xml,
            email=refinegems_email,
            id_db=refinegems_id_db,
            protein_fasta=proteins_faa,
            lab_strain=refinegems_lab_strain,
        )
        analysis_model_xml = outputs.polished_model_xml
    if refinegems_biomass:
        refine_biomass(analysis_model_xml, outputs.biomass_refined_model_xml)
        analysis_model_xml = outputs.biomass_refined_model_xml
    if refinegems_charges:
        refine_charges(
            analysis_model_xml,
            outputs.charge_refined_model_xml,
            outputs.charge_multiple_options_json,
        )
        analysis_model_xml = outputs.charge_refined_model_xml

    run_memote(analysis_model_xml, outputs.memote_report_html)
    
    growth_rate = run_fba(analysis_model_xml)
    
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
    parser.add_argument("--refinegems-polish", action="store_true", help="Polish the CarveMe SBML model with refineGEMs before analysis")
    parser.add_argument("--refinegems-biomass", action="store_true", help="Normalise biomass reaction coefficients with refineGEMs before analysis")
    parser.add_argument("--refinegems-charges", action="store_true", help="Fill missing metabolite charges with refineGEMs before analysis")
    parser.add_argument("--refinegems-email", default="anonymous@example.com", help="Email used by refineGEMs for Entrez-backed polishing")
    parser.add_argument("--refinegems-id-db", default="BIGG", help="Primary ID database used by refineGEMs polishing, e.g. BIGG or VMH")
    parser.add_argument("--refinegems-lab-strain", action="store_true", help="Tell refineGEMs polishing to keep lab-strain locus tags from the protein FASTA")
    return parser.parse_args()


def main():
    args = parse_args()
    run_pipeline(
        genome=args.genome,
        protein=args.protein,
        output_dir=args.output_dir,
        refinegems_polish=args.refinegems_polish,
        refinegems_biomass=args.refinegems_biomass,
        refinegems_charges=args.refinegems_charges,
        refinegems_email=args.refinegems_email,
        refinegems_id_db=args.refinegems_id_db,
        refinegems_lab_strain=args.refinegems_lab_strain,
    )


if __name__ == "__main__":
    main()

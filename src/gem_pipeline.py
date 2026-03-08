""" for the prototype, the goal is to get work with cobra, memote, carveme, prodigal

Workflow:
1. Prodigal: genome.fna -> proteins.faa
2. CarveMe reconstruction: proteins.faa -> model.xml (SBML)
3. MEMOTE report generation: model.xml -> memote_report.html
4. COBRApy FBA simulation: model.xml -> growth rate
5. Save FBA result to fba_result.txt
"""

import argparse
import subprocess
from pathlib import Path

import cobra  # type: ignore


def run_command(cmd, step_name):
    print(f"[{step_name}] Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"{step_name} failed with exit code {exc.returncode}") from exc
    return

def run_prodigal(genome_fna, proteins_faa):
    # prodigal -i input.fna -a output.faa -p single -q
    cmd = ["prodigal","-i", str(genome_fna),"-a",str(proteins_faa),"-p","single", "-q"]
    run_command(cmd, "Prodigal")
    return


def run_carveme(proteins_faa, model_xml):
    cmd = ["carve", str(proteins_faa), "-o", str(model_xml)]
    run_command(cmd, "CarveMe")
    return

def run_memote(model_xml, memote_report_html):
    cmd = ["memote", "run", str(model_xml), "--filename", str(memote_report_html)]
    run_command(cmd, "MEMOTE")
    return

def run_fba(model_xml):
    print("[COBRApy] Loading model and running FBA")
    model = cobra.io.read_sbml_model(str(model_xml))
    solution = model.optimize()
    print(f"[COBRApy] FBA solution: {solution}")
    if solution.status != "optimal":
        raise RuntimeError(f"FBA failed: solution status is '{solution.status}'")
    return float(solution.objective_value)

def save_fba_result(growth_rate, output_file):
    output_file.write_text(
        f"Predicted growth rate (objective value): {growth_rate:.6f}\n",
        encoding="utf-8",
    )
    return


def parse_args():
    parser = argparse.ArgumentParser(
        description="Minimal prototype for genome -> GEM reconstruction -> FBA"
    )
    parser.add_argument(
        "--genome",
        type=Path,
        default=Path("data/genome.fna"),
    )
    parser.add_argument(
        "--protein",
        type=Path,
        default=Path("data/protein.faa"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    genome_fna = args.genome.resolve()
    proteins_faa = args.protein.resolve()
    output_dir = args.output_dir.resolve()
    if not (genome_fna.exists() or proteins_faa.exists()):
        raise FileNotFoundError(f"Input file not found")

    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_xml = output_dir/"model.xml"
    memote_report_html = output_dir / "memote_report.json"
    fba_result_txt = output_dir / "fba_result.txt"
    
    if not proteins_faa.exists():
        proteins_faa = output_dir/"proteins.faa"
        run_prodigal(genome_fna, proteins_faa)
    
    run_carveme(proteins_faa, model_xml)
    run_memote(model_xml, memote_report_html)

    growth_rate = run_fba(model_xml)
    print(f"Predicted growth rate: {growth_rate:.6f}")

    save_fba_result(growth_rate, fba_result_txt)
    print(f"Saved FBA result to: {fba_result_txt}")
    print("Pipeline completed successfully.")
    return


if __name__ == "__main__":
    main()

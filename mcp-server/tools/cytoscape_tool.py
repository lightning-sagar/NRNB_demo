from __future__ import annotations

import csv

import cobra

from .path_utils import resolve_input_file_path, resolve_output_dir_path


def prepare_cytoscape_export_tool(
    model_xml: str,
    output_dir: str = "data/output",
) -> dict[str, str | int]:
    model_path = resolve_input_file_path(model_xml)
    output_path = resolve_output_dir_path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model = cobra.io.read_sbml_model(str(model_path))
    nodes_path = output_path / "cytoscape_nodes.tsv"
    edges_path = output_path / "cytoscape_edges.tsv"

    node_ids: set[str] = set()
    edge_count = 0

    with nodes_path.open("w", encoding="utf-8", newline="") as nodes_file:
        nodes_writer = csv.writer(nodes_file, delimiter="\t")
        nodes_writer.writerow(["id", "label", "type"])

        for metabolite in model.metabolites:
            nodes_writer.writerow([metabolite.id, metabolite.name or metabolite.id, "metabolite"])
            node_ids.add(metabolite.id)

        for reaction in model.reactions:
            nodes_writer.writerow([reaction.id, reaction.name or reaction.id, "reaction"])
            node_ids.add(reaction.id)

    with edges_path.open("w", encoding="utf-8", newline="") as edges_file:
        edges_writer = csv.writer(edges_file, delimiter="\t")
        edges_writer.writerow(["source", "target", "interaction", "stoichiometry"])

        for reaction in model.reactions:
            for metabolite, coefficient in reaction.metabolites.items():
                interaction = "consumes" if coefficient < 0 else "produces"
                edges_writer.writerow(
                    [reaction.id, metabolite.id, interaction, str(abs(coefficient))]
                )
                edge_count += 1

    return {
        "status": "prepared",
        "tool": "Cytoscape",
        "model_xml": str(model_path),
        "nodes_tsv": str(nodes_path),
        "edges_tsv": str(edges_path),
        "node_count": len(node_ids),
        "edge_count": edge_count,
        "output_dir": str(output_path),
    }

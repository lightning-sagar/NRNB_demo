# GEM Tools Skills

This repository is designed to work with OpenCode using both MCP and skills-style documentation.

## Intended OpenCode Setup

1. Start the MCP server from this repo.
2. Point OpenCode at [opencode.json](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\opencode.json).
3. Let the OpenCode agent use MCP tools when available.
4. If MCP is unavailable, fall back to the guidance in this `SKILLS.md`.

## Tool Coverage

### CarveMe

Purpose:
Reconstruct a draft metabolic model from protein FASTA input.

Typical inputs:
- `data/input/protein.faa`
- `data/output/proteins.faa`

Typical output:
- `data/output/model.xml`

MCP route:
- `run_carveme(faa_file, output_dir)`

Fallback:
- Use the local pipeline or direct CarveMe CLI if MCP is unavailable.

### COBRApy

Purpose:
Load SBML and run flux balance analysis.

Typical input:
- `data/output/model.xml`

Typical output:
- `data/output/fba_result.txt`

MCP route:
- `run_fba(model_xml, output_dir)`

Fallback:
- Use the Python pipeline locally.

### MEMOTE

Purpose:
Assess SBML model quality and generate a report.

Typical input:
- `data/output/model.xml`

Typical output:
- `data/output/memote_report.html`

MCP route:
- `run_memote(model_xml, output_dir)`

Fallback:
- Run MEMOTE from the local environment if installed.

### refineGEMs

Purpose:
Refine or curate draft GEMs after reconstruction.

Current repo status:
- Exposed as a handoff-preparation MCP tool.
- Produces a `refinegems_handoff.json` manifest for downstream curation.

Recommended OpenCode behavior:
- Use generated `model.xml` as the handoff artifact.
- Use `prepare_refinegems_handoff` after MEMOTE and FBA.
- If refineGEMs runtime execution is added later, extend the current handoff tool into a full execution workflow.

### Cytoscape

Purpose:
Visualization, network exploration, and presentation of metabolic models.

Current repo status:
- Exposed as an MCP export-preparation tool.
- Produces Cytoscape-ready node and edge TSV files.

Recommended OpenCode behavior:
- Treat Cytoscape as a downstream visualization step after `model.xml` generation.
- Use `prepare_cytoscape_export` to generate import-ready network tables.

## Reconstruction Workflows

### Genome to Model

Input:
- `data/input/genome.fna`

Expected sequence:
1. Prodigal
2. CarveMe
3. MEMOTE
4. COBRApy FBA

Expected outputs:
- `data/output/proteins.faa`
- `data/output/model.xml`
- `data/output/memote_report.html`
- `data/output/fba_result.txt`
- `data/output/refinegems_handoff.json`
- `data/output/cytoscape_nodes.tsv`
- `data/output/cytoscape_edges.tsv`

### Protein to Model

Input:
- `data/input/protein.faa`

Expected sequence:
1. CarveMe
2. MEMOTE
3. COBRApy FBA

## MCP Health Expectations

Healthy MCP endpoint:
- `http://localhost:8000/health`

Healthy agent endpoint:
- `http://localhost:9000/health`

If MCP is unavailable:
1. Tell the user MCP is down.
2. Fall back to this `SKILLS.md`.
3. Suggest starting the MCP server again.
4. If needed, use the direct local pipeline entrypoints.

## Portable Usage

Docker-first flow:

```bash
docker compose up --build -d --remove-orphans
```

Host pipeline fallback:

```bash
python -m apps.pipeline_cli --genome data/input/genome.fna --output-dir data/output
```

Host MCP server:

```bash
python -m apps.mcp_server
```

## Important Distinction

`apps/cli_chat.py` is not OpenCode.

It is a local test client for the repository's FastAPI agent.

OpenCode should instead use:
- [opencode.json](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\opencode.json)
- this `SKILLS.md`
- the MCP server from this repository

# GEM Tools Prototype

This repository packages a draft genome-scale metabolic model reconstruction workflow as:

- a FastMCP server for executable tooling
- an OpenCode workspace with a discoverable skill at `.opencode/skills/gem-workflow/SKILL.md`
- a Docker Compose stack that starts the dependencies together

The biological workflow is:

1. Prodigal: genome.fna -> proteins.faa
  - plus refineGEMs-ready `proteins_refinegems.faa` (NCBI-style headers)
2. CarveMe: proteins.faa -> model.xml
3. Optional refineGEMs curation: polish annotations, normalise biomass, fill missing charges
4. MEMOTE: model.xml -> memote_report.html
5. COBRApy FBA: model.xml -> predicted growth rate
6. Save results: fba_result.txt

## Installation

Create an environment and install the Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You still need the biological command-line tools available for local non-Docker execution:

- prodigal
- carve
- memote

The refineGEMs integration calls Python functions directly. It does not shell out to a refineGEMs CLI. Charge refinement also needs the MassChargeCuration dependency from the `requirements.txt` Git URL.

MEMOTE is invoked with `--ignore-git` so local experiments can run in a dirty worktree without forcing a commit or stash.

## CLI Mode

Genome input:

```bash
python pipeline.py --genome data/input/genome.fna --output-dir data/output
```

Protein input:

```bash
python pipeline.py --protein data/input/protein.faa --output-dir data/output
```

The previous entrypoint still works:

```bash
python src/gem_pipeline.py --genome data/input/genome.fna --output-dir data/output
```

Optional refineGEMs curation can run after CarveMe and before MEMOTE/FBA:

```bash
python src/gem_pipeline.py --protein data/input/protein.faa --output-dir data/output --refinegems-polish --refinegems-biomass --refinegems-charges
```

Useful refineGEMs flags:

- `--refinegems-polish`: cleans/polishes SBML annotations and model metadata.
- `--refinegems-biomass`: checks biomass reactions and normalises biomass coefficients toward 1 gCDW.
- `--refinegems-charges`: fills missing metabolite charges from ModelSEED/refineGEMs data and writes ambiguous charge options to JSON.
- `--refinegems-email`: email used by Entrez-backed polish steps.
- `--refinegems-id-db`: identifier namespace used by polishing, usually `BIGG` for CarveMe models.
- `--refinegems-lab-strain`: tells polish to keep lab-strain locus tags from the protein FASTA.

## MCP Server Mode

The FastMCP server exposes these tools:

- run_prodigal(fna_file)
- run_carveme(faa_file)
- run_memote(model_xml)
- get_memote_status(job_id)
- run_refinegems_polish(model_xml)
- refine_biomass(model_xml)
- refine_charges(model_xml)
- get_refinegems_status(job_id)
- run_fba(model_xml)
- inspect_model_stats(model_xml)
- query_reaction(model_xml, reaction_id)
- run_fva(model_xml, reaction_ids)
- simulate_gene_knockout(model_xml, gene_ids)

Run the server directly:

```bash
python mcp-server/server.py
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

## Docker Compose Mode

Copy `.env.example` to `.env` and set your Gemini API key:

```env
GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key_here
NEO4J_AUTH=neo4j/password
```

Then start the full workspace:

```bash
docker compose up --build --remove-orphans
```

For the normal interactive OpenCode experience, do not use `-d`. OpenCode is a terminal UI, so it should stay attached to your terminal.

If you already started it detached, attach to the running CLI container with:

```bash
docker attach gem-opencode
```

What this now does:

- starts Neo4j
- starts the FastMCP server on `http://localhost:8000/mcp`
- waits for the MCP server to become healthy
- opens the OpenCode CLI inside the `opencode` container
- makes the repo-local OpenCode skill available in the mounted workspace

Container-to-container endpoints:

- MCP: `http://gem-mcp-server:8000/mcp`
- Neo4j: `bolt://gem-neo4j:7687`

Host endpoints:

- MCP: `http://localhost:8000/mcp`
- Neo4j Browser: `http://localhost:7474`

## OpenCode Agent (Easiest)

OpenCode reads project config from `opencode.json` in the workspace root.

Inside Docker Compose, the config enables the in-network MCP endpoint by default:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "gem-tools-docker": {
      "type": "remote",
      "url": "http://gem-mcp-server:8000/mcp",
      "enabled": true
    },
    "gem-tools": {
      "type": "remote",
      "url": "http://localhost:8000/mcp",
      "enabled": false
    }
  }
}
```

If you want to run OpenCode on your host instead of in Docker, flip the `enabled` flags so `gem-tools` is enabled and `gem-tools-docker` is disabled.

You can also point to your hosted FastMCP URL if you have one:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "gem-tools": {
      "type": "remote",
      "url": "https://purring-amber-cat.fastmcp.app/mcp",
      "enabled": true
    }
  }
}
```

The same config is already included as `opencode.json` in this repository.

To use Gemini instead of OpenAI billing, start OpenCode and run:

```text
/connect
```

Then select the Google provider, paste your Gemini API key if prompted, and choose a Gemini model with:

```text
/models
```

The `opencode` container now persists auth data in a Docker volume, so your provider login survives container restarts.

## Workspace Skill

The repo now includes a discoverable OpenCode skill at `.opencode/skills/gem-workflow/SKILL.md`, which gives the agent a project-specific workflow for:

- CarveMe
- COBRApy
- MEMOTE
- refineGEMs integration planning
- Cytoscape integration planning

This means the agent starts with both executable MCP tools and local workflow guidance when launched through Docker Compose.

## File Input Examples

You can pass file paths directly when calling the MCP tools:

- `run_prodigal(fna_file="data/input/genome.fna", output_dir="outputs")`
- `run_prodigal(fna_file="data/input/genome.fna", output_dir="outputs", annotation_tsv="outputs/protein_annotations.tsv", default_organism="Bacillus sp.")`
- `run_carveme(faa_file="outputs/proteins.faa", output_dir="outputs")`
- `run_memote(model_xml="outputs/model.xml", output_dir="outputs")`
- `get_memote_status(job_id="<returned job id>")`
- `run_refinegems_polish(model_xml="outputs/model.xml", output_dir="outputs", email="you@example.org", id_db="BIGG", protein_fasta="outputs/proteins.faa", protein_annotation_tsv="outputs/protein_annotations.tsv", default_organism="Bacillus sp.")`
- `refine_biomass(model_xml="outputs/model_refinegems_polished.xml", output_dir="outputs")`
- `refine_charges(model_xml="outputs/model_refinegems_biomass.xml", output_dir="outputs")`
- `get_refinegems_status(job_id="<returned job id>")`
- `run_fba(model_xml="outputs/model.xml", output_dir="outputs")`
- `inspect_model_stats(model_xml="outputs/model.xml", output_dir="outputs")`
- `query_reaction(model_xml="outputs/model.xml", reaction_id="BIOMASS_Ec_iML1515_core_75p37M", output_dir="outputs")`
- `run_fva(model_xml="outputs/model.xml", reaction_ids=["EX_glc__D_e", "ATPM"], output_dir="outputs")`
- `simulate_gene_knockout(model_xml="outputs/model.xml", gene_ids=["b1779"], output_dir="outputs")`

## Expected data/output

- data/output/proteins.faa
- data/output/proteins_refinegems.faa
- data/output/model.xml
- data/output/model_refinegems_polished.xml
- data/output/model_refinegems_biomass.xml
- data/output/model_refinegems_charges.xml
- data/output/refinegems_charge_options.json
- data/output/memote_report.html
- data/output/fba_result.txt
- data/output/model_statistics.json
- data/output/reaction_<reaction_id>_details.json
- data/output/fva_results.json
- data/output/gene_knockout_results.json

## Protein annotation input format

Optional annotation files for `run_prodigal` and `run_refinegems_polish` should be UTF-8 TSV with at least two columns:

```text
query_id\tproduct_name\torganism_name(optional)
1_1\tDNA polymerase III subunit beta\tBacillus sp.
1_2\tABC transporter ATP-binding protein\tBacillus sp.
```

This lets you project BLAST/eggNOG/InterPro-style functional calls into NCBI-like FASTA headers such as:

```text
>prot_000001 DNA polymerase III subunit beta [Bacillus sp.]
```

## Citation

If this workflow helps your project, please cite:

Famke Bäuerle, Gwendolyn O. Döbel, Laura Camus, Simon Heilbronner, and Andreas Dräger. Genome-scale metabolic models consistently predict in vitro characteristics of Corynebacterium striatum. Front. Bioinform., oct 2023. doi:10.3389/fbinf.2023.1214074.

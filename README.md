# GEM Tools Prototype

This repository is now organized as an OpenCode-first proof of concept: OpenCode can use the local MCP server through [opencode.json](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\opencode.json), and it can fall back to [SKILLS.md](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\SKILLS.md) when MCP-backed tooling is unavailable.

The biological workflow is:

1. Prodigal: genome.fna -> proteins.faa
2. CarveMe: proteins.faa -> model.xml
3. MEMOTE: model.xml -> memote_report.html
4. COBRApy FBA: model.xml -> predicted growth rate
5. Save results: fba_result.txt

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

## CLI Mode

Genome input:

```bash
python -m apps.pipeline_cli --genome data/input/genome.fna --output-dir data/output
```

Protein input:

```bash
python -m apps.pipeline_cli --protein data/input/protein.faa --output-dir data/output
```

The compatibility wrapper still works:

```bash
python -m pipeline.pipeline --genome data/input/genome.fna --output-dir data/output
```

## MCP Server Mode

The FastMCP server exposes these tools:

- run_prodigal(fna_file)
- run_carveme(faa_file)
- run_memote(model_xml)
- run_fba(model_xml)
- prepare_refinegems_handoff(model_xml, output_dir, memote_report_html, fba_result_txt)
- prepare_cytoscape_export(model_xml, output_dir)

Run the server directly:

```bash
python -m apps.mcp_server
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

## Docker Compose Mode

Start the portable stack with Docker:

```bash
docker compose up --build -d --remove-orphans
```

The services expose:

- MCP server: `http://localhost:8000/mcp`
- Agent health: `http://localhost:9000/health`
- Agent prompt endpoint: `http://localhost:9000/prompt`
- Neo4j browser: `http://localhost:7474`

Run the terminal chat client against the agent from the same compose setup:

```bash
docker compose exec cli-agent python -m apps.cli_chat --url http://localhost:9000
```

The containers are attached to Docker network `gem-tools-net` with names `gem-mcp-server`, `gem-cli-agent`, and `gem-neo4j`.

## Conversational CLI

The agent accepts free-form prompts and routes file-based requests by extension:

- `.fna`: Prodigal -> CarveMe -> MEMOTE -> FBA
- `.faa`: CarveMe -> MEMOTE -> FBA
- `.xml`: MEMOTE and/or FBA

Example prompts:

```text
Run the pipeline for data/input/genome.fna
Build a model from data/input/protein.faa
Run memote and FBA for data/output/model.xml
```

The chat client can also run directly on the host:

```bash
python -m apps.cli_chat --url http://localhost:9000
```

Important:
`apps/cli_chat.py` is a local custom terminal client for this repository's FastAPI agent. It is useful for smoke-testing the workflow, but it is not the OpenCode chat application itself.

## OpenCode Setup

OpenCode reads project config from `opencode.json` (not `opencode.yaml`).

Use this OpenCode configuration file:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "gem-tools": {
      "type": "remote",
      "url": "http://localhost:8000/mcp",
      "enabled": true
    },
    "gem-tools-docker": {
      "type": "remote",
      "url": "http://gem-mcp-server:8000/mcp",
      "enabled": false
    }
  }
}
```

Use `gem-tools` when OpenCode runs on your host machine.

If OpenCode runs in Docker on the same network, either enable `gem-tools-docker` or connect your OpenCode container to the MCP network:

```bash
docker network connect gem-tools-net <opencode_container_name>
```

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

The same config is already added as `opencode.json` in this repository.

To use this project with OpenCode, the intended flow is:

1. Start the MCP server, locally or with Docker.
2. Open this repository in OpenCode.
3. Make sure OpenCode loads [opencode.json](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\opencode.json).
4. Keep [SKILLS.md](c:\Users\light\OneDrive\Desktop\Open Source\NRNB\demo\SKILLS.md) in the repo so the agent also has non-MCP tool guidance and fallback instructions.
5. Ask OpenCode directly for tasks such as reconstructing a model from `data/input/genome.fna`, preparing a refineGEMs handoff, or exporting a Cytoscape-ready network from `data/output/model.xml`.

In other words:

- `python -m apps.cli_chat` talks to your local FastAPI agent
- OpenCode talks to the MCP server defined in `opencode.json` and can also read `SKILLS.md`

## File Input Examples

You can pass file paths directly when calling the MCP tools:

- `run_prodigal(fna_file="data/input/genome.fna", output_dir="outputs")`
- `run_carveme(faa_file="outputs/proteins.faa", output_dir="outputs")`
- `run_memote(model_xml="outputs/model.xml", output_dir="outputs")`
- `run_fba(model_xml="outputs/model.xml", output_dir="outputs")`
- `prepare_refinegems_handoff(model_xml="outputs/model.xml", output_dir="outputs")`
- `prepare_cytoscape_export(model_xml="outputs/model.xml", output_dir="outputs")`

## Expected data/output

- data/output/proteins.faa
- data/output/model.xml
- data/output/memote_report.html
- data/output/fba_result.txt
- data/output/refinegems_handoff.json
- data/output/cytoscape_nodes.tsv
- data/output/cytoscape_edges.tsv

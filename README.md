# GEM Tools Prototype

This repository extends the existing genome-scale metabolic model reconstruction prototype into a reusable pipeline module plus a FastMCP server. The biological workflow is unchanged:

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

## MCP Server Mode

The FastMCP server exposes these tools:

- run_prodigal(fna_file)
- run_carveme(faa_file)
- run_memote(model_xml)
- run_fba(model_xml)

Run the server directly:

```bash
python mcp-server/server.py
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

## Docker Compose Mode

Start the local MCP server with Docker:

```bash
docker compose up --build --remove-orphans
```

The server exposes:

- Local MCP URL

The service is also attached to Docker network `gem-tools-net` with container name `gem-mcp-server`.

## OpenCode Agent (Easiest)

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

## File Input Examples

You can pass file paths directly when calling the MCP tools:

- `run_prodigal(fna_file="data/input/genome.fna", output_dir="outputs")`
- `run_carveme(faa_file="outputs/proteins.faa", output_dir="outputs")`
- `run_memote(model_xml="outputs/model.xml", output_dir="outputs")`
- `run_fba(model_xml="outputs/model.xml", output_dir="outputs")`

## Expected data/output

- data/output/proteins.faa
- data/output/model.xml
- data/output/memote_report.html
- data/output/fba_result.txt

# GEM Tools Prototype

This repository extends the existing genome-scale metabolic model reconstruction prototype into a reusable pipeline module plus a FastMCP server. The biological workflow is unchanged:

1. Prodigal: genome.fna -> proteins.faa
2. CarveMe: proteins.faa -> model.xml
3. MEMOTE: model.xml -> memote_report.html
4. COBRApy FBA: model.xml -> predicted growth rate
5. Save results: fba_result.txt

## Project Layout

```text
docker-compose.yml
docker/
	Dockerfile
mcp-server/
	server.py
	tools/
pipeline/
	pipeline.py
outputs/
data/
pipeline.py
```

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
python pipeline.py --genome data/input/genome.fna --output-dir outputs
```

Protein input:

```bash
python pipeline.py --protein data/input/protein.faa --output-dir outputs
```

The previous entrypoint still works:

```bash
python src/gem_pipeline.py --genome data/input/genome.fna --output-dir outputs
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

Provide an ngrok auth token if you want a public tunnel:

```bash
# bash
export NGROK_AUTHTOKEN=your_token
# PowerShell
$env:NGROK_AUTHTOKEN="your_token"
docker compose up --build
```

The server container prints:

- Local MCP URL
- Public ngrok MCP URL

If ngrok is not configured, the local MCP server still runs and the public URL is reported as unavailable.

## Expected Outputs

- outputs/proteins.faa
- outputs/model.xml
- outputs/memote_report.html
- outputs/fba_result.txt

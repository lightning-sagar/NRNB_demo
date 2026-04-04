# GEM Fallback Skill

Use this fallback when the MCP server health check is failing.

## What To Do

1. Confirm the agent is still reachable on `/health`.
2. Start or restart the MCP server.
3. Re-run the same prompt after MCP is healthy again.

## MCP Recovery

Host run:

```bash
python apps/mcp_server.py
```

Docker run:

```bash
docker compose up --build -d mcp-server
```

## Pipeline Fallback

If MCP is down and you still need outputs, run the local pipeline entrypoint directly:

```bash
python apps/pipeline_cli.py --genome data/input/genome.fna --output-dir data/output
```

Or for proteins:

```bash
python apps/pipeline_cli.py --protein data/input/protein.faa --output-dir data/output
```

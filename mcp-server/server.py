import os
import sys
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.carveme_tool import get_carveme_status_tool, run_carveme_tool
from tools.cobra_tool import (
    inspect_model_statistics_tool,
    query_reaction_details_tool,
    run_fba_tool,
    run_fva_tool,
    simulate_gene_knockout_effects_tool,
)
from tools.memote_tool import run_memote_tool
from tools.prodigal_tool import run_prodigal_tool


HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp")


mcp = FastMCP("gem-tools")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


@mcp.tool
def ping() -> dict[str, str]:
    """Check whether the GEM MCP server is reachable and responding."""
    return {
        "status": "ok",
        "server": "gem-tools",
        "mcp_path": MCP_PATH,
        "health_url": f"http://localhost:{PORT}/health",
    }


@mcp.tool
def run_prodigal(fna_file: str, output_dir: str = "data/output") -> dict[str, str]:
    return run_prodigal_tool(fna_file=fna_file, output_dir=output_dir)


@mcp.tool
def run_carveme(faa_file: str, output_dir: str = "data/output") -> dict[str, str]:
    return run_carveme_tool(faa_file=faa_file, output_dir=output_dir)


@mcp.tool
def get_carveme_status(job_id: str) -> dict[str, str]:
    return get_carveme_status_tool(job_id=job_id)


@mcp.tool
def run_memote(model_xml: str, output_dir: str = "data/output") -> dict[str, str]:
    return run_memote_tool(model_xml=model_xml, output_dir=output_dir)


@mcp.tool
def run_fba(model_xml: str, output_dir: str = "data/output") -> dict[str, str | float]:
    return run_fba_tool(model_xml=model_xml, output_dir=output_dir)


@mcp.tool
def inspect_model_stats(model_xml: str, output_dir: str = "data/output") -> dict[str, object]:
    return inspect_model_statistics_tool(model_xml=model_xml, output_dir=output_dir)


@mcp.tool
def query_reaction(model_xml: str, reaction_id: str, output_dir: str = "data/output") -> dict[str, object]:
    return query_reaction_details_tool(
        model_xml=model_xml,
        reaction_id=reaction_id,
        output_dir=output_dir,
    )


@mcp.tool
def run_fva(
    model_xml: str,
    reaction_ids: list[str],
    output_dir: str = "data/output",
    fraction_of_optimum: float = 1.0,
) -> dict[str, object]:
    return run_fva_tool(
        model_xml=model_xml,
        reaction_ids=reaction_ids,
        output_dir=output_dir,
        fraction_of_optimum=fraction_of_optimum,
    )


@mcp.tool
def simulate_gene_knockout(
    model_xml: str,
    gene_ids: list[str],
    output_dir: str = "data/output",
) -> dict[str, object]:
    return simulate_gene_knockout_effects_tool(
        model_xml=model_xml,
        gene_ids=gene_ids,
        output_dir=output_dir,
    )


def print_local_url():
    print(f"Local MCP URL: http://localhost:{PORT}{MCP_PATH}", flush=True)
    print(f"Health URL: http://localhost:{PORT}/health", flush=True)


if __name__ == "__main__":
    print_local_url()
    mcp.run(transport="http", host=HOST, port=PORT)

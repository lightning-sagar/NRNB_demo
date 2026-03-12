import json
import os
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from fastmcp import FastMCP


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.carveme_tool import run_carveme_tool
from tools.cobra_tool import run_fba_tool
from tools.memote_tool import run_memote_tool
from tools.prodigal_tool import run_prodigal_tool


HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp")
NGROK_API_URL = os.getenv("NGROK_API_URL", "http://ngrok:4040/api/tunnels")
NGROK_POLL_SECONDS = int(os.getenv("NGROK_POLL_SECONDS", "30"))


mcp = FastMCP("gem-tools")


@mcp.tool
def run_prodigal(fna_file: str, output_dir: str = "outputs") -> dict[str, str]:
    return run_prodigal_tool(fna_file=fna_file, output_dir=output_dir)


@mcp.tool
def run_carveme(faa_file: str, output_dir: str = "outputs") -> dict[str, str]:
    return run_carveme_tool(faa_file=faa_file, output_dir=output_dir)


@mcp.tool
def run_memote(model_xml: str, output_dir: str = "outputs") -> dict[str, str]:
    return run_memote_tool(model_xml=model_xml, output_dir=output_dir)


@mcp.tool
def run_fba(model_xml: str, output_dir: str = "outputs") -> dict[str, str | float]:
    return run_fba_tool(model_xml=model_xml, output_dir=output_dir)


def print_local_url():
    print(f"Local MCP URL: http://localhost:{PORT}{MCP_PATH}", flush=True)


def print_public_url():
    for _ in range(NGROK_POLL_SECONDS):
        try:
            with urlopen(NGROK_API_URL, timeout=2) as response:
                payload = json.load(response)
        except (URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(1)
            continue

        tunnels = payload.get("tunnels", [])
        public_url = next((item.get("public_url") for item in tunnels if item.get("public_url")), None)
        if public_url:
            print(f"Public ngrok MCP URL: {public_url}{MCP_PATH}", flush=True)
            return
        time.sleep(1)

    print("Public ngrok MCP URL: unavailable", flush=True)


if __name__ == "__main__":
    print_local_url()
    print_public_url()
    mcp.run(transport="http", host=HOST, port=PORT)
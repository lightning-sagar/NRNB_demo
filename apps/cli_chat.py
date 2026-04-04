from __future__ import annotations

import argparse
import json
from urllib import error
from urllib import request

try:
    from apps.bootstrap import ensure_project_root
except ModuleNotFoundError:
    from bootstrap import ensure_project_root

ensure_project_root()

from agent.client import send_prompt
from agent.config import DEFAULT_AGENT_URL, DEFAULT_OUTPUT_DIR


def fetch_health(base_url: str) -> dict | None:
    try:
        with request.urlopen(f"{base_url.rstrip('/')}/health", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Conversational CLI for the GEM prompt agent")
    parser.add_argument("--url", default=DEFAULT_AGENT_URL, help="Base URL for the agent service")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory for routed jobs")
    args = parser.parse_args()

    print("GEM local CLI started. This is a custom terminal client for the local agent, not the OpenCode chat UI.")
    print("For OpenCode, use the repo's opencode.json and SKILLS.md with your OpenCode runtime.")
    print("Type a prompt with a .fna, .faa, or .xml path. Type 'exit' to quit.")
    health = fetch_health(args.url)
    if health is None:
        print("agent > Health check unavailable. I will still try to send prompts.")
    elif health["mcp_status"] == "ok":
        print("agent > MCP health check is OK.")
    else:
        print(
            "agent > MCP is unavailable. Fallback mode is active via "
            f"{health.get('fallback', 'SKILL.md')}."
        )
    while True:
        try:
            prompt = input("user > ").strip()
        except EOFError:
            print()
            break
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            break

        try:
            print("agent > Working on it...")
            response = send_prompt(args.url, prompt, args.output_dir)
            print(f"agent > {response.reply}")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"agent > Request failed ({exc.code}): {body}")
        except Exception as exc:
            print(f"agent > Request failed: {exc}")


if __name__ == "__main__":
    main()

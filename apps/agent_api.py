from __future__ import annotations

from fastapi import FastAPI, HTTPException
import uvicorn

try:
    from apps.bootstrap import ensure_project_root
except ModuleNotFoundError:
    from bootstrap import ensure_project_root

ensure_project_root()

from agent.config import AGENT_HOST, AGENT_PORT
from agent.health import get_mcp_health
from agent.models import PromptRequest, PromptResponse
from agent.service import run_prompt_workflow


app = FastAPI(title="gem-opencode-agent")


@app.get("/health")
def health() -> dict[str, str]:
    mcp_health = get_mcp_health()
    return {
        "status": "ok" if mcp_health["status"] == "ok" else "degraded",
        "agent": "ok",
        "mcp_status": mcp_health["status"],
        "mode": mcp_health["mode"],
        "detail": mcp_health["detail"],
        "health_url": mcp_health["health_url"],
        "fallback": mcp_health.get("fallback", ""),
    }


@app.post("/prompt", response_model=PromptResponse)
def prompt(request: PromptRequest) -> PromptResponse:
    try:
        return run_prompt_workflow(request.prompt, request.output_dir)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def main() -> None:
    uvicorn.run(app, host=AGENT_HOST, port=AGENT_PORT)


if __name__ == "__main__":
    main()

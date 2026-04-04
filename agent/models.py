from __future__ import annotations

from pydantic import BaseModel

from agent.config import DEFAULT_OUTPUT_DIR


class PromptRequest(BaseModel):
    prompt: str
    output_dir: str = DEFAULT_OUTPUT_DIR


class PromptResponse(BaseModel):
    reply: str
    routed_file: str | None = None
    output_dir: str | None = None
    mcp_status: str | None = None
    mode: str | None = None

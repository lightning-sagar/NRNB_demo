from __future__ import annotations

import json
from urllib import request

from agent.models import PromptResponse


def send_prompt(base_url: str, prompt: str, output_dir: str) -> PromptResponse:
    payload = json.dumps({"prompt": prompt, "output_dir": output_dir}).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=900) as response:
        return PromptResponse(**json.loads(response.read().decode("utf-8")))

#!/bin/sh
set -eu

echo "Workspace: /workspace"
echo "Using MCP config from /workspace/opencode.json"
echo "Using skills from /workspace/.opencode/skills/gem-workflow/SKILL.md"

exec opencode

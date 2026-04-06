---
name: gem-workflow
description: Guide genome-scale metabolic model reconstruction and analysis in this repo, with MCP-first execution and local fallback when MCP is unavailable.
license: MIT
compatibility: opencode
metadata:
  domain: systems-biology
  workflow: gem-reconstruction
---

## What I do

- Guide bacterial GEM reconstruction from `data/input/genome.fna` or `data/input/protein.faa`
- Prefer MCP tools for executable steps when available
- Fall back to local project commands and existing outputs only when MCP is unavailable
- Explain biological outputs without pretending automated drafts are fully validated models

## When to use me

Use this skill when working on:

- `Prodigal -> CarveMe -> MEMOTE -> FBA` workflows
- interpretation of `data/output/model.xml`, MEMOTE results, FBA output, FVA ranges, or knockout simulations
- deciding the next validation step for a draft GEM

## Primary workflow

1. Start from a bacterial genome FASTA in `data/input/genome.fna` or a protein FASTA in `data/input/protein.faa`.
2. Use MCP tools for the executable steps:
   - `ping()`
   - `run_prodigal(fna_file, output_dir)`
   - `run_carveme(faa_file, output_dir)`
  - `get_carveme_status(job_id)`
  - `run_memote(model_xml, output_dir)`
  - `run_fba(model_xml, output_dir)`
  - `inspect_model_stats(model_xml, output_dir)`
  - `query_reaction(model_xml, reaction_id, output_dir)`
  - `run_fva(model_xml, reaction_ids, output_dir, fraction_of_optimum)`
  - `simulate_gene_knockout(model_xml, gene_ids, output_dir)`
3. Store generated artifacts under `data/output` unless the user asks for a different location.
4. Explain each result in biological terms: what the tool does, what files it produced, and what the user should inspect next.

## Tool guidance

### CarveMe

- Purpose: draft GEM reconstruction from protein sequences.
- Typical input: `data/output/proteins.faa` or `data/input/protein.faa`.
- Typical output: SBML model such as `data/output/model.xml`.
- Ask the user to review draft biomass, exchange reactions, and media assumptions before treating the model as analysis-ready.

### COBRApy

- Purpose: inspect and simulate the reconstructed model.
- In this workspace:
  - `inspect_model_stats` summarizes model size, compartment coverage, and objective metadata.
  - `query_reaction` explains one reaction's equation, bounds, subsystem, and GPR.
  - `run_fba` performs a simple flux balance analysis on an SBML model.
  - `run_fva` estimates feasible flux ranges for selected reactions.
  - `simulate_gene_knockout` estimates growth effects for selected gene deletions.
- Report objective values clearly and mention that growth predictions, FVA ranges, and knockout effects depend on the chosen medium and objective formulation.

### MEMOTE

- Purpose: model quality assessment.
- Use `run_memote` after reconstruction or after any substantial model refinement.
- Summarize the report rather than dumping raw output. Highlight blocked reactions, annotation gaps, stoichiometric issues, and namespace consistency.

### refineGEMs

- Purpose: downstream curation and annotation refinement.
- Current status in this repo: documented workflow target, not yet exposed as an MCP tool.
- If a user asks for refineGEMs-specific work, explain that the next implementation step is to add either a dedicated MCP wrapper or a containerized helper command.

### Cytoscape

- Purpose: network visualization and exploratory pathway analysis.
- Current status in this repo: documented integration target, not yet exposed as an MCP tool.
- If the user wants graph visualization, prepare exports that Cytoscape can consume and describe what network slice should be inspected.

## Working style

- Prefer MCP tools over ad hoc shell commands when the tool is already exposed.
- For simple MCP availability checks, use `ping()` instead of `get_carveme_status`.
- Keep file paths explicit in every tool call.
- Flag biological uncertainty instead of masking it with confident prose.
- Treat automated reconstruction as a draft that needs validation, not a final model.

## MCP fallback

- Only use this fallback path when MCP is unavailable.
- First try MCP availability with `ping()`.
- When MCP is down, do not claim tools are available and do not guess job IDs.
- When the user mentions a file loosely, ask for the exact path only if it cannot be found safely.
- Before choosing a fallback command, check both `data/output` and `data/input` for the relevant file.
- Prefer existing generated outputs over rerunning earlier steps unnecessarily.
- Fall back to local commands:
  - For genome input, use `python pipeline/pipeline.py --genome <resolved_path> --output-dir data/output`
  - For protein input, use `python pipeline/pipeline.py --protein <resolved_path> --output-dir data/output`
- Resolution rule:
  - if the requested protein file exists in `data/output`, use that path
  - else if it exists in `data/input`, use that path
  - else ask the user to provide the correct path
- If the user asks for FBA on an existing SBML model and MCP is unavailable, run the local pipeline function directly:
  - `python -c "from pathlib import Path; from pipeline.pipeline import run_fba, save_fba_result; model_path = Path('data/output/model.xml') if Path('data/output/model.xml').exists() else Path('data/input/model.xml'); growth_rate = run_fba(model_path); print(f'Growth rate: {growth_rate:.6f}'); save_fba_result(growth_rate, Path('data/output/fba_result.txt'))"`
- If MCP is unavailable for inspection-oriented COBRApy analysis, use local functions from `pipeline.pipeline`:
  - `inspect_model_statistics`
  - `query_reaction_details`
  - `run_fva`
  - `simulate_gene_knockout_effects`
- Do not start fallback by exploring unrelated files or importing from `mcp-server/tools/*` directly when `pipeline.pipeline` already exposes the supported local functions.
- If outputs already exist, interpret files under `data/output` directly instead of blocking on MCP recovery.
- When execution is blocked, provide the next biological validation steps rather than pretending the run succeeded.

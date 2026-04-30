# SOP Supervisor Agent

Turn any repeatable SOP into a supervised local agent workflow.

SOP Supervisor Agent is a small, stdlib-first orchestration layer for people who already have good operating procedures, prompts, review rules, or handoff checklists, and want agents to execute them without turning the process into an untraceable chat thread.

It gives each agent run a durable paper trail: rendered prompt, selected runner, inputs, stdout, stderr, parsed output, metadata, checker report, and retry attempts. The goal is simple: make SOP-driven agent work repeatable, inspectable, and safe to improve.

## Why This Exists

Most agent workflows fail in boring ways:

- the prompt that produced a result is lost
- a manual SOP drifts after a few runs
- one model is hardwired into the whole process
- retries happen by memory instead of by policy
- review rules live in someone's head
- artifacts are scattered across terminals, chats, and files

This project treats an agent workflow like an executable runbook. A workflow declares the step, prompt template, runner, checker, and retry policy. The supervisor renders the prompt, runs the selected CLI, stores every artifact, and optionally routes failed checks into a rework prompt.

## What It Does

- Defines SOP workflows as `workflow.json` or `workflow.yaml`
- Renders prompt templates with explicit input variables
- Runs local agent CLIs through pluggable runners
- Supports `codex_cli` and `gemini_cli`
- Saves every run under a predictable artifact directory
- Supports dry-runs for prompt inspection before execution
- Allows workflow-local context builders, checkers, and rework prompts
- Keeps the generic registry separate from domain-specific checkers

## Requirements

- Python 3.9+
- Codex CLI for `codex_cli` runner
- Gemini CLI for `gemini_cli` runner
- PyYAML only if you want to use `workflow.yaml`; JSON workflows work with the Python standard library

## Quick Start

Clone and run tests:

```bash
git clone https://github.com/lulu1373/sop-supervisor-agent.git
cd sop-supervisor-agent
python3 -m unittest discover -s tests
```

Dry-run the bundled workflow:

```bash
python3 scripts/sop_supervisor.py run \
  --workflow document_review \
  --step review_note \
  --input job_id=demo-note \
  --input artifact_label="Demo Note" \
  --input review_goal="Find gaps and risks" \
  --input source_text="A short note to review." \
  --dry-run
```

Run the workflow with Codex:

```bash
python3 scripts/sop_supervisor.py run \
  --workflow document_review \
  --step review_note \
  --input job_id=demo-note \
  --input artifact_label="Demo Note" \
  --input review_goal="Find gaps and risks" \
  --input source_text="A short note to review."
```

Artifacts are written under `docs/supervisor-runs/` by default.

## Architecture

```text
workflow.json
  -> prompt template
  -> optional context.py
  -> runner: codex_cli / gemini_cli / custom
  -> optional checker
  -> artifacts per attempt
```

The supervisor separates three concerns:

- Workflow config declares steps, prompt templates, runner, checker, and retry policy.
- Runner executes a rendered prompt with a local CLI such as Codex or Gemini.
- Artifacts store prompts, metadata, command output, parsed output, and checker reports.

## Workflow Shape

Each workflow lives under `supervisor/workflows/<workflow_id>/` and provides a `workflow.json` or `workflow.yaml`.

```json
{
  "id": "document_review",
  "defaults": {
    "run_root": "docs/supervisor-runs"
  },
  "steps": {
    "review_note": {
      "prompt_template": "prompts/review_note.md",
      "runner": "codex_cli",
      "checker": "none",
      "allow_edits": false
    }
  }
}
```

Prompt templates use Python `string.Template` placeholders, for example `${source_text}`.

## Included Example

The repository includes `document_review`, a minimal workflow that reviews a provided note or document excerpt. It is intentionally small, because the important point is the control plane: the same engine can run a writing review, research SOP, QA checklist, code audit, customer-support triage, or any other repeatable multi-step procedure.

## Design Principles

- Local first: runs through local CLIs and writes artifacts to disk.
- Inspectable: dry-run first, then execute with a saved prompt bundle.
- Runner neutral: the workflow chooses the runner; the engine does not care which model is behind it.
- Domain neutral: checkers and context builders belong to workflows, not the generic core.
- Boring by design: standard library first, JSON always supported, YAML optional.

## Tests

```bash
python3 -m unittest discover -s tests
```

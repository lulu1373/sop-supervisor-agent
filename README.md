# SOP Supervisor Agent

Generic local supervisor for running SOP-style agent workflows.

It separates three concerns:

- workflow config: declares steps, prompt templates, runner, checker, and retry policy
- runner: executes a rendered prompt with a local CLI such as Codex or Gemini
- artifacts: stores prompts, metadata, command output, and checker reports per attempt

The repository includes a minimal non-assessment workflow, `document_review`, to prove the supervisor is not coupled to one business domain.

## Requirements

- Python 3.9+
- Codex CLI for `codex_cli` runner
- Gemini CLI for `gemini_cli` runner
- PyYAML only if you want to use `workflow.yaml`; JSON workflows work with the Python standard library

## Quick Start

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

## Tests

```bash
python3 -m unittest discover -s tests
```

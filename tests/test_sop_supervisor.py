from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "sop_supervisor.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SopSupervisorTests(unittest.TestCase):
    def test_render_template_rejects_missing_key(self) -> None:
        from supervisor.core.templating import render_prompt_text

        with self.assertRaises(KeyError):
            render_prompt_text("hello ${name} ${missing}", {"name": "world"})

    def test_load_workflow_config_supports_json(self) -> None:
        from supervisor.core.engine import load_workflow_config

        with TemporaryDirectory() as tmp_dir:
            workflow_path = Path(tmp_dir) / "workflow.json"
            workflow_path.write_text(
                json.dumps(
                    {
                        "id": "demo",
                        "defaults": {"run_root": "runs/demo"},
                        "steps": {
                            "draft": {
                                "prompt_template": "prompts/draft.md",
                                "runner": "codex_cli",
                                "checker": "none",
                                "allow_edits": False,
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            config = load_workflow_config(workflow_path)

        self.assertEqual(config.workflow_id, "demo")
        self.assertEqual(config.steps["draft"].runner, "codex_cli")
        self.assertEqual(config.defaults.run_root, "runs/demo")

    def test_codex_runner_builds_expected_command(self) -> None:
        from supervisor.core.models import RunnerRequest
        from supervisor.runners.codex_cli import CodexCliRunner

        runner = CodexCliRunner()
        request = RunnerRequest(
            prompt="Reply with OK only.",
            cwd=ROOT,
            timeout_seconds=120,
            allow_edits=False,
            env={},
            metadata={},
        )

        with mock.patch("supervisor.runners.codex_cli.shutil.which", return_value="/opt/bin/codex"):
            with mock.patch("supervisor.runners.codex_cli.subprocess.run") as run_mock:
                run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                result = runner.run(request)

        self.assertEqual(result.command[0], "/opt/bin/codex")
        self.assertEqual(result.command[1], "exec")
        self.assertIn("--skip-git-repo-check", result.command)
        self.assertIn("--sandbox", result.command)
        self.assertIn("read-only", result.command)
        self.assertEqual(result.exit_code, 0)

    def test_generic_registry_does_not_load_checkers_by_default(self) -> None:
        from supervisor.core.generic_registry import build_registry

        registry = build_registry()

        self.assertIn("codex_cli", registry.runners)
        self.assertIn("gemini_cli", registry.runners)
        self.assertEqual(registry.checkers, {})

    def test_sop_supervisor_prints_codex_last_message_when_stdout_empty(self) -> None:
        module = load_module(SCRIPT_PATH, "sop_supervisor_script_print_result")
        result = module.RunnerResult(
            command=["codex"],
            exit_code=0,
            stdout_text="",
            stderr_text="",
            parsed_output={"last_message": "OK from Codex"},
            started_at="",
            finished_at="",
        )

        with mock.patch("builtins.print") as print_mock:
            module.print_runner_output(result)

        print_mock.assert_called_once_with("OK from Codex")

    def test_engine_dry_run_uses_generic_job_id_without_domain_inputs(self) -> None:
        from supervisor.core.engine import SupervisorEngine, load_workflow_from_directory
        from supervisor.core.generic_registry import build_registry

        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow_dir = root / "workflow"
            prompts_dir = workflow_dir / "prompts"
            prompts_dir.mkdir(parents=True)
            (prompts_dir / "draft.md").write_text("Hello ${subject}", encoding="utf-8")
            (workflow_dir / "workflow.json").write_text(
                json.dumps(
                    {
                        "id": "demo",
                        "defaults": {"run_root": str(root / "runs")},
                        "steps": {
                            "draft": {
                                "prompt_template": "prompts/draft.md",
                                "runner": "codex_cli",
                                "checker": "none",
                                "allow_edits": False,
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            workflow = load_workflow_from_directory(workflow_dir)
            engine = SupervisorEngine(build_registry())
            outcome = engine.run(
                workflow=workflow,
                step_id="draft",
                inputs={"subject": "world"},
                runner_name=None,
                timeout_seconds=60,
                dry_run=True,
            )

        self.assertEqual(outcome.parent_run_dir.parent.name, "demo-draft")

    def test_builtin_document_review_workflow_dry_run_renders_inputs(self) -> None:
        from supervisor.core.engine import SupervisorEngine, load_workflow_from_directory
        from supervisor.core.generic_registry import build_registry

        with TemporaryDirectory() as tmp_dir:
            workflow = load_workflow_from_directory(
                ROOT / "supervisor" / "workflows" / "document_review"
            )
            workflow.defaults.run_root = str(Path(tmp_dir) / "runs")
            engine = SupervisorEngine(build_registry())

            outcome = engine.run(
                workflow=workflow,
                step_id="review_note",
                inputs={
                    "job_id": "note-1",
                    "artifact_label": "Demo Note",
                    "review_goal": "point out gaps",
                    "source_text": "Alpha beta gamma",
                },
                runner_name=None,
                timeout_seconds=60,
                dry_run=True,
            )

            prompt_text = outcome.prompt_path.read_text(encoding="utf-8")
            self.assertIn("Demo Note", prompt_text)
            self.assertIn("point out gaps", prompt_text)
            self.assertIn("Alpha beta gamma", prompt_text)


if __name__ == "__main__":
    unittest.main()

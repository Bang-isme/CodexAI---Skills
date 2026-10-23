from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "codex-project-memory" / "scripts"
SUMMARY_SCRIPT = SCRIPT_DIR / "generate_session_summary.py"
sys.path.insert(0, str(SCRIPT_DIR))
import compact_context  # noqa: E402
import generate_session_summary  # noqa: E402


def run_summary_cli(project_root: Path, since: str, output_dir: Path) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
            "--project-root",
            str(project_root),
            "--since",
            since,
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(f"session-summary CLI failed: {completed.stderr or completed.stdout}")
    return json.loads(completed.stdout)


def complete_generated_checkpoint(summary_path: Path) -> None:
    content = summary_path.read_text(encoding="utf-8")
    for prompt in generate_session_summary.SESSION_PROMPT_MARKERS:
        if prompt == "[Fill from the user request]":
            replacement = "Verify stable checkpoint cutoff"
        elif prompt == "[in_progress | completed | blocked]":
            replacement = "in_progress"
        else:
            replacement = "None"
        content = content.replace(prompt, replacement)
    summary_path.write_text(content, encoding="utf-8")


class SessionSummaryWorktreeTests(unittest.TestCase):
    def test_summary_includes_staged_unstaged_and_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir(parents=True)
            output_dir = Path(temporary) / "summaries"

            def git(*args: str) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            for filename in ("staged.txt", "unstaged.txt"):
                (project_root / filename).write_text("base\n", encoding="utf-8")
            git("add", "staged.txt", "unstaged.txt")
            git("commit", "--quiet", "-m", "feat: add endpoint")
            expected_branch = git("branch", "--show-current")
            expected_root = git("rev-parse", "--show-toplevel")
            expected_head = git("rev-parse", "--short", "HEAD")

            (project_root / "staged.txt").write_text("staged version\n", encoding="utf-8")
            git("add", "staged.txt")
            (project_root / "staged.txt").write_text("staged and unstaged version\n", encoding="utf-8")
            (project_root / "unstaged.txt").write_text("unstaged version\n", encoding="utf-8")
            (project_root / "untracked.txt").write_text("new repro\n", encoding="utf-8")

            result = run_summary_cli(
                project_root,
                "2000-01-01",
                output_dir,
            )

            summary = Path(str(result["path"])).read_text(encoding="utf-8")
            archived = compact_context.parse_session_file(Path(str(result["path"])))

        self.assertIn("## Working Tree", summary)
        self.assertIn("## Task State", summary)
        self.assertIn("## In Progress", summary)
        self.assertIn("## Commands Verified", summary)
        self.assertIn("## Next Steps", summary)
        self.assertIn("## Recent Commits", summary)
        self.assertIn("feat: add endpoint", summary)
        self.assertIn(f"- Branch: {expected_branch}", summary)
        self.assertIn(f"- HEAD: {expected_head}", summary)
        self.assertIn("- Files changed: 2", summary)
        self.assertIn("### Staged Changes", summary)
        self.assertIn("- staged.txt", summary)
        self.assertIn("### Unstaged Changes", summary)
        self.assertIn("- unstaged.txt", summary)
        self.assertIn("### Untracked Files", summary)
        self.assertIn("- untracked.txt", summary)
        self.assertEqual(result["working_tree_files"], 3)
        self.assertEqual(result["branch"], expected_branch)
        self.assertEqual(Path(str(result["git_root"])), Path(expected_root))
        self.assertEqual(result["head"], expected_head)
        self.assertIsNotNone(datetime.fromisoformat(str(result["checkpoint_created"])))
        self.assertEqual(result["staged_files"], 1)
        self.assertEqual(result["unstaged_files"], 2)
        self.assertEqual(result["untracked_files"], 1)
        self.assertEqual(archived["files_changed"], 2)
        self.assertIn("staged.txt", archived["key_changes"])

    def test_summary_handles_an_unborn_git_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir()
            subprocess.run(["git", "init", "--quiet"], cwd=project_root, check=True)

            result = run_summary_cli(
                project_root,
                "today",
                Path(temporary) / "summaries",
            )
            summary = Path(str(result["path"])).read_text(encoding="utf-8")

        self.assertEqual(result["head"], "unborn")
        self.assertEqual(result["commits"], 0)
        self.assertIn("- HEAD: unborn", summary)

    def test_last_session_uses_checkpoint_time_after_summary_is_edited(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir()
            output_dir = Path(temporary) / "summaries"

            def git(*args: str, env: dict[str, str] | None = None) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=project_root,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            (project_root / "base.txt").write_text("base\n", encoding="utf-8")
            git("add", "base.txt")
            base_commit_time = datetime.now().astimezone() - timedelta(minutes=5)
            git(
                "commit",
                "--quiet",
                "-m",
                "chore: initialize",
                env={
                    **os.environ,
                    "GIT_AUTHOR_DATE": base_commit_time.isoformat(),
                    "GIT_COMMITTER_DATE": base_commit_time.isoformat(),
                },
            )

            first = run_summary_cli(project_root, "2000-01-01", output_dir)
            first_summary = Path(str(first["path"]))
            checkpoint_created = datetime.fromisoformat(str(first["checkpoint_created"]))
            checkpoint_text = first_summary.read_text(encoding="utf-8")
            self.assertIn(
                f"- Checkpoint created: {checkpoint_created.isoformat(timespec='seconds')}",
                checkpoint_text,
            )
            complete_generated_checkpoint(first_summary)
            future_commit = datetime.now().astimezone() + timedelta(minutes=10)
            future_iso = future_commit.isoformat()
            (project_root / "followup.txt").write_text("follow-up\n", encoding="utf-8")
            git("add", "followup.txt")
            git(
                "commit",
                "--quiet",
                "-m",
                "fix: follow-up after checkpoint",
                env={
                    **os.environ,
                    "GIT_AUTHOR_DATE": future_iso,
                    "GIT_COMMITTER_DATE": future_iso,
                },
            )

            edited_at = future_commit + timedelta(hours=1)
            os.utime(first_summary, (edited_at.timestamp(), edited_at.timestamp()))
            second = run_summary_cli(project_root, "last-session", output_dir)
            second_summary = Path(str(second["path"])).read_text(encoding="utf-8")

        self.assertIn("fix: follow-up after checkpoint", second_summary)
        self.assertEqual(second["commits"], 1)

    def test_last_session_uses_filename_date_for_legacy_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir()
            output_dir = project_root / ".codex" / "sessions"

            def git(*args: str) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            branch = git("branch", "--show-current") or "master"
            (project_root / "base.txt").write_text("base\n", encoding="utf-8")
            git("add", "base.txt")
            git("commit", "--quiet", "-m", "chore: initialize")
            head = git("rev-parse", "--short", "HEAD")

            output_dir.mkdir(parents=True)
            legacy_summary = output_dir / "2001-01-01.md"
            legacy_summary.write_text(
                "# Legacy summary without a checkpoint timestamp\n\n"
                f"## Overview\n- Branch: {branch}\n- HEAD: {head}\n\n"
                "## Task State\n- Goal: Verify the legacy cutoff\n- Status: in_progress\n\n"
                "## Completed\n- None\n\n## In Progress\n- None\n\n"
                "## Blocked\n- None\n\n## Commands Verified\n- None\n\n"
                "## Next Steps\n- None\n\n## Open Questions\n- None\n",
                encoding="utf-8",
            )
            edited_mtime = datetime.now().timestamp() + 86400
            os.utime(legacy_summary, (edited_mtime, edited_mtime))

            (project_root / "followup.txt").write_text("follow-up\n", encoding="utf-8")
            git("add", "followup.txt")
            git("commit", "--quiet", "-m", "fix: after legacy checkpoint")
            result = run_summary_cli(project_root, "last-session", output_dir)
            summary = Path(str(result["path"])).read_text(encoding="utf-8")

        self.assertIn("fix: after legacy checkpoint", summary)
        self.assertEqual(result["commits"], 1)

    def test_last_session_scopes_checkpoints_to_current_branch_and_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            git_root = Path(temporary) / "repo"
            output_dir = git_root / ".codex" / "sessions"
            git_root.mkdir()

            def git(*args: str) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=git_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            (git_root / "base.txt").write_text("base\n", encoding="utf-8")
            git("add", "base.txt")
            git("commit", "--quiet", "-m", "chore: base")
            git("branch", "-M", "main")
            ancestor_head = git("rev-parse", "HEAD")
            (git_root / "main.txt").write_text("main descendant\n", encoding="utf-8")
            git("add", "main.txt")
            git("commit", "--quiet", "-m", "feat: main descendant")
            current_head = git("rev-parse", "HEAD")
            git("checkout", "--quiet", "--detach", ancestor_head)
            (git_root / "sibling.txt").write_text("unrelated sibling\n", encoding="utf-8")
            git("add", "sibling.txt")
            git("commit", "--quiet", "-m", "feat: sibling")
            diverged_head = git("rev-parse", "HEAD")
            git("checkout", "--quiet", "main")

            output_dir.mkdir(parents=True)
            checkpoint_a = (datetime.now().astimezone() - timedelta(days=4)).replace(microsecond=0)
            checkpoint_b = (datetime.now().astimezone() - timedelta(days=3)).replace(microsecond=0)
            checkpoint_diverged = (datetime.now().astimezone() - timedelta(days=2)).replace(microsecond=0)
            checkpoint_other_repo = (datetime.now().astimezone() - timedelta(days=1)).replace(microsecond=0)

            def complete_summary(branch: str, created: datetime, head: str) -> str:
                return (
                    "# Session Summary\n\n## Overview\n"
                    f"- Checkpoint created: {created.isoformat(timespec='seconds')}\n"
                    f"- Branch: {branch}\n"
                    f"- Git root: {git_root}\n\n"
                    f"- HEAD: {head}\n\n"
                    "## Task State\n- Goal: Preserve branch history\n- Status: completed\n\n"
                    "## Completed\n- Done\n\n## In Progress\n- None\n\n"
                    "## Blocked\n- None\n\n## Commands Verified\n- None\n\n"
                    "## Next Steps\n- None\n\n## Open Questions\n- None\n"
                )

            (output_dir / f"{checkpoint_a.date().isoformat()}.md").write_text(
                complete_summary("main", checkpoint_a, ancestor_head), encoding="utf-8"
            )
            (output_dir / f"{checkpoint_b.date().isoformat()}.md").write_text(
                complete_summary("feature", checkpoint_b, current_head), encoding="utf-8"
            )
            (output_dir / f"{checkpoint_diverged.date().isoformat()}.md").write_text(
                complete_summary("main", checkpoint_diverged, diverged_head), encoding="utf-8"
            )
            other_repo = Path(temporary) / "another-repo"
            (output_dir / f"{checkpoint_other_repo.date().isoformat()}.md").write_text(
                complete_summary("main", checkpoint_other_repo, ancestor_head).replace(
                    str(git_root), str(other_repo)
                ),
                encoding="utf-8",
            )

            resolved, _, since_head = generate_session_summary.resolve_since_datetime(
                "last-session", output_dir, branch="main", git_root=git_root, head=current_head
            )
            self.assertEqual(resolved, checkpoint_a)
            self.assertEqual(since_head, ancestor_head)

    def test_last_session_rejects_an_incomplete_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir()
            output_dir = Path(temporary) / "summaries"
            subprocess.run(["git", "init", "--quiet"], cwd=project_root, check=True)
            subprocess.run(["git", "config", "user.name", "Session Summary Test"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "session-summary@example.test"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=project_root, check=True)
            (project_root / "base.txt").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "base.txt"], cwd=project_root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "chore: initialize"], cwd=project_root, check=True)

            run_summary_cli(project_root, "2000-01-01", output_dir)
            summary_path = next(output_dir.glob("*.md"))
            summary_path.write_text(
                summary_path.read_text(encoding="utf-8").replace(
                    "- Checkpoint created: ", "- Original checkpoint: "
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "Latest session checkpoint is incomplete"):
                run_summary_cli(project_root, "last-session", output_dir)

    def test_last_session_scopes_detached_head_checkpoints_by_ancestry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "repo"
            project_root.mkdir()
            output_dir = project_root / ".codex" / "sessions"

            def git(*args: str) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            (project_root / "base.txt").write_text("base\n", encoding="utf-8")
            git("add", "base.txt")
            git("commit", "--quiet", "-m", "chore: base")
            base_head = git("rev-parse", "HEAD")

            (project_root / "main.txt").write_text("main descendant\n", encoding="utf-8")
            git("add", "main.txt")
            git("commit", "--quiet", "-m", "feat: main descendant")
            current_head = git("rev-parse", "HEAD")

            git("checkout", "--quiet", "--detach", base_head)
            (project_root / "sibling.txt").write_text("sibling commit\n", encoding="utf-8")
            git("add", "sibling.txt")
            git("commit", "--quiet", "-m", "feat: sibling detached history")
            sibling_head = git("rev-parse", "HEAD")
            git("checkout", "--quiet", "--detach", current_head)

            output_dir.mkdir(parents=True)
            checkpoint_ancestor = (datetime.now().astimezone() - timedelta(days=2)).replace(microsecond=0)
            checkpoint_sibling = (datetime.now().astimezone() - timedelta(days=1)).replace(microsecond=0)

            def detached_summary(created: datetime, head: str) -> str:
                return (
                    "# Session Summary\n\n## Overview\n"
                    f"- Checkpoint created: {created.isoformat(timespec='seconds')}\n"
                    "- Branch: detached HEAD\n"
                    f"- Git root: {project_root}\n"
                    f"- HEAD: {head}\n\n"
                    "## Task State\n- Goal: Preserve detached history\n- Status: completed\n\n"
                    "## Completed\n- Done\n\n## In Progress\n- None\n\n"
                    "## Blocked\n- None\n\n## Commands Verified\n- None\n\n"
                    "## Next Steps\n- None\n\n## Open Questions\n- None\n"
                )

            (output_dir / f"{checkpoint_ancestor.date().isoformat()}.md").write_text(
                detached_summary(checkpoint_ancestor, base_head), encoding="utf-8"
            )
            (output_dir / f"{checkpoint_sibling.date().isoformat()}.md").write_text(
                detached_summary(checkpoint_sibling, sibling_head), encoding="utf-8"
            )

            resolved, _, since_head = generate_session_summary.resolve_since_datetime(
                "last-session",
                output_dir,
                branch="detached HEAD",
                git_root=project_root,
                head=current_head,
            )

        self.assertEqual(resolved, checkpoint_ancestor)
        self.assertEqual(since_head, base_head)

    def test_last_session_uses_head_range_for_old_dated_descendant_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_root = Path(temporary) / "project"
            project_root.mkdir()
            output_dir = Path(temporary) / "summaries"

            def git(*args: str, env: dict[str, str] | None = None) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=project_root,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return completed.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "Session Summary Test")
            git("config", "user.email", "session-summary@example.test")
            git("config", "commit.gpgsign", "false")
            base_date = "1990-01-01T00:00:00+00:00"
            (project_root / "base.txt").write_text("base\n", encoding="utf-8")
            git("add", "base.txt")
            git(
                "commit",
                "--quiet",
                "-m",
                "chore: initialize",
                env={**os.environ, "GIT_AUTHOR_DATE": base_date, "GIT_COMMITTER_DATE": base_date},
            )

            first = run_summary_cli(project_root, "2000-01-01", output_dir)
            checkpoint_path = Path(str(first["path"]))
            complete_generated_checkpoint(checkpoint_path)
            old_date = "2001-01-01T00:00:00+00:00"
            (project_root / "rebased.txt").write_text("descendant with preserved old date\n", encoding="utf-8")
            git("add", "rebased.txt")
            git(
                "commit",
                "--quiet",
                "-m",
                "fix: old-dated descendant",
                env={**os.environ, "GIT_AUTHOR_DATE": old_date, "GIT_COMMITTER_DATE": old_date},
            )

            result = run_summary_cli(project_root, "last-session", output_dir)
            summary = Path(str(result["path"])).read_text(encoding="utf-8")

        self.assertIn("fix: old-dated descendant", summary)
        self.assertEqual(result["commits"], 1)
        self.assertEqual(result["history_range"], f"{first['head']}..HEAD")

    def test_legacy_summary_with_generic_todo_is_incomplete(self) -> None:
        complete_legacy = (
            "## Task State\n- Goal: Verify resume state\n- Status: completed\n\n"
            "## Completed\n- Done\n\n## In Progress\n- None\n\n"
            "## Blocked\n- None\n\n## Commands Verified\n- None\n\n"
            "## Next Steps\n- TODO\n\n## Open Questions\n- None\n"
        )
        for placeholder in ("TODO", ""):
            with self.subTest(placeholder=placeholder):
                content = complete_legacy.replace("- TODO", f"- {placeholder}")
                self.assertTrue(generate_session_summary.summary_is_incomplete(content))

    def test_summary_output_paths_are_reserved_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "summaries"
            output_dir.mkdir()
            with ThreadPoolExecutor(max_workers=12) as executor:
                paths = list(executor.map(lambda _: generate_session_summary.next_output_file(output_dir), range(24)))

        self.assertEqual(len(paths), len(set(paths)))


if __name__ == "__main__":
    unittest.main()

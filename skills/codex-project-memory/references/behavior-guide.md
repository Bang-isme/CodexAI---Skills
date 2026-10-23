# Behavior Guide

## Behavior

### Decision Logger

1. Collect decision details:
   - `title`
   - `decision`
   - `alternatives`
   - `reasoning`
   - `context`
2. Run `scripts/decision_logger.py` to persist the record under project `.codex/decisions/`.
3. Return created file path and confirmation summary.
4. Before making similar decisions, review existing files in `.codex/decisions/`.

### Context Handoff Generator

1. Trigger when user needs portable project context for another AI or teammate.
2. Run `scripts/generate_handoff.py`.
3. Default output: `<project-root>/.codex/handoff.md`.
4. Return output path, section count, and file size from script JSON.

### Session Summary Generator

1. Trigger when the user requests an end-of-session summary, or before pausing multi-step work for context compaction or handoff.
2. Run `scripts/generate_session_summary.py`. Use `--since last-session` for a follow-up checkpoint when the newest summary is complete. For the first checkpoint of work that began before today, pass the task's actual start time as an ISO datetime so earlier commits are included.
3. Default output directory: `<project-root>/.codex/sessions/`.
4. Read the generated Markdown. It records the checkpoint time, Git root, branch, HEAD, recent commit subjects, and staged/unstaged/untracked paths, but not dirty-file contents, task meaning, or command results. Confirm the commit range covers the task.
5. Replace every bracketed prompt with the goal, status, completed work, exact resume point, blockers, decisions with reasons and alternatives, commands actually verified, actionable next steps, and open questions. Use `in_progress` for a resumable pause and `None` for empty sections. Expand generated decision titles using the matching `.codex/decisions/` record or current conversation; do not infer rationale from a title. Do not claim a checkpoint is ready while prompts remain.
6. Reconcile the path snapshot with `git status --short --untracked-files=all`. For paths listed as both staged and unstaged, inspect `git diff --cached -- <path>` and `git diff -- <path>` separately; inspect the contents of untracked files before describing them.
7. Each run creates a new dated summary file; it does not update the prior one. The filename is reserved exclusively so concurrent runs cannot replace each other's summaries. The generated `Checkpoint created` timestamp is immutable and stored to whole-second precision; editing task fields does not move it. When the prior checkpoint has a committed HEAD, `last-session` summarizes the exact `checkpoint HEAD..current HEAD` range, including descendants with old committer dates. If the prior checkpoint says `HEAD: unborn`, it includes all commits reachable from current HEAD. With no prior checkpoint, it uses the timestamp cutoff. The resolver scopes checkpoints to the current Git branch and repository, requires the recorded HEAD to be an ancestor of current HEAD, and refuses to use the newest matching checkpoint while its generated prompts remain. For legacy summaries without a timestamp, it uses midnight on the date in the filename for the fallback cutoff; these summaries still need matching branch identity, a valid HEAD or `unborn`, and complete task-state fields with no blank or generic TODO entries. Rootless legacy summaries are accepted only when the summary directory is inside the current repository. When summaries exist but none matches the current branch/repository/history, pass an explicit ISO `--since` value or create a checkpoint there; with no prior summaries, `last-session` falls back to today. If another task has a newer checkpoint on the same branch, find the matching task's `in_progress` summary by Goal and resume its narrative directly; `last-session` is branch-wide and does not identify a task. If the worktree changes after generation, run the generator again, carry forward the task narrative and verified commands, and complete every prompt in the new file.
8. A session summary resumes work only when the receiving agent can access the same repository state. For a different checkout, provide the recorded branch/HEAD or an authorized patch; a list of dirty paths does not transfer their contents. For a portable project handoff, also use `generate_handoff.py`.
9. Return the completed summary path plus branch, HEAD, commit, committed-file, and working-tree counts from script JSON.

### Changelog Generator

1. Trigger when user asks for release notes or changelog generation.
2. Run `scripts/generate_changelog.py`.
3. Default source range: latest tag or last 30 days.
4. Return categorized markdown output and summary JSON.

### Pattern Learner

1. Trigger when user asks to learn project coding conventions.
2. Run `scripts/analyze_patterns.py`.
3. Default output: `<project-root>/.codex/project-profile.json`.
4. Return generated profile with naming, structure, import style, and pattern detection.

### Feedback Tracker

1. Trigger when user asks to record AI-vs-user fix deltas.
2. Run `scripts/track_feedback.py` with category and fix context.
3. Persist entries under `<project-root>/.codex/feedback/`.
4. On `$feedback-summary`, run `scripts/track_feedback.py --aggregate` and return trend summary.

### Knowledge Graph Builder

1. Trigger when user asks for deep project structure mapping.
2. Run `scripts/build_knowledge_graph.py`.
3. Default output: `<project-root>/.codex/knowledge-graph.json`.
4. Before complex refactors, read `knowledge-graph.json` first to understand boundaries and dependencies.
5. Treat `code_index` as the structural source of truth for modules/imports and `codebase_index` as the richer symbol/chunk/search source.

### Knowledge Index

1. Trigger on `$knowledge`, "build knowledge index", or when a task needs durable project context.
2. Run `scripts/build_knowledge_index.py --project-root <path>`.
3. Default output directory: `<project-root>/.codex/knowledge/`.
4. Return `index_path`, `graph_path`, `codebase_index_path`, `coverage`, and `warnings`.
5. For large projects, pass traversal limits explicitly (`--max-files`, `--max-total-bytes`, `--max-file-bytes`) and report any truncation or graph/codebase file-set divergence.
6. For direct lookup, use `--query "<terms>" --top-k <n>` and return the ranked local results.

### Memory Status Validator

1. Trigger before handoff, deploy, CLI migration, or when the user asks whether project memory is reliable.
2. Run `scripts/memory_status.py --project-root <path>`; add `--strict` for CI gates that must fail on warnings; add `--require-standalone-graph` when `.codex/knowledge-graph.json` must exist and be schema v2.
3. Treat `fail` as blocking for automation; treat `warn` as usable but requiring disclosure (unless `--strict`).
4. Return `policy`, artifact paths, staleness, graph/codebase coherence, warnings, and failures.

### Project Genome Generator

1. Trigger when user asks for compressed, layered project context.
2. Run `scripts/generate_genome.py`.
3. Default output: `<project-root>/.codex/context/genome.md` and optional module maps in `.codex/context/modules/`.
4. Use `--depth auto|shallow|full` for scale-aware output and `--force` to refresh stale context.

### Chaining Guidance

1. Log major technical choices via `decision_logger.py`.
2. Generate release communication via `generate_changelog.py`.
3. Keep continuity via `generate_session_summary.py`.

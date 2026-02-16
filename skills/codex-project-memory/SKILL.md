---
name: codex-project-memory
description: Tracks project knowledge, decisions, and patterns across sessions
---

# Codex Project Memory

## Activation

1. Activate after complex tasks involving architecture, design decisions, or refactors.
2. Activate on explicit command `$log-decision`.
3. Activate on `$handoff` or when user asks to generate handoff context.
4. Activate on `$session-summary` or when user asks to summarize a coding session.
5. Activate on `$analyze-patterns` or "learn project style".
6. Activate on `$log-feedback` or "track my fix".
7. Activate on `$feedback-summary` for aggregated feedback recall.
8. Activate on `$skill-track` to record skill usage analytics.
9. Activate on `$skill-report` to generate skill evolution report.
10. Activate on `$build-graph` or "map project" to generate project knowledge graph.

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

1. Trigger when user requests end-of-session summary.
2. Run `scripts/generate_session_summary.py`.
3. Default output directory: `<project-root>/.codex/sessions/`.
4. Return output path, commit count, and changed file count from script JSON.

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

### Skill Evolution Tracker

1. Trigger when user asks to track skill performance across tasks.
2. Run `scripts/track_skill_usage.py --record` for single usage entries.
3. Run `scripts/track_skill_usage.py --report` for aggregate effectiveness analysis.
4. Use report output to identify underperforming or unused skills.

### Knowledge Graph Builder

1. Trigger when user asks for deep project structure mapping.
2. Run `scripts/build_knowledge_graph.py`.
3. Default output: `<project-root>/.codex/knowledge-graph.json`.
4. Before complex refactors, read `knowledge-graph.json` first to understand boundaries and dependencies.

## Execution Command

### Decision Logger

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`

### Context Handoff Generator

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\generate_handoff.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`

### Session Summary Generator

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\generate_session_summary.py" --project-root <path> --since today`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`

### Pattern Learner

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\analyze_patterns.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/analyze_patterns.py" --project-root <path>`

### Feedback Tracker

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- Aggregate:
  `python ".../track_feedback.py" --project-root <path> --aggregate`

### Skill Evolution Tracker

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\track_skill_usage.py" --skills-root "$env:USERPROFILE\\.codex\\skills" --record --skill <skill-name> --task <task> --outcome <success|partial|failed> --notes <text>`
- Report:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\track_skill_usage.py" --skills-root "$env:USERPROFILE\\.codex\\skills" --report`

### Knowledge Graph Builder

- Windows:
  `python "$env:USERPROFILE\\.codex\\skills\\codex-project-memory\\scripts\\build_knowledge_graph.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-project-memory/scripts/build_knowledge_graph.py" --project-root <path>`

## Output Contract

Success JSON:

```json
{
  "status": "logged",
  "path": "<project-root>/.codex/decisions/YYYY-MM-DD-<slug>.md",
  "title": "<title>"
}
```

Error JSON:

```json
{
  "status": "error",
  "path": "",
  "title": "<title>",
  "message": "<error details>"
}
```

## Reference

Read:
- `references/decision-journal-spec.md` for decision logging criteria and naming conventions.
- `references/handoff-spec.md` for handoff usage guidance.
- `references/session-summary-spec.md` for session summary workflow and retention guidance.
- `references/pattern-learner-spec.md` for project style learning behavior.
- `references/feedback-tracker-spec.md` for feedback logging and aggregate usage.
- `references/skill-evolution-spec.md` for skill usage analytics and optimization.
- `references/knowledge-graph-spec.md` for deep architecture mapping and refresh guidance.

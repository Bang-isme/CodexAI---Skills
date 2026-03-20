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

1. Trigger when user requests end-of-session summary.
2. Run `scripts/generate_session_summary.py`.
3. Default output directory: `<project-root>/.codex/sessions/`.
4. Return output path, commit count, and changed file count from script JSON.

### Changelog Generator

1. Trigger when user asks for release notes or changelog generation.
2. Run `scripts/generate_changelog.py`.
3. Default source range: latest tag or last 30 days.
4. Return categorized markdown output and summary JSON.

### Growth Report Generator

1. Trigger when user asks for learning trends or improvement planning.
2. Run `scripts/generate_growth_report.py`.
3. Aggregate feedback, sessions, and usage analytics.
4. Return report path and prioritized improvement areas.

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

### Project Genome Generator

1. Trigger when user asks for compressed, layered project context.
2. Run `scripts/generate_genome.py`.
3. Default output: `<project-root>/.codex/context/genome.md` and optional module maps in `.codex/context/modules/`.
4. Use `--depth auto|shallow|full` for scale-aware output and `--force` to refresh stale context.

### Chaining Guidance

1. Log major technical choices via `decision_logger.py`.
2. Generate release communication via `generate_changelog.py`.
3. Keep continuity via `generate_session_summary.py`.
4. Track long-term improvement via `generate_growth_report.py`.

# Script Commands

Canonical command paths are centralized in `skills/.system/REGISTRY.md`.

## Execution Command

### Decision Logger

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/decision_logger.py" --project-root <path> --title <slug> --decision <text> --alternatives <text> --reasoning <text> --context <text>`

### Context Handoff Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_handoff.py" --project-root <path>`

### Session Summary Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_session_summary.py" --project-root <path> --since today`

### Changelog Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_changelog.py" --project-root <path> --since "30 days ago"`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_changelog.py" --project-root <path> --since "30 days ago"`

### Growth Report Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_growth_report.py" --project-root <path> --skills-root "<SKILLS_ROOT>"`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_growth_report.py" --project-root <path> --skills-root "<SKILLS_ROOT>"`

### Pattern Learner

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/analyze_patterns.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/analyze_patterns.py" --project-root <path>`

### Feedback Tracker

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_feedback.py" --project-root <path> --file <file> --ai-version <text> --user-fix <text> --category <category>`
- Aggregate:
  `python ".../track_feedback.py" --project-root <path> --aggregate`

### Skill Evolution Tracker

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_skill_usage.py" --skills-root "<SKILLS_ROOT>" --record --skill <skill-name> --task <task> --outcome <success|partial|failed> --notes <text>`
- Report:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/track_skill_usage.py" --skills-root "<SKILLS_ROOT>" --report`

### Knowledge Graph Builder

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_graph.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/build_knowledge_graph.py" --project-root <path>`

### Project Genome Generator

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_genome.py" --project-root <path>`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/generate_genome.py" --project-root <path>`
- Options:
  `--depth auto|shallow|full` (default: auto), `--force` to regenerate
- Output:
  JSON summary + `.codex/context/genome.md` and optional `.codex/context/modules/*.md`

### auto_commit.py

- **Skill**: `codex-git-autopilot`
- **Purpose**: Automated commit with CI gate + GPG signing
- **Command**: `python auto_commit.py --project-root <dir> --files <file1> <file2>`
- **Options**: `--dry-run`, `--skip-tests`, `--no-push`, `--setup-gpg`, `--message`, `--type`, `--scope`
- **Output**: JSON with commit hash, push status, GPG status

### Context Compactor

- Windows:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/compact_context.py" --project-root <path> --max-age-days 90 --keep-latest 5`
- macOS/Linux:
  `python "<SKILLS_ROOT>/codex-project-memory/scripts/compact_context.py" --project-root <path> --max-age-days 90 --keep-latest 5`
- Dry run:
  `python ".../compact_context.py" --project-root <path> --dry-run`

# Script Commands

Canonical command paths are centralized in `skills/.system/REGISTRY.md`.

## Script Paths

- Windows:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\<script>.py" --project-root <path>`
- macOS/Linux:
  `python "$HOME/.codex/skills/codex-execution-quality-gate/scripts/<script>.py" --project-root <path>`

### Environment Doctor Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\doctor.py" --skills-root "$env:USERPROFILE\.codex\skills" --format json`
- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\doctor.py" --format table`

### Tech Debt Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\tech_debt_scan.py" --project-root <path>`

### Auto Gate Command

- Quick:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\auto_gate.py" --project-root <path> --mode quick`
- Full:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\auto_gate.py" --project-root <path> --mode full`
- Deploy:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\auto_gate.py" --project-root <path> --mode deploy`
- Optional human summary:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\auto_gate.py" --project-root <path> --mode quick --human`

### Pre-Commit Intelligence Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root <path>`

### Install Hooks Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_hooks.py" --project-root <path>`
- Heavier local enforcement:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_hooks.py" --project-root <path> --with-lint-test`
- Preview without writing:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_hooks.py" --project-root <path> --dry-run`
- Remove managed hook block:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_hooks.py" --project-root <path> --uninstall`

### Install CI Gate Command

- GitHub Actions:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_ci_gate.py" --project-root <path> --ci github`
- GitLab CI:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\install_ci_gate.py" --project-root <path> --ci gitlab`

### Smart Test Selector Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\smart_test_selector.py" --project-root <path> --source staged`

### Improvement Suggester Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\suggest_improvements.py" --project-root <path> --source last-commit`
- In proactive mode, run after complex tasks and present top 3 suggestions.

### Output Guard Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\output_guard.py" --file <path/to/deliverable.md>`
- Inline text:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\output_guard.py" --text "..." --format table`
- Repo-aware grounding check:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\output_guard.py" --file <path/to/deliverable.md> --repo-root <project-root>`
- Opt-in LLM judge:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\output_guard.py" --text "Deploy by running npm run build && npm run start on port 3000." --llm-judge --model gpt-4o-mini --max-tokens 500 --format json`

### Editorial Review Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\editorial_review.py" --file <path/to/deliverable.md>`
- Inline text:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\editorial_review.py" --text "Decision: ..."`
- Repo-aware editorial pass:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\editorial_review.py" --file <path/to/deliverable.md> --repo-root <project-root> --deliverable-kind review`
- Opt-in LLM judge:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\editorial_review.py" --text "Decision: ship the current checklist." --deliverable-kind handoff --llm-judge --model gpt-4o-mini --max-tokens 500 --format json`

### Strict Output Gate Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root <path> --strict-output --output-file <deliverable.md>`
- Inline text:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root <path> --skip-lint --skip-test --strict-output --output-text "Decision: ..."`
- Auto-strict defaults:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root <path> --output-file implementation-plan.md`
- Downgrade intentionally:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root <path> --output-file handoff.md --advisory-output`

### Impact Predictor Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\predict_impact.py" --project-root <path> --files <file1,file2> --depth 2`

### Quality Trend Commands

- Record:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\quality_trend.py" --project-root <path> --record`
- Report:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\quality_trend.py" --project-root <path> --report --days 30`
- Gate-aware report:
  gate runs now feed `.codex/quality/gate-events.jsonl`, so reports can include gate pass rate, average output quality, and average editorial quality.

### UX Audit Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\ux_audit.py" --project-root <path>`

### Accessibility Check Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\accessibility_check.py" --project-root <path> --level AA`

### Lighthouse Audit Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\lighthouse_audit.py" --url <http://localhost:3000> --device mobile --runs 1`
- Requires a running URL and Lighthouse availability through `npx`.

### Playwright Runner Commands

- Check setup:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\playwright_runner.py" --project-root <path> --mode check`
- Generate skeleton:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\playwright_runner.py" --project-root <path> --mode generate --url <http://localhost:3000/page>`
- Run tests:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\playwright_runner.py" --project-root <path> --mode run --browser chromium`

### Server Lifecycle Helper Command

- `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\with_server.py" --help`
- Example:
  `python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\with_server.py" --server "npm run dev" --port 3000 -- python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\lighthouse_audit.py" --url http://localhost:3000`

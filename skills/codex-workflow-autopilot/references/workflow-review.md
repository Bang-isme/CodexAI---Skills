# Workflow: Review

Use this workflow for technical review, risk assessment, and codebase quality evaluation. Follow the **4-Part Finding Contract** in `../../codex-domain-specialist/references/code-review.md`.

## Steps

1. Run `tech_debt_scan.py` and `shortcut_ledger.py` for structural debt and documented `shortcut:` ceilings.
2. Run `quality_trend.py --report` and `security_scan.py` for historical quality direction and security exposure.
3. Inspect the changed code AND grep its callers (`Caller-Grep Rule`) across functional, security, and maintainability dimensions.
4. Structure the review report using the **4-Part Finding Contract**:
   - Priority order: `Correct -> Safe -> Holds at expected load -> Tested -> Fast -> Lean`.
   - Declare `Assumed Load: <number>` and `Not Checked / Out of Scope`.
   - Group findings into `Must-Fix`, `Should-Fix`, and `Nice-to-Have` (omit empty groups; number continuously `1..N`).
   - Provide all 4 parts for every finding: `What it is (file:line)`, `The problem (concrete failing input/case)`, `The smallest fix`, and `What happens if skipped`.
   - Exclude `shortcut: <ceiling>, <when to upgrade>` markers whose ceiling exceeds `Assumed Load`.
5. Validate the written review with `finding_contract.py`, `output_guard.py`, and `editorial_review.py` (or `run_gate.py --deliverable-kind review --output-file <review.md>`).

## Exit Criteria

- Findings are numbered continuously across `Must-Fix`, `Should-Fix`, and `Nice-to-Have` with a concrete trigger case for each.
- `finding_contract.py` passes with 0 contract errors and 0 fabricated savings claims.
- Immediate `Must-Fix` blockers are clearly separated from `Should-Fix` and `Nice-to-Have` items.

## Example Sequence

1. Run technical debt and shortcut ledger scans:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/tech_debt_scan.py" --project-root .`
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/shortcut_ledger.py" --project-root .`
2. Run security scan and trend report:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/security_scan.py" --project-root .`
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/quality_trend.py" --project-root . --report --days 30`
3. Draft the review report following `code-review.md` (`Must-Fix` / `Should-Fix` / `Nice-to-Have`, 4 parts per finding, `Assumed Load`, `Not Checked / Out of Scope`).
4. Validate the review report contract:
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/finding_contract.py" --file review.md --format json`
   `python "<SKILLS_ROOT>/codex-execution-quality-gate/scripts/run_gate.py" --project-root . --deliverable-kind review --output-file review.md`

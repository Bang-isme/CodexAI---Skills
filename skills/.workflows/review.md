---
name: review
trigger: $review
loads: [codex-workflow-autopilot, codex-execution-quality-gate, codex-reasoning-rigor]
---

# Workflow Alias: $review

## Trigger

Use for audits, code reviews, technical risk assessment, or release-readiness inspection.

## Step Outline

1. Load `workflow-review.md` and `../codex-domain-specialist/references/code-review.md`.
2. Gather structural debt, shortcut ledger (`shortcut_ledger.py`), quality trend, and security signals (`security_scan.py`).
3. Inspect both the diff and all upstream/downstream callers (`Caller-Grep Rule`). For UI, require independent visual review with desktop and mobile evidence, or disclose `DEGRADED`.
4. Author findings strictly under the **4-Part Finding Contract** (`Priority: Correct -> Safe -> Holds at expected load -> Tested -> Fast -> Lean`):
   - State `Assumed Load: <number>` and `Not Checked / Out of Scope: <items>`.
   - Group findings under `### Must-Fix`, `### Should-Fix`, and `### Nice-to-Have` (omit empty groups; number findings continuously across groups).
   - Include all 4 required parts per finding: `What it is (file:line)`, `The problem (concrete failing input/case)`, `The smallest fix`, and `What happens if skipped`.
   - Treat documented `shortcut: <ceiling>, <when to upgrade>` comments below `Assumed Load` as accepted decisions, not findings.
5. Validate the written review with `finding_contract.py`, `output_guard.py`, and `editorial_review.py` (or `run_gate.py --deliverable-kind review --output-file <review.md>`).

## Exit Criteria

- Every reported finding has a concrete failing input/scenario and all 4 contract parts.
- `finding_contract.py` and `shortcut_ledger.py` checks pass with zero contract violations or fabricated savings claims.
- The written review passes `output_guard` and `editorial_review`.

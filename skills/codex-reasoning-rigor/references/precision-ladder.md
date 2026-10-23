# 6-Rung Smallest-Complete-Change Decision Ladder

Use this ladder before adding code. Stop at the first rung that fully solves the task, including the edge cases that rung claims to handle. A shorter change that fails on a real input is not complete.

## The Ladder

1. **Does it need to exist?** A vague "build X" gets the smallest working core, not a new platform, framework, or configuration surface.
2. **Reuse an existing helper in this repository** the way surrounding code already uses it. Search shared folders such as `utils`, `lib`, `shared`, `common`, `helpers`, and `services` before writing a second copy.
3. **Standard library or platform/browser native feature**, unless the project already has a house component for that job.
4. **Already-installed dependency.** Never add a new package for a few lines of logic.
5. **One readable line.** Prefer one obvious line over a new abstraction when that line is the whole behavior.
6. **Minimum complete code that works on edge cases.** This is the floor when a one-liner is wrong on empty input, boundaries, a second caller, or a hostile value.

## Caller-Grep Rule

Before fixing a bug or changing a signature, grep every caller and fix the shared function once. A guard that lives only in one caller is still broken when the second caller runs. Moved code keeps its validation; do not drop the check during the move and plan to add it back later.

## Shortcut Marker Contract

A deliberate ceiling is a comment, not an unlabeled guess. Put it in a real code comment (`#`, `//`, or `/* */`):

```python
# shortcut: 1000 rows, when the table exceeds 1000 rows
```

```javascript
// shortcut: 100 requests/minute, when one key exceeds 100 requests per minute
```

```c
/* shortcut: 50 items, when the batch grows past 50 items */
```

The shape is `shortcut: <ceiling>, <when to upgrade>`. A marker without the upgrade trigger is unfinished and is tagged `no-trigger`. Reviewers treat a complete marker as a documented decision, not a finding, unless **Assumed Load** exceeds `<ceiling>`.

## Never-Cut Carve-Outs

Do not "simplify away" any of these, even when an earlier rung looks smaller:

- trust-boundary validation
- error handling that prevents data loss
- security controls
- accessibility
- hardware or sensor calibration
- explanations the user explicitly asked for

These carve-outs force a later rung when a smaller one would delete them.

## Session Mode State Machine

Intensities: `off`, `lite`, `full`, `ultra`.

| Intensity | What is in force |
| --- | --- |
| off | No extra precision rules are latched |
| lite | Smallest complete change and the ladder |
| full | Ladder, caller-grep, shortcut contract, and never-cut carve-outs |
| ultra | Full, plus the edge case and the verification command |

Resolution order:

1. Explicit environment variable `CODEX_PRECISION_MODE`
2. Project config JSON (a leading UTF-8 BOM is stripped before parse; writes merge and keep unrelated keys)
3. Default `full`

`review`, `audit`, `debt`, and `help` are one-shot commands. They are rejected as default levels and must not overwrite the latched intensity.

Session state is stored per project. The file key is the SHA-256 of the normalized path. Normalization does not rewrite `\` into `/`, so distinct paths never share a state file. `source == "compact"` keeps the live level. A fresh start uses the resolved default.

Prompt commands, after trim and after ignoring only trailing `.!?;,`:

- Bare `on` reports the current level when it is already active. From `off`, it activates the default, or `full` when the default is `off`.
- `off`, `stop`, and `normal mode` deactivate only when the whole message is that command. A longer sentence that mentions those words does not deactivate.
- `lite`, `full`, and `ultra` set that level when the whole message is that word.
- Any other sentence leaves the level unchanged.
- `$review`, `$audit`, `$debt`, and `$help` do not latch.

Instruction text is filtered for the active level: table rows and examples for other levels drop, while rule bullets stay even when their label is a level word such as `lite` or `off`. The same ruleset is not appended again on the next turn unless the level changed or the context was compacted.

```text
off --on / set--> lite | full | ultra
lite | full | ultra --off | stop | normal mode--> off
any --$review | $audit | $debt | $help--> same level
compact --> keep live level
fresh --> resolved default
```

## Rule Shape The Filter Expects

```markdown
- lite: keep the change on the smallest rung that still works
- full: apply the ladder, caller-grep, and never-cut carve-outs
- ultra: name the edge case and the verification command
- off: do not inject extra precision rules

| level | behavior |
| --- | --- |
| lite | smallest complete change |
| full | ladder plus caller-grep |
| ultra | edge cases and verification |
| off | no extra rules |

### Example: lite
Ship the smallest working core.

### Example: full
Reuse the existing helper and cover the failing input.
```

## Scripts

- `skills/codex-runtime-hook/scripts/precision_mode.py` resolves the level, stores per-project session state, and filters instructions.
- `skills/codex-runtime-hook/scripts/reuse_map.py` builds the sanitized helper index used by rung 2.
- `skills/codex-execution-quality-gate/scripts/shortcut_ledger.py` lists shortcut comments and tags a missing upgrade trigger as `no-trigger`.

# Scope Escalation

## Complexity-To-Scope Mapping

| Intent Analyzer Output | Workflow Autopilot Scope | Plan Writer Trigger | Action |
| --- | --- | --- | --- |
| `complexity: simple` | `estimated_scope: small` | Skip plan (direct execution) | Standard |
| `complexity: complex` + <=10 files | `estimated_scope: medium` | Plan recommended | Standard |
| `complexity: complex` + >10 files | `estimated_scope: large` | Plan mandatory | Staged execution |
| Blast Radius > 20 files | `estimated_scope: epic` | **HALT** | Epic Mode |

## Epic Mode

When `predict_impact.py` returns `escalate_to_epic: true`:

1. Refuse to write implementation code in the current session.
2. Generate a Master Plan document breaking the epic into 3-5 isolated tickets.
3. Each ticket must have:
   - a clear file boundary
   - independent acceptance criteria
   - estimated blast radius <= 15 files
4. Ask the user to approve the Master Plan.
5. Instruct the user to open a fresh session for each ticket to preserve context window.

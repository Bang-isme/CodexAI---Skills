---
name: codex-domain-specialist
description: Apply domain-specific engineering rules for frontend, backend, mobile, debugging, and security based on project signals and files being edited. Use to route specialized decisions without separate agents.
---

# Domain Specialist

## Activation

1. Activate when the task edits domain-specific files.
2. Activate on explicit `$codex-domain-specialist`.

## Domain Detection

| Signal | Domain | Reference |
| --- | --- | --- |
| `.tsx`, `.jsx`, `.vue`, `.svelte`, `components/`, `pages/` | frontend | `references/frontend-rules.md` |
| `routes/`, `controllers/`, `services/`, `api/`, `server/` | backend | `references/backend-rules.md` |
| React Native, Flutter, Expo, `.swift`, `.kt` | mobile | `references/mobile-rules.md` |
| user reports error/bug/not working | debug | `references/debugging-rules.md` |
| auth, crypto, secrets, `.env`, validation | security | `references/security-rules.md` |

## Usage Rules

1. Detect relevant domain(s).
2. Read only the needed reference file(s), not all references.
3. Apply those rules while implementing or reviewing.
4. If task crosses domains, load each required reference and reconcile constraints.

## Cross-Domain Requirements

- Backend changes that affect API contracts require frontend checks.
- Debug flows must consider security implications.
- New features require tests in the affected domain.

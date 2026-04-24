---
name: codex-role-docs
description: Initialize, update, index, and check role-scoped project documentation under .codex/project-docs to preserve micro-context across long-running projects.
load_priority: on-demand
---

## TL;DR
Use this skill when a project needs durable FE/BE/DevOps/Admin/QA context. Generate `.codex/project-docs/` once, then keep role docs updated as code changes.

# Codex Role Docs

## Activation

1. Activate on `$role-docs`, `$init-docs`, or `$check-docs`.
2. Activate when the user asks for project docs, role docs, technical documentation, architecture notes, API docs, UI/UX docs, runbooks, or durable context.
3. Activate during long-running projects where micro-context can be lost across sessions.
4. Auto-use with agent personas when a role-owned file changes.

## Core Rule

Role docs are project-local artifacts, not always-loaded context. Read only the role docs needed for the current task, then update the same docs before completion when code behavior, contracts, architecture, UI patterns, deployment, admin flows, or tests changed.

## Commands

- Initialize docs: `init_role_docs.py --project-root <path>`
- Update one doc: `update_role_docs.py --project-root <path> --role <role> --doc <doc-id> --summary <text> --files <csv>`
- Check impact: `check_role_docs.py --project-root <path> --changed-files <csv>`
- Rebuild index: `build_role_docs_index.py --project-root <path>`
- See `skills/.system/REGISTRY.md` for full script paths.

## Role Ownership

| Role | Owns |
| --- | --- |
| `frontend-specialist` | `frontend/FE-*`, admin UI flows, dashboards, reports |
| `backend-specialist` | `backend/BE-*`, admin permissions, contracts, data management |
| `devops-engineer` | `devops/DO-*` |
| `test-engineer` | `qa/QA-*` |
| `security-auditor` | auth/security, permissions, audit-log docs |
| `planner` | project brief, ADR template, admin scope |

## Update Discipline

1. Before editing, check whether relevant docs exist under `.codex/project-docs/`.
2. If missing and the task is project setup or planning, run `$init-docs`.
3. After code changes, run `$check-docs` or map changed files manually.
4. Update only the docs owned by the active agent's role.
5. Keep entries factual: decision, source files, constraints, risks, verification.
6. Do not block completion only because docs are missing unless the user explicitly made docs mandatory.

## Generated Structure

- `PROJECT-BRIEF.md`
- `index.json`
- `decisions/ADR-0001-template.md`
- `frontend/FE-*.md`
- `backend/BE-*.md`
- `devops/DO-*.md`
- `admin/AD-*.md`
- `qa/QA-*.md`

## Resources

- `templates/role_docs_manifest.json`: canonical role docs, owners, and doc metadata.
- `templates/project-brief-template.md`: project-level context template.
- `templates/role-doc-template.md`: shared role-document template.
- `templates/adr-template.md`: decision record template.

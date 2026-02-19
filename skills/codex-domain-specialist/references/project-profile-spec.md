# Project Profile
## Purpose
Allow projects to declare their tech stack and primary domain in a single YAML file, eliminating per-session auto-detection overhead.
## File Location
`.codex/profile.yaml` in the project root.
## Schema
```yaml
name: <project-name>
stack: [<tech1>, <tech2>, ...]          # e.g. [node, express, mongodb, react]
primary_domain: <domain>                 # frontend | backend | fullstack | mobile | devops
test_framework: <framework>              # jest | pytest | vitest | none
deploy_target: <target>                  # vercel | cloudflare | docker | manual | none
custom_references: []                    # optional extra reference files to always load
```
## How AI Uses It
1. At session start, check if `<project-root>/.codex/profile.yaml` exists.
2. If exists: parse YAML -> map `primary_domain` to routing table -> load references directly.
3. If `stack` array contains known signals (for example `react` -> React/Frontend, `express` -> Backend API), use those for supplemental reference loading.
4. If not exists: fall back to current file-extension-based auto-detection.
## Validation Rules
- `primary_domain` must be one of: `frontend`, `backend`, `fullstack`, `mobile`, `devops`.
- `stack` is a flat list of lowercase strings.
- Unknown stack items are ignored silently.
- File is optional. Missing file = no error.
## Integration Behavior
- Read-only. AI never modifies this file.
- User creates/edits manually or via `$init-profile` trigger.
- Profile takes priority over auto-detection when present.

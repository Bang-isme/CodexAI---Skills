# Monorepo Patterns

## Scope
Use when managing multiple apps/packages in one repository.

## Monorepo vs Multi-Repo

| Use Monorepo | Use Multi-Repo |
| --- | --- |
| Shared code between apps | Independent projects |
| Coordinated releases | Separate release cadence |
| Unified CI/CD and tooling | Different stacks and ownership |
| Small to medium teams | Large distributed org |

## Turborepo Setup

```bash
npx create-turbo@latest my-monorepo
```

```text
my-monorepo/
  apps/
    web/
    api/
    admin/
  packages/
    ui/
    utils/
    config/
    types/
  turbo.json
  package.json
  pnpm-workspace.yaml
```

## turbo.json

```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", ".next/**"] },
    "dev": { "cache": false, "persistent": true },
    "lint": {},
    "test": { "dependsOn": ["build"] }
  }
}
```

## pnpm-workspace.yaml

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

## Shared Package Pattern

```json
{
  "name": "@repo/ui",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "dependencies": { "react": "^18.0.0" }
}
```

```typescript
// packages/ui/src/index.ts
export { Button } from "./Button";
export { Card } from "./Card";
export { Modal } from "./Modal";
```

## Rules
- Use `@repo/*` namespace for internal shared packages.
- Keep dependencies explicit in every package.
- Use `turbo run build` to respect dependency graph.
- In CI, filter changed packages where possible.
- Keep shared packages focused and stable.

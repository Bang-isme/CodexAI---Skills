# File Structure

## Scope and Triggers

Use when organizing project directories, defining module boundaries, naming conventions, and import topology.

## Core Principles

- Structure should reflect business domains and ownership.
- Keep boundaries explicit and enforceable.
- Prefer predictable conventions over custom per-feature layouts.
- Optimize for onboarding and safe change velocity.

## Common Structure Styles

### Feature-Based Structure

Best for product teams with domain ownership.

```text
src/
  features/
    auth/
      api/
      components/
      hooks/
      tests/
    billing/
    reporting/
```

Pros:
- strong locality
- easier parallel work

Tradeoff:
- potential duplication of generic utilities if governance is weak

### Layer-Based Structure

Best for smaller apps with limited domain complexity.

```text
src/
  controllers/
  services/
  repositories/
  models/
```

Pros:
- simple and familiar

Tradeoff:
- features spread across folders as app scales

### Hybrid (Recommended for medium-large)

- top-level by feature/domain
- inner layering inside each feature

## Monorepo Patterns

### Package Layout

```text
apps/
  web/
  api/
packages/
  ui/
  config/
  utils/
  types/
```

Rules:
- each package has explicit public API
- no hidden cross-package deep imports
- shared tooling config centralized

## Naming Conventions

### Files

- components: `PascalCase.jsx` or `kebab-case.tsx` (project-wide consistency required)
- hooks: `useXxx.ts`
- services: `xxx.service.ts`
- tests: `*.test.ts` or `*.spec.ts`

### Folders

- use lowercase and hyphen or domain names
- avoid ambiguous folders like `misc`, `helpers` without clear criteria

## Import Alias Strategy

Use aliases to avoid fragile relative chains.

Examples:
- `@/features/auth/...`
- `@shared/ui/...`
- `@server/services/...`

Rules:
- map aliases in tsconfig, bundler, and test runner consistently
- do not alias everything; keep intent readable

## Barrel Files

### Use With Discipline

Good:
- package-level exports (`index.ts`) for stable API surface

Avoid:
- deep barrels that create accidental circular deps
- wildcard re-exports with unclear ownership

## Boundary Enforcement

- feature can import shared, not peer internals directly
- UI layer cannot import repository/DB layer directly
- lint rules for restricted imports recommended

## Example Restriction Matrix

| From | Allowed | Blocked |
| --- | --- | --- |
| `features/*/ui` | same feature hooks/services facade | direct db/repository imports |
| `features/*/service` | repositories, domain utils | other feature private modules |
| `shared/ui` | shared tokens/utils | app-specific business logic |

## Documentation Files

Every feature should include:
- `README.md` brief purpose and boundaries
- `API.md` if external contract exists
- `DECISIONS.md` for major architectural choices

## Refactor Strategy

1. Define target structure and ownership.
2. Move files in small, verified batches.
3. Keep temporary adapters for compatibility.
4. Remove old paths after consumers migrate.

## Anti-Patterns

1. Mixed conventions (`camelCase` + `kebab-case`) in same scope.
2. Deep relative imports like `../../../../` everywhere.
3. Domain logic hidden in `utils/` catch-all.
4. Cross-feature imports into private internals.
5. Oversized files with multiple unrelated responsibilities.

## Review Checklist

- Is structure aligned to feature ownership?
- Are module boundaries explicit and enforced?
- Are naming conventions consistent?
- Are aliases configured across all toolchains?
- Are barrels used only for stable public APIs?
- Is onboarding path clear from root to feature entry points?

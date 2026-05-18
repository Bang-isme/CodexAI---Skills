# Knowledge Graph Spec

## Purpose

Build a project-wide structural graph (dependencies, module boundaries, routes, models, code index, entrypoints, external dependencies, risk signals, and AI/human context) so AI and people can reason with architecture-level context instead of guessing from file names.

## When To Build

- At project start.
- After major restructuring (new modules, moved files, architecture changes).
- Weekly refresh for active repositories.
- Before cross-module refactors or large feature additions.

## Output Schema

```json
{
  "project": "my-project",
  "generated_at": "2026-04-25T14:00:00Z",
  "total_nodes": 87,
  "total_edges": 134,

  "modules": [
    {
      "name": "auth",
      "path": "src/features/auth/",
      "files": 8,
      "exports": ["AuthController", "AuthService", "JwtGuard", "AuthModule"],
      "depends_on": ["user", "config"],
      "depended_by": ["order", "admin"]
    },
    {
      "name": "order",
      "path": "src/features/order/",
      "files": 12,
      "exports": ["OrderController", "OrderService", "OrderModule"],
      "depends_on": ["auth", "product", "payment"],
      "depended_by": ["report", "notification"]
    }
  ],

  "routes": [
    {
      "method": "POST",
      "path": "/api/auth/login",
      "handler": "src/features/auth/auth.controller.ts:login",
      "middleware": ["rateLimiter", "validateBody"],
      "auth_required": false
    },
    {
      "method": "GET",
      "path": "/api/orders",
      "handler": "src/features/order/order.controller.ts:list",
      "middleware": ["jwtGuard", "paginationParser"],
      "auth_required": true
    }
  ],

  "models": [
    {
      "name": "User",
      "source": "prisma/schema.prisma",
      "fields": ["id", "email", "name", "password", "role", "createdAt"],
      "relations": [
        { "to": "Order", "type": "one-to-many" },
        { "to": "Session", "type": "one-to-many" }
      ]
    },
    {
      "name": "Order",
      "source": "prisma/schema.prisma",
      "fields": ["id", "userId", "status", "total", "createdAt"],
      "relations": [
        { "to": "User", "type": "many-to-one" },
        { "to": "OrderItem", "type": "one-to-many" }
      ]
    }
  ],

  "dependency_tree": {
    "external": {
      "express": "4.19.2",
      "prisma": "5.14.0",
      "jsonwebtoken": "9.0.2",
      "zod": "3.23.4"
    },
    "circular_dependencies": [],
    "orphaned_modules": ["src/utils/legacy-helpers.ts"]
  }
}
```


## Language Registry

`build_knowledge_graph.py` uses a language registry instead of hard-coded extension lists. Each registry entry maps an extension to:

- `language`: display name stored in `code_index[*].language`.
- `parser`: parser family (`javascript`, `python`, `javascript+component`, or pattern fallback).
- `import_extractor`: function that extracts import/module references.
- `definition_extractor`: function that extracts definitions.
- `resolver_strategy`: local dependency resolver (`javascript`, `python`, `relative`, `go`, `rust`, `package`, or `none`).
- `confidence`: reliability of the parser result.

Supported extensions include JavaScript/TypeScript/Python plus `.go`, `.rs`, `.java`, `.cs`, `.php`, `.rb`, `.kt`, `.kts`, `.swift`, `.vue`, `.svelte`, `.html`, `.css`, `.scss`, `.sql`, `.tf`, `.yaml`, `.yml`, and `.json`.

### Parser Reliability

| Confidence | Parser families | Expected reliability |
|---|---|---|
| `high` | Dedicated JavaScript/TypeScript/CommonJS/ESM and Python extractors | Preserves existing import/definition behavior and resolves common local imports. |
| `medium` | Pattern extractors for Go, Rust, Java, C#, PHP, Ruby, Kotlin, Swift, Vue/Svelte component scripts, Terraform, YAML, and JSON | Captures common class/function/interface/type/struct/enum/route/config blocks, but can miss macro-heavy, generated, or framework-specific constructs. |
| `low` | Asset/config-oriented pattern extractors for HTML, CSS/SCSS, SQL | Useful for navigation and obvious references; not a semantic parser. |

Every `code_index` entry includes parser metadata so consumers can decide how strongly to trust the extracted symbols.

## Graph Visualization

The knowledge graph can be rendered as a Mermaid diagram for documentation:

```mermaid
flowchart LR
    subgraph Features
        Auth[auth] --> User[user]
        Auth --> Config[config]
        Order[order] --> Auth
        Order --> Product[product]
        Order --> Payment[payment]
        Report[report] --> Order
        Notification[notification] --> Order
    end

    subgraph Infrastructure
        Config
        DB[(Database)]
        Cache[(Redis)]
    end

    User --> DB
    Order --> DB
    Auth --> Cache
```

## How AI Uses It

1. Run `build_knowledge_graph.py` to generate `.codex/knowledge-graph.json`, or run `build_knowledge_index.py` to generate `.codex/knowledge/knowledge-graph.json` plus `.codex/knowledge/index.html`.
2. Read `ai_context.recommended_read_order` before complex refactors, cross-module changes, or API-impact work.
3. Use `code_index` for file-level definitions, imports, imported-by, language, module, entrypoint, and risk tags.
4. Use module boundaries and route/model maps to reduce incorrect assumptions.
5. When modifying a module, check `imported_by` and `ai_context.top_dependents` to identify downstream impact.
6. When adding a new feature, check existing modules and the interactive HTML dashboard to avoid duplication.

## Detection Rules

| Node Type | Detection Method |
|---|---|
| Modules | Directory structure + barrel exports (index.ts) |
| Routes | Express/Next.js route declarations |
| Models | Prisma schema, TypeORM entities, Mongoose schemas |
| Dependencies | `package.json` + import analysis |
| Circular deps | DFS cycle detection on import graph |
| Middleware | Express `app.use()` and route-level middleware |

## Complements

- `predict_impact.py` can use graph context to estimate dependents more accurately.
- `project-profile.json` and session summaries provide additional style/history context.
- `codex-docs-change-sync` uses module boundaries to map code changes to documentation.

## Limitations

- Parsing is regex-based and best-effort.
- Dynamic imports, runtime DI containers, and advanced runtime wiring may be missed.
- Re-run regularly to keep graph fresh.
- Does not analyze runtime behavior — only static structure.

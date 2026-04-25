# Pattern Learner Spec

## Purpose

Analyze project conventions and coding patterns, then write `.codex/project-profile.json` so AI can match the codebase style before generating new code.

## When To Run

- At the start of a new project.
- When generated code keeps drifting from team conventions.
- After major architecture or style changes.
- After framework, ORM, or routing migrations.

## Output Schema

```json
{
  "project_name": "my-project",
  "analyzed_at": "2026-04-25T14:00:00Z",
  "file_count": 142,
  "primary_language": "TypeScript",

  "naming_conventions": {
    "files": "kebab-case (user-service.ts)",
    "components": "PascalCase (UserProfile.tsx)",
    "variables": "camelCase",
    "constants": "UPPER_SNAKE_CASE",
    "types": "PascalCase with suffix (UserDto, CreateOrderRequest)",
    "database_tables": "snake_case plural (user_sessions)",
    "database_columns": "snake_case (created_at)"
  },

  "import_style": {
    "order": ["node builtins", "external packages", "internal aliases", "relative"],
    "alias": "@/ maps to src/",
    "prefer_named": true,
    "barrel_exports": false
  },

  "architecture_patterns": {
    "structure": "feature-based (src/features/auth/, src/features/cart/)",
    "api_style": "REST with controller → service → repository layers",
    "state_management": "React Query for server state, Zustand for client state",
    "error_handling": "Custom AppError class → global error middleware",
    "validation": "Zod schemas co-located with route handlers"
  },

  "formatting": {
    "indent": "2 spaces",
    "semicolons": true,
    "quotes": "single",
    "trailing_commas": "all",
    "max_line_length": 100,
    "formatter": "prettier",
    "linter": "eslint with @typescript-eslint"
  },

  "testing_patterns": {
    "framework": "Jest",
    "file_naming": "*.test.ts co-located with source",
    "structure": "describe → it with AAA pattern (Arrange/Act/Assert)",
    "mocking": "jest.mock() for external dependencies",
    "fixtures": "src/__fixtures__/ for shared test data"
  },

  "dominant_patterns": [
    {
      "pattern": "All API handlers follow: validate → authorize → execute → respond",
      "example_file": "src/features/auth/auth.controller.ts",
      "frequency": "100% of controllers"
    },
    {
      "pattern": "Database queries wrapped in try/catch with Prisma error mapping",
      "example_file": "src/features/user/user.service.ts",
      "frequency": "95% of service files"
    },
    {
      "pattern": "React components use custom hooks for data fetching",
      "example_file": "src/features/cart/hooks/useCart.ts",
      "frequency": "90% of components with data"
    }
  ],

  "anti_patterns_detected": [
    {
      "pattern": "Mixed async error handling — some use try/catch, some use .catch()",
      "files": ["src/features/payment/payment.service.ts"],
      "recommendation": "Standardize on try/catch for consistency"
    }
  ]
}
```

## How AI Uses It

1. Run `analyze_patterns.py` to generate the profile.
2. Read `.codex/project-profile.json` before any implementation task.
3. Match naming, imports, formatting, and dominant framework patterns from the profile.
4. When generating new files, follow:
   - File naming from `naming_conventions.files`
   - Import order from `import_style.order`
   - Architecture layers from `architecture_patterns.structure`
   - Test structure from `testing_patterns`
5. When the profile conflicts with user instructions, user instructions win.

## Detection Rules

The pattern analyzer should detect:

| Category | Detection Method |
|---|---|
| Naming conventions | Regex on file names, variable names, export names |
| Import style | Parse import statements, count patterns |
| Formatting | Read `.prettierrc`, `.eslintrc`, `tsconfig.json` |
| Architecture | Analyze folder structure depth and naming |
| Testing patterns | Read test files for describe/it/test structure |
| Dominant patterns | Find repeated code structures across 3+ files |

## Update Frequency

- Re-run after significant folder structure changes.
- Re-run after migrations (framework, ORM, routing, auth).
- Re-run after style/lint rule changes.
- Re-run quarterly for long-running projects.

## Override

Users can manually edit `.codex/project-profile.json` to enforce explicit team preferences. Manual overrides take precedence over detected patterns.

# Diagram & Visual Documentation Patterns

Use this reference when the document needs visual explanation. Choose the simplest diagram type that communicates the point. Never add diagrams for decoration — every diagram must answer a specific question the reader has.

## Diagram Selection Decision Table

| Reader Question | Best Diagram | Tool |
|---|---|---|
| "How does data flow through the system?" | Flowchart | Mermaid `flowchart` |
| "What's the sequence of API calls?" | Sequence Diagram | Mermaid `sequenceDiagram` |
| "How are entities related?" | Entity Relationship | Mermaid `erDiagram` |
| "What are the states and transitions?" | State Diagram | Mermaid `stateDiagram-v2` |
| "Who does what and when?" | Gantt Chart | Mermaid `gantt` |
| "What's the class hierarchy?" | Class Diagram | Mermaid `classDiagram` |
| "What's the deployment topology?" | Architecture Diagram | Mermaid `C4Context` or `flowchart` |
| "How does the user journey work?" | User Journey | Mermaid `journey` |
| "What percentage/proportion?" | Pie Chart | Mermaid `pie` |
| "How does the Git branch work?" | Git Graph | Mermaid `gitGraph` |
| "What are the time relationships?" | Timeline | Mermaid `timeline` |
| "What's the mental model?" | Mind Map | Mermaid `mindmap` |
| "How is the project structured?" | Directory Tree | ASCII tree (text) |

## Mermaid Syntax Reference

### Flowchart (System Flow / Process)

```mermaid
flowchart TD
    A[User Request] --> B{Auth Valid?}
    B -->|Yes| C[Load Dashboard]
    B -->|No| D[Redirect to Login]
    C --> E[Fetch Data]
    E --> F{Cache Hit?}
    F -->|Yes| G[Return Cached]
    F -->|No| H[Query DB]
    H --> I[Update Cache]
    I --> G
```

**Rules:**
- Use `TD` (top-down) for processes, `LR` (left-right) for pipelines
- Limit to 15 nodes max — split into sub-diagrams if larger
- Use `{}` for decisions, `[]` for actions, `()` for rounded, `[()]` for database
- Label edges with `|condition|` for clarity

### Sequence Diagram (API / Interaction Flow)

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as API Server
    participant DB as Database
    participant Cache as Redis

    User->>FE: Click "Submit Order"
    FE->>API: POST /api/orders
    API->>DB: INSERT order
    DB-->>API: order_id
    API->>Cache: Invalidate user_orders
    API-->>FE: 201 Created {order_id}
    FE-->>User: Show confirmation
```

**Rules:**
- Use `actor` for humans, `participant` for systems
- Use `->>` for requests, `-->>` for responses
- Add `Note over` for important context
- Name participants with short aliases: `participant API as API Server`
- Show error paths with `alt/else` blocks:

```mermaid
sequenceDiagram
    FE->>API: POST /api/login
    alt Valid credentials
        API-->>FE: 200 {token}
    else Invalid
        API-->>FE: 401 Unauthorized
    end
```

### Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER {
        string id PK
        string email UK
        string name
        enum role
    }
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        string id PK
        string user_id FK
        enum status
        datetime created_at
    }
    PRODUCT ||--o{ ORDER_ITEM : "included in"
    PRODUCT {
        string id PK
        string name
        decimal price
        int stock
    }
    ORDER_ITEM {
        string id PK
        string order_id FK
        string product_id FK
        int quantity
    }
```

**Rules:**
- `||--||` one-to-one, `||--o{` one-to-many, `}o--o{` many-to-many
- Always mark PK, FK, UK
- Include only fields relevant to the discussion

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review : submit
    Review --> Approved : approve
    Review --> Draft : request_changes
    Approved --> Published : publish
    Published --> Archived : archive
    Archived --> [*]

    state Review {
        [*] --> PendingReview
        PendingReview --> InReview : assign_reviewer
        InReview --> ReviewComplete : complete
    }
```

### Gantt Chart (Timeline / Sprint Plan)

```mermaid
gantt
    title Sprint 3 Plan
    dateFormat YYYY-MM-DD
    section Backend
        API Design           :a1, 2026-04-01, 3d
        Implementation       :a2, after a1, 5d
        Testing              :a3, after a2, 2d
    section Frontend
        UI Components        :b1, 2026-04-01, 4d
        Integration          :b2, after b1, 3d
    section DevOps
        CI/CD Setup          :c1, 2026-04-05, 2d
        Deployment           :c2, after a3, 1d
```

### Architecture Diagram (C4-style)

```mermaid
flowchart TB
    subgraph External
        User([fa:fa-user End User])
        Admin([fa:fa-user-shield Admin])
    end

    subgraph "Frontend Layer"
        WebApp[React SPA<br/>Port 3000]
        AdminPanel[Admin Dashboard<br/>Port 3001]
    end

    subgraph "API Layer"
        Gateway[API Gateway<br/>Nginx]
        AuthSvc[Auth Service<br/>JWT + OAuth]
        CoreAPI[Core API<br/>Express.js]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary)]
        Redis[(Redis<br/>Cache + Sessions)]
        S3[(S3<br/>File Storage)]
    end

    User --> WebApp
    Admin --> AdminPanel
    WebApp --> Gateway
    AdminPanel --> Gateway
    Gateway --> AuthSvc
    Gateway --> CoreAPI
    CoreAPI --> PG
    CoreAPI --> Redis
    CoreAPI --> S3
```

### User Journey

```mermaid
journey
    title User Onboarding Flow
    section Registration
        Visit homepage: 5: User
        Click Sign Up: 4: User
        Fill form: 3: User
        Verify email: 2: User
    section First Use
        Complete profile: 3: User
        Read tutorial: 4: User
        Create first item: 5: User
    section Retention
        Receive notification: 4: System
        Return to app: 3: User
```

### Mind Map

```mermaid
mindmap
    root((Project))
        Frontend
            React
            TypeScript
            Tailwind CSS
        Backend
            Node.js
            Express
            PostgreSQL
        DevOps
            Docker
            GitHub Actions
            AWS
        Testing
            Jest
            Playwright
            k6
```

### Pie Chart

```mermaid
pie title Test Coverage by Module
    "API Routes" : 85
    "Services" : 72
    "Utils" : 95
    "Models" : 88
    "Middleware" : 60
```

### Git Graph

```mermaid
gitGraph
    commit id: "init"
    branch develop
    commit id: "setup"
    branch feature/auth
    commit id: "login"
    commit id: "register"
    checkout develop
    merge feature/auth id: "merge-auth"
    branch feature/dashboard
    commit id: "layout"
    commit id: "charts"
    checkout develop
    merge feature/dashboard id: "merge-dash"
    checkout main
    merge develop id: "release-v1"
    commit id: "hotfix" type: REVERSE
```

### Timeline

```mermaid
timeline
    title Project Milestones
    section Phase 1
        Week 1-2 : Requirements gathering
                  : Stakeholder interviews
        Week 3-4 : Architecture design
                  : Tech stack decision
    section Phase 2
        Week 5-8 : Core development
                  : API implementation
        Week 9-10 : Integration testing
    section Phase 3
        Week 11 : UAT
        Week 12 : Production deployment
```

## ASCII Diagrams (For Terminal / Plain Text)

When Mermaid is not available (email, terminal, plain .txt):

### Directory Tree
```
project/
├── src/
│   ├── controllers/
│   │   ├── auth.controller.js
│   │   └── user.controller.js
│   ├── models/
│   │   └── user.model.js
│   ├── routes/
│   │   └── index.js
│   └── app.js
├── tests/
│   └── auth.test.js
├── .env.example
├── package.json
└── README.md
```

### Simple Flow
```
[Request] → [Auth Middleware] → [Controller] → [Service] → [Database]
                  ↓ (401)
             [Error Handler]
```

### Comparison Table
```
┌──────────────┬───────────┬───────────┬──────────┐
│ Feature      │ Option A  │ Option B  │ Option C │
├──────────────┼───────────┼───────────┼──────────┤
│ Cost         │ $$$       │ $$        │ $        │
│ Performance  │ ★★★★★     │ ★★★★      │ ★★★      │
│ Complexity   │ High      │ Medium    │ Low      │
└──────────────┴───────────┴───────────┴──────────┘
```

## Diagram Quality Rules

1. **One diagram = one question answered.** If you need to show both data flow and entity relationships, use two diagrams.
2. **Label everything.** Every edge, every node. The reader should never have to guess what an arrow means.
3. **Max complexity:** 15 nodes per diagram. Split into layers if larger.
4. **Caption required.** Every diagram must have a title or a sentence before it explaining what the reader should learn from it.
5. **Consistent notation.** Use the same shapes for the same concepts across all diagrams in one document.
6. **Color with purpose.** Use colors to highlight status (green=ok, red=error, yellow=warning), not for decoration.
7. **Test render.** Always verify Mermaid renders correctly before delivering — syntax errors are common.

## When NOT to Use a Diagram

- The relationship can be stated in one sentence → use text
- The data is better as a table → use a table
- The reader will only read it once → keep it textual
- The document is being copy-pasted into email → use ASCII

# Teaching Mode

## Trigger Signals

- "explain this"
- "teach me"
- "how does this work"
- "why is it done this way"
- "walk me through"
- User opens a file and asks about internal logic

## Operating Protocol

### Step 1: Identify Scope

- Single function: explain purpose, inputs, outputs, and side effects.
- Single file: explain file role in architecture, key functions, and dependencies.
- Module/folder: explain module responsibility, public API, and internal flow.

### Step 2: Use Project Context, Not Generic Theory

- Wrong: "useEffect is a React hook for side effects."
- Right: "This `useEffect` in `Dashboard.jsx` fetches earnings data when `selectedMonth` changes. It calls `api.getDashboardEarnings()` and stores the result in `earningsData`."

### Step 3: Layered Explanation

1. Layer 1 (WHAT): one sentence for what the code does.
2. Layer 2 (HOW): step-by-step logic walkthrough with line references.
3. Layer 3 (WHY): why this design exists and what problem it solves.
4. Layer 4 (CONNECTIONS): what calls this and what this calls.

### Step 4: Highlight Gotchas

- Point out non-obvious behavior.
- Mention handled and unhandled edge cases.
- Note technical debt or safe improvement opportunities.

## Output Contract

1. One-line summary (Layer 1)
2. Logic walkthrough (Layer 2) with line references
3. Design rationale (Layer 3)
4. Dependency map (Layer 4): inbound and outbound dependencies
5. Gotchas and notes

## Anti-Patterns in Teaching

- Repeating raw code without insight
- Using generic documentation instead of project-specific behavior
- Explaining language basics when the user asked about business logic
- Explaining entire file when the user asked one function

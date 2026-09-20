# React + Tailwind + shadcn

Use when the repo already has or the user asked for this stack.

1. Prefer existing `components/ui` primitives over new one-off controls.
2. Tokens in CSS variables or Tailwind theme, not magic hex in JSX.
3. Dark mode via `class` or `prefers-color-scheme`, using tinted neutrals.
4. Forms: labels, `aria-invalid`, visible focus rings, server error mapping.
5. Do not add a purple gradient marketing layout to an app shell.

If shadcn is absent, do not silently `npx shadcn@latest init`. Ask or match the incumbent system.

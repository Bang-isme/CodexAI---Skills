# Next.js App Router

- Default to Server Components. Add `"use client"` only for state, effects, or browser APIs.
- Colocate loading/error/not-found files with the route.
- Keep data fetching on the server when possible; do not hide waterfalls in client effects.
- Metadata and titles are UX; no generic "My App".
- For marketing pages, still follow `codex-frontend-design` landing anatomy.

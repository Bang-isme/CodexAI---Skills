# Mobile Rules

## Core Principles

- Optimize for touch targets (minimum 44x44 px).
- Handle offline and unstable network conditions.
- Minimize battery-heavy background behavior.
- Respect iOS and Android platform conventions.
- Keep startup and scrolling performance within acceptable limits.

## Decision Checklist

1. framework/platform choice
2. navigation model
3. state ownership and offline sync
4. local storage strategy

## Performance Rules

- Use list virtualization for dynamic lists.
- Optimize media for device resolution.
- Avoid unnecessary bridge/platform channel calls.
- Prefer skeleton states over blocking spinners.

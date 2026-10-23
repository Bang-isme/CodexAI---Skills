# DevOps, Container Hardening & CI/CD Engineering Rules

## Scope and Triggers

Use this reference for containerization (`Dockerfile`, `docker-compose.yml`), CI/CD pipelines, build reproducibility, runtime configuration, health probes, and release automation.

---

## 1. Core DevOps & SRE Principles

1. **Immutable, Reproducible Builds:** Pin base image digests/versions and lockfiles (`npm ci`, `pnpm install --frozen-lockfile`, `pip install --require-hashes` / locked requirements). Never build different artifacts per environment—promote the same image/artifact across staging and production.
2. **Least-Privilege Non-Root Containers:** Production containers must use multi-stage builds, strip build toolchains from the runtime stage, run as an explicit non-root UID/GID (`USER 10001`), and mount root filesystems read-only where possible.
3. **Fail-Fast Boot & Graceful Shutdown (`SIGTERM`):** Validate all required environment variables at startup; on `SIGTERM`/`SIGINT`, stop accepting new requests, drain active HTTP connections and in-flight worker jobs within a bounded timeout (`15s–30s`), close DB pools cleanly, and exit `0`.
4. **Zero Secret Leakage:** Never bake `.env` files, private keys, or API tokens into Docker layers, Git history, or CI logs. Inject secrets at runtime via managed secret stores or CI OIDC federated identity.

---

## 2. Hardened Multi-Stage Dockerfile Pattern

```dockerfile
# Stage 1: Dependency & Build Stage
FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

# Stage 2: Minimal Non-Root Production Runtime
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Create unprivileged user and group
RUN addgroup -g 10001 -S appgroup && adduser -u 10001 -S appuser -G appgroup

COPY --from=builder --chown=appuser:appgroup /app/package.json ./
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist

USER 10001
EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health/live || exit 1

CMD ["node", "dist/server.js"]
```

---

## 3. Liveness vs Readiness Probes & Graceful Shutdown

Separate **Liveness** (is the process wedged and needing a restart?) from **Readiness** (can this instance serve traffic right now?):

| Probe | Endpoint | Checks Performed | Failure Action |
| --- | --- | --- | --- |
| **Liveness** | `GET /health/live` | Process event loop responsiveness only (never check external DB/APIs here, or a DB blip will restart all pods in a cascading loop) | Orchestrator restarts container |
| **Readiness** | `GET /health/ready` | Shutdown flag is `false` + primary DB/cache ping succeeds within `1500ms` | Load balancer stops routing new requests to this instance |

---

## 4. CI/CD Pipeline Architecture Checklist

- [ ] **Concurrency Cancelation:** Cancel superseded CI runs on feature branches (`concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }`).
- [ ] **Fast-Fail Stage Ordering:** `Lint & Typecheck + Secret Scan -> Unit & SILC Contract Tests -> Integration Tests -> Build Artifact -> Deploy Gate`.
- [ ] **Explicit Job Timeouts & Permissions:** Set `timeout-minutes` on every job and restrict `GITHUB_TOKEN` to `permissions: contents: read` by default.

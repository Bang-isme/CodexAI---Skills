# Container Security

## Core Principles
- Containers are NOT sandboxes — a container escape grants host access
- Run as non-root inside container (always)
- Use minimal base images (Alpine, distroless)
- Scan images for vulnerabilities before deployment
- Immutable containers: never SSH into running containers to fix

## Dockerfile Security

```dockerfile
# ---- SECURE Dockerfile ----

# 1. Pin exact version (not :latest)
FROM node:20.11-alpine AS builder

WORKDIR /app
COPY package*.json ./

# 2. Install dependencies without dev
RUN npm ci --production --ignore-scripts

COPY . .
RUN npm run build

# 3. Multi-stage: minimal production image
FROM node:20.11-alpine AS production

# 4. Run as non-root user
RUN addgroup -g 1001 appuser && \
    adduser -u 1001 -G appuser -D -s /bin/false appuser

WORKDIR /app

# 5. Copy only what's needed
COPY --from=builder --chown=appuser:appuser /app/dist ./dist
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/package.json .

# 6. Drop all capabilities
USER appuser

# 7. Read-only filesystem (app writes to volumes)
# Set via docker run --read-only

# 8. Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Dockerfile Anti-Patterns
```dockerfile
# ❌ Using :latest tag
FROM node:latest

# ❌ Running as root (default)
# No USER directive

# ❌ Copying everything
COPY . .

# ❌ Secrets in build
ARG DB_PASSWORD
ENV DB_PASSWORD=$DB_PASSWORD

# ❌ Installing unnecessary tools
RUN apt-get install -y vim curl wget git
```

## Image Scanning

```bash
# Trivy (recommended — fast, comprehensive)
trivy image myapp:v1.0.0

# Severity filter
trivy image --severity HIGH,CRITICAL myapp:v1.0.0

# Docker Scout (built into Docker Desktop)
docker scout cves myapp:v1.0.0
docker scout quickview myapp:v1.0.0

# Snyk
snyk container test myapp:v1.0.0
```

## Runtime Security

### Docker Run Hardening
```bash
docker run \
  --read-only \                        # Read-only filesystem
  --tmpfs /tmp:rw,noexec,nosuid \      # Writable /tmp without execute
  --security-opt no-new-privileges \   # Prevent privilege escalation
  --cap-drop ALL \                     # Drop all Linux capabilities
  --cap-add NET_BIND_SERVICE \         # Add only what's needed
  --memory 512m \                      # Memory limit
  --cpus 1.0 \                         # CPU limit
  --pids-limit 100 \                   # Process limit (fork bomb defense)
  --network app-internal \             # Isolated network
  -p 127.0.0.1:3000:3000 \            # Bind to localhost only
  myapp:v1.0.0
```

### Docker Compose Security
```yaml
services:
  app:
    image: myapp:v1.0.0
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
          pids: 100
    healthcheck:
      test: wget -qO- http://localhost:3000/health || exit 1
      interval: 30s
      retries: 3
```

## Kubernetes Security

### Pod Security Context
```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: [ALL]
    resources:
      limits:
        memory: 512Mi
        cpu: 500m
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: { sizeLimit: 100Mi }
```

### K8s RBAC
```yaml
# ServiceAccount per app (not default)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-server
  namespace: production
automountServiceAccountToken: false  # Don't auto-mount unless needed

---
# Role with minimal permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-server-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["api-secrets"]  # Only specific secret
  verbs: ["get"]
```

## Container Security Checklist
- [ ] Base image pinned to specific version (not :latest)
- [ ] Multi-stage build — no build tools in production image
- [ ] Running as non-root user
- [ ] All capabilities dropped, only required ones added
- [ ] Read-only root filesystem
- [ ] Resource limits set (memory, CPU, PIDs)
- [ ] Images scanned for vulnerabilities before deployment
- [ ] No secrets in image layers or environment
- [ ] Health check configured
- [ ] Network isolated (internal Docker network / K8s NetworkPolicy)

# Zero Trust Architecture

## Core Principle
Never trust, always verify. Every request is evaluated continuously using identity, device posture, network context, and requested action.

## Traditional vs Zero Trust

| Aspect | Traditional Perimeter | Zero Trust |
| --- | --- | --- |
| Trust model | Trust internal network | Trust nothing by default |
| Authentication | At network edge | Every request/session |
| Authorization | Coarse network rules | Fine-grained resource/action |
| Lateral movement | Easier once inside | Limited by segmentation |
| Security boundary | Network perimeter | Identity + policy engine |

## Pillars
- Identity verification on every request.
- Device trust and posture awareness.
- Network microsegmentation.
- Least privilege authorization.
- Continuous telemetry and audit logging.

## Identity-Centric Enforcement Example
```javascript
const zeroTrustAuth = async (req, res, next) => {
  const token = extractToken(req);
  const decoded = verifyJWT(token);
  if (!decoded) return res.status(401).json({ error: "Invalid token" });

  const session = await Session.findById(decoded.sessionId);
  if (!session || session.revokedAt) {
    return res.status(401).json({ error: "Session invalid" });
  }

  const riskScore = await calculateRiskScore({
    ip: req.ip,
    userAgent: req.headers["user-agent"],
    userId: decoded.userId,
    lastKnownIP: session.lastIP,
  });

  if (riskScore > 0.7) {
    return res.status(403).json({ error: "Step-up MFA required", code: "STEP_UP_AUTH" });
  }

  const allowed = await checkPermission(decoded.userId, req.method, req.path);
  if (!allowed) return res.status(403).json({ error: "Access denied" });

  await AuditLog.create({
    userId: decoded.userId,
    action: `${req.method} ${req.path}`,
    riskScore,
    ip: req.ip,
    timestamp: new Date(),
  });

  req.user = decoded;
  return next();
};

const calculateRiskScore = async ({ ip, userAgent, userId, lastKnownIP }) => {
  let score = 0;
  const knownIPs = await UserIP.find({ userId });
  if (!knownIPs.some((entry) => entry.ip === ip)) score += 0.3;

  const knownDevices = await UserDevice.find({ userId });
  if (!knownDevices.some((entry) => entry.userAgent === userAgent)) score += 0.2;

  const hour = new Date().getHours();
  if (hour < 6 || hour > 22) score += 0.1;

  const distance = await calculateGeoDistance(ip, lastKnownIP);
  if (distance > 1000) score += 0.4;

  return Math.min(score, 1.0);
};
```

## Microsegmentation Example (Kubernetes)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-server-policy
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes: [Ingress, Egress]
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - port: 3000
      protocol: TCP
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
      protocol: TCP
```

## API Layer Controls

| Layer | Control |
| --- | --- |
| Transport | mTLS for service-to-service traffic |
| Identity | Short-lived JWT + session revocation |
| Authorization | Per-endpoint RBAC/ABAC |
| Abuse protection | Identity-aware rate limits |
| Observability | Full access audit logs |

## Implementation Roadmap
- Phase 1: MFA, short-lived access tokens, session revocation.
- Phase 2: RBAC on every endpoint, risk-based step-up auth.
- Phase 3: microsegmentation and mTLS between services.
- Phase 4: continuous verification using behavior and device signals.

## Checklist
- [ ] MFA enforced for privileged and remote access
- [ ] Sessions revocable and centrally tracked
- [ ] Risk-based authentication implemented
- [ ] East-west traffic segmented
- [ ] Access logs include identity and context

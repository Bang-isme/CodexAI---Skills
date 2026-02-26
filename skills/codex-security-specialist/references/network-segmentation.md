# Network Segmentation

## Core Principle
Different security zones for different trust levels. Traffic between zones must pass through firewall rules.

## Segmentation Architecture

```
                         INTERNET
                            │
                     ┌──────┴──────┐
                     │   Edge/CDN   │  DDoS protection, WAF
                     └──────┬──────┘
                            │
                     ┌──────┴──────┐
                     │   DMZ Zone   │  10.0.1.0/28
                     │  (Nginx/LB)  │  Public-facing only
                     └──────┬──────┘
                            │ (Firewall: only 80/443 from DMZ → App)
                     ┌──────┴──────┐
                     │   App Zone   │  10.0.2.0/24
                     │  (API/Web)   │  Business logic
                     └──────┬──────┘
                            │ (Firewall: only DB ports from App → Data)
                     ┌──────┴──────┐
                     │  Data Zone   │  10.0.3.0/24
                     │ (DB/Cache)   │  Most restricted
                     └──────┬──────┘
                            │ (Admin access only via bastion)
                     ┌──────┴──────┐
                     │  Mgmt Zone   │  10.0.4.0/28
                     │  (Bastion,   │  SSH, monitoring
                     │  Monitoring) │
                     └─────────────┘
```

## Zone Rules

| From Zone | To Zone | Allowed | Denied |
| --- | --- | --- | --- |
| Internet | DMZ | 80, 443 | Everything else |
| DMZ | App | App ports (3000, 8080) | SSH, DB |
| App | Data | 3306, 5432, 6379, 27017 | SSH, HTTP |
| App | Internet | HTTPS (API calls) | Inbound |
| Data | Any | None (no outbound) | All |
| Mgmt | All | SSH (22), monitoring ports | None |
| All | Mgmt | None | Direct access |

## AWS VPC Implementation

```
VPC: 10.0.0.0/16
├── Public Subnet:  10.0.1.0/24 (DMZ — NAT Gateway, ALB)
├── Private Subnet: 10.0.2.0/24 (App — EC2/ECS instances)
├── Private Subnet: 10.0.3.0/24 (Data — RDS, ElastiCache)
└── Private Subnet: 10.0.4.0/28 (Mgmt — Bastion host)

Route Tables:
- Public: 0.0.0.0/0 → Internet Gateway
- Private: 0.0.0.0/0 → NAT Gateway (outbound only)
- Data: No internet route (fully isolated)
```

## Docker Network Segmentation

```yaml
# docker-compose.yml — isolated networks
services:
  nginx:
    networks: [frontend, backend]   # bridge between zones
  app:
    networks: [backend, database]   # no direct internet
  db:
    networks: [database]            # most isolated
  redis:
    networks: [database]

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true    # no external access
  database:
    driver: bridge
    internal: true    # no external access
```

## Kubernetes Network Policies

```yaml
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-all, namespace: production }
spec:
  podSelector: {}
  policyTypes: [Ingress]

---
# Allow only frontend → backend on port 3000
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-frontend-to-backend }
spec:
  podSelector:
    matchLabels: { app: backend }
  ingress:
  - from:
    - podSelector: { matchLabels: { app: frontend } }
    ports: [{ protocol: TCP, port: 3000 }]
```

## Segmentation Checklist
- [ ] Database/cache servers not accessible from internet
- [ ] Each zone has its own subnet/security group
- [ ] Inter-zone traffic limited to required ports only
- [ ] Bastion host is the only SSH entry point
- [ ] Data zone has no outbound internet access
- [ ] Network policies enforced in Kubernetes
- [ ] Docker internal networks used for backend services

# Threat Modeling

## Core Principle
Identify threats BEFORE writing code. Cheaper to fix in design than production.

## When to Threat Model
- New feature touching auth, payments, or user data
- Architecture change (new service, new data flow)
- Third-party integration
- Before every major release

## STRIDE Framework

| Threat | Description | Example | Mitigation |
| --- | --- | --- | --- |
| **S**poofing | Pretend to be someone else | Fake login, stolen JWT | MFA, JWT expiry, cert pinning |
| **T**ampering | Modify data in transit/rest | Man-in-the-middle, DB manipulation | TLS, integrity checks, signatures |
| **R**epudiation | Deny having done something | "I didn't place that order" | Audit logs, digital signatures |
| **I**nformation Disclosure | Access unauthorized data | IDOR, verbose errors, log leaks | RBAC, output filtering, log sanitization |
| **D**enial of Service | Make system unavailable | DDoS, resource exhaustion | Rate limiting, CDN, auto-scaling |
| **E**levation of Privilege | Gain higher access | JWT manipulation, SQL injection | Input validation, RBAC, least privilege |

## Threat Modeling Process

### Step 1: Diagram the System
```
                      User
                       │
                  [Web Browser]
                       │ HTTPS
                  [Load Balancer]
                       │
                  [API Server]
                   ╱        ╲
              [MongoDB]   [Redis]     [S3]
                                       │
                            [Email Service (external)]
```

### Step 2: Identify Trust Boundaries
```
TRUST BOUNDARY 1: Internet ↔ Load Balancer (untrusted → DMZ)
TRUST BOUNDARY 2: Load Balancer ↔ API Server (DMZ → internal)
TRUST BOUNDARY 3: API Server ↔ Database (internal → data)
TRUST BOUNDARY 4: API Server ↔ External Service (internal → third-party)
```

### Step 3: Apply STRIDE at Each Boundary

```markdown
#### Boundary 1: Internet → Load Balancer
| Threat | Attack | Mitigation |
| Spoofing | Fake requests | TLS + authentication |
| Tampering | Modified request body | Input validation |
| DoS | Traffic flood | Rate limiting, WAF, CDN |

#### Boundary 3: API → Database
| Threat | Attack | Mitigation |
| Injection | SQL/NoSQL injection | Parameterized queries |
| Info Disclosure | Mass data extraction | Pagination, field filtering |
| Tampering | Direct DB modification | App-only access, no shared accounts |
```

### Step 4: Risk Assessment (DREAD)

| Factor | Score 1-3 | Description |
| --- | --- | --- |
| **D**amage | How bad if exploited? | 1=Low, 3=Critical |
| **R**eproducibility | How easy to reproduce? | 1=Hard, 3=Always |
| **E**xploitability | How easy to exploit? | 1=Expert, 3=Script kiddie |
| **A**ffected users | How many impacted? | 1=Few, 3=All |
| **D**iscoverability | How easy to find? | 1=Internal, 3=Public |

Score ≥ 12: Critical (fix before release)
Score 8-11: High (fix within sprint)
Score 4-7: Medium (plan for next cycle)

## Threat Model Document Template

```markdown
# Threat Model: [Feature Name]
**Date**: YYYY-MM-DD | **Author**: [Name] | **Status**: Draft/Reviewed/Approved

## System Description
[What does this feature do? What data does it handle?]

## Data Flow Diagram
[Diagram showing components, data flows, trust boundaries]

## Assets
- User credentials (Critical)
- Personal data (High)
- Session tokens (High)
- Application logs (Medium)

## Threats Identified
| # | STRIDE | Threat | Risk (DREAD) | Mitigation | Status |
| 1 | S | Token theft via XSS | 11 | CSP, HttpOnly cookies | ✅ Mitigated |
| 2 | I | IDOR on user profiles | 13 | Ownership middleware | 🔴 Open |
| 3 | D | API rate abuse | 8 | Rate limiting | ✅ Mitigated |

## Residual Risks
[Risks accepted with justification]
```

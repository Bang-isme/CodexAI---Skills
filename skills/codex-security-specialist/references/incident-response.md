# Incident Response

## Incident Severity Levels

| Level | Description | Example | Response |
| --- | --- | --- | --- |
| P1 — Critical | Active breach, data exfiltration, service down | DB dumped, ransomware, DDoS | All hands, < 15 min response |
| P2 — High | Confirmed vulnerability being exploited | Auth bypass discovered in prod | Security team, < 1 hour |
| P3 — Medium | Potential compromise, unusual activity | Spike in failed logins | Investigate within 4 hours |
| P4 — Low | Minor security event, no impact | Port scan detected | Log and review next business day |

## Incident Response Phases (NIST)

```
1. PREPARE → 2. DETECT → 3. CONTAIN → 4. ERADICATE → 5. RECOVER → 6. LESSONS LEARNED
```

## Phase 1: Preparation (Before Incident)

### Essential Preparations
- [ ] Incident response team defined (roles, contacts)
- [ ] Communication channels established (Slack channel, phone tree)
- [ ] Runbooks written for common scenarios
- [ ] Log aggregation working (ELK/CloudWatch)
- [ ] Backup and restore tested
- [ ] Legal/PR contacts identified
- [ ] Forensics tools available

### Contact List Template
```
Incident Commander:  [Name] — [Phone] — [Email]
Security Lead:       [Name] — [Phone] — [Email]
DevOps Lead:         [Name] — [Phone] — [Email]
Legal Counsel:       [Name] — [Phone] — [Email]
PR/Communications:   [Name] — [Phone] — [Email]
Cloud Provider:      [Support Number] — [Account ID]
```

## Phase 2: Detection

### Indicators of Compromise (IoC)
```
🔴 Unusual outbound traffic (data exfiltration)
🔴 New admin accounts created unexpectedly
🔴 Modified system files / binaries
🔴 Disabled security tools / logging
🔴 Large number of failed login attempts from single IP
🔴 Database queries returning unusually large result sets
🔴 API calls from unexpected geographic locations
🔴 Unexpected cron jobs or scheduled tasks
```

### Detection Sources
```
- Application logs (auth failures, errors)
- WAF/IDS alerts
- Cloud monitoring (GuardDuty, CloudTrail)
- Dependency vulnerability alerts (Snyk, Dependabot)
- User reports ("I can't log in", "I see strange data")
- External reports (security researchers, bug bounty)
```

## Phase 3: Containment

### Immediate Actions (First 30 Minutes)
```bash
# 1. Isolate affected system (DON'T shut down — preserve evidence)
# Network isolation:
iptables -I INPUT -j DROP    # Block all incoming
iptables -I INPUT -s ADMIN_IP -j ACCEPT  # Allow admin only

# 2. Revoke compromised credentials
# Rotate: JWT secrets, API keys, DB passwords, SSH keys
# Force logout all sessions

# 3. Block attacker IP (if known)
iptables -I INPUT -s ATTACKER_IP -j DROP

# 4. Preserve evidence
# Capture memory dump
dd if=/dev/mem of=/evidence/memory.dump bs=1M

# Capture disk image
dd if=/dev/sda of=/evidence/disk.img bs=4M

# Save logs before rotation
cp /var/log/auth.log /evidence/
cp /var/log/nginx/access.log /evidence/
docker logs app > /evidence/app.log 2>&1
```

### Short-Term Containment
```
- Deploy WAF rule to block attack pattern
- Disable compromised feature/endpoint
- Switch to maintenance mode if needed
- Enable enhanced logging on affected systems
```

## Phase 4: Eradication

```
- Remove malware / unauthorized access
- Patch vulnerability that was exploited
- Reset ALL credentials (not just compromised ones)
- Verify no backdoors remain
- Scan all systems for similar vulnerabilities
```

## Phase 5: Recovery

```
1. Restore from VERIFIED clean backup
2. Deploy patched version
3. Monitor intensively for 48-72 hours
4. Gradually restore normal operations
5. Verify data integrity
```

## Phase 6: Post-Incident Review

### Blameless Post-Mortem Template
```markdown
# Incident Post-Mortem: [Title]

**Date**: YYYY-MM-DD
**Duration**: [start] to [resolution]
**Severity**: P1/P2/P3/P4
**Impact**: [what was affected, how many users]

## Timeline
- HH:MM — [event]
- HH:MM — [detection]
- HH:MM — [response action]
- HH:MM — [resolution]

## Root Cause
[Technical explanation of what went wrong]

## What Went Well
- [Fast detection]
- [Effective communication]

## What Went Wrong
- [Delayed response because...]
- [Missing monitoring for...]

## Action Items
- [ ] [Action] — Owner: [Name] — Due: [Date]
- [ ] [Action] — Owner: [Name] — Due: [Date]
```

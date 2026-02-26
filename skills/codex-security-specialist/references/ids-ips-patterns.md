# IDS/IPS Patterns

## IDS vs IPS

| Capability | IDS | IPS |
| --- | --- | --- |
| Primary role | Detect and alert | Detect and block |
| Placement | Passive/span/tap | Inline traffic path |
| Impact risk | Low | Higher (false positives can block) |
| Best use | Visibility and triage | Automated protection for known threats |

## Detection Layers
- Network detection: Suricata/Snort signatures and anomaly rules.
- Host detection: login anomalies, file integrity, suspicious processes.
- Application detection: API abuse, token replay, impossible travel.

## Host-Based Detection Examples
```javascript
// Login anomaly: brute-force behavior
const detectLoginAnomaly = async (username, ip) => {
  const failuresLast10m = await LoginEvent.countDocuments({
    username,
    ip,
    status: "failed",
    createdAt: { $gte: new Date(Date.now() - 10 * 60 * 1000) },
  });
  return failuresLast10m >= 10;
};

// Impossible travel
const detectImpossibleTravel = async (userId, currentIP) => {
  const last = await LoginEvent.findOne({ userId, status: "success" }).sort({ createdAt: -1 });
  if (!last) return false;
  const km = await calculateGeoDistance(last.ip, currentIP);
  const minutes = (Date.now() - last.createdAt.getTime()) / 60000;
  return minutes > 0 && km / (minutes / 60) > 900;
};
```

## API Abuse Signals
- Sudden spike in token-specific request volume.
- Excessive 401/403 on single principal.
- Repeated high-cost query patterns.
- Enumeration behavior (sequential IDs, broad scans).

## File Integrity Monitoring
```bash
# Linux baseline + verify example using AIDE
aide --init
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
aide --check
```

Monitor:
- Auth binaries, SSH configs, sudoers, cron, systemd unit files.
- Web root, API config, secrets mount points.

## Suricata Example Rule
```text
alert http any any -> $HOME_NET any (
  msg:"Potential SQLi pattern";
  flow:established,to_server;
  content:"union select"; nocase;
  classtype:web-application-attack;
  sid:100001;
  rev:1;
)
```

## Alert Severity Matrix

| Severity | Typical Trigger | Action |
| --- | --- | --- |
| Critical | Confirmed compromise, active exfiltration | Immediate containment + incident response |
| High | Privilege escalation attempt, malware indicator | Block source + urgent triage |
| Medium | Repeated abuse pattern | Investigate within SLA, tune rules |
| Low | Single suspicious event | Correlate and monitor |

## Response Workflow
1. Validate alert (reduce false positives).
2. Enrich with context (identity, host, geo, session).
3. Contain (block token/IP/session/process).
4. Investigate timeline and blast radius.
5. Patch control gaps and tune detection rules.

## Checklist
- [ ] IDS baseline deployed for ingress/egress visibility
- [ ] IPS enabled for high-confidence signatures
- [ ] Login anomaly and impossible travel detection active
- [ ] File integrity monitoring scheduled
- [ ] Alert routing and on-call escalation defined

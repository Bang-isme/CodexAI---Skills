# Security Scan
## Purpose
Run static security analysis to detect common vulnerability patterns in source code.
It helps identify risks before shipping and supports remediation planning.
## When to Run
- Before deployment to staging or production.
- During formal code review or security review.
- After adding authentication, authorization, or cryptography logic.
- On explicit `$security-scan` request.
## How AI Uses It
1. Run `security_scan.py` on the project root.
2. Parse structured findings and group them by severity.
3. Block on critical findings and provide prioritized remediation guidance.
## Integration Behavior
- Trigger on `$security-scan` or "run security scan".
- Auto-run in quality gate for deployment-sensitive tasks.
- Blocking for critical severity; advisory for medium and low findings.
## Output Intent
- Produce a security risk summary for gate decisions and follow-up fixes.
- Caveat: static analysis may miss runtime-only attack paths and environment issues.

# Security Rules

## Always Apply

- validate and sanitize all external input
- parameterize queries
- hash passwords with modern algorithms
- enforce HTTPS for sensitive paths
- secure cookie/session settings
- never expose stack traces to clients
- keep secrets in environment or secret manager
- rate-limit auth and public write endpoints

## Quick OWASP Checks

1. injection defenses
2. auth/session robustness
3. encryption in transit and at rest
4. access control correctness
5. secure configuration defaults
6. XSS and unsafe rendering prevention
7. dependency risk awareness
8. security logging coverage

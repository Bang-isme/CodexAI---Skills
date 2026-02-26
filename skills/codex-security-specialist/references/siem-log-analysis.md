# SIEM & Log Analysis

## Core Principle
Centralize ALL security-relevant logs → correlate → alert → investigate.

## Architecture

```
Sources:                     Collector:           Storage:         Analysis:
├── App logs ──────────┐
├── Auth logs ─────────┤
├── Nginx access logs ─┼──→ Filebeat/Fluentd ──→ Elasticsearch ──→ Kibana
├── Firewall logs ─────┤                                          Dashboards
├── Docker logs ───────┤                                          Alerts
├── CloudTrail ────────┘
└── System logs (syslog)
```

## ELK Stack Setup (Docker)

```yaml
# docker-compose-elk.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    volumes: [es-data:/usr/share/elasticsearch/data]
    ports: ["9200:9200"]

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=kibana_system
      - ELASTICSEARCH_PASSWORD=${KIBANA_PASSWORD}
    ports: ["5601:5601"]

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.12.0
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

## Security Events to Monitor

| Event | Log Source | Alert Priority |
| --- | --- | --- |
| 5+ failed logins from same IP in 1 min | Auth log | 🔴 High |
| Successful login from new country | Auth log + GeoIP | 🟡 Medium |
| Admin account created | App log | 🔴 High |
| Database query returned > 10,000 rows | App log | 🟡 Medium |
| 4xx/5xx error rate spike (>5% in 5 min) | Nginx log | 🟡 Medium |
| Outbound traffic to unusual IP/port | Firewall log | 🔴 High |
| SSH login outside business hours | Auth log | 🟡 Medium |
| File modified in /etc or /usr/bin | Auditd | 🔴 High |
| Docker container started with --privileged | Docker log | 🔴 High |
| API endpoint accessed > 100x by single user | App log | 🟡 Medium |

## Alert Rules (Elasticsearch Watcher)

```json
{
  "trigger": { "schedule": { "interval": "1m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["filebeat-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                { "match": { "event.action": "login_failed" } },
                { "range": { "@timestamp": { "gte": "now-5m" } } }
              ]
            }
          },
          "aggs": {
            "by_ip": { "terms": { "field": "source.ip", "min_doc_count": 5 } }
          }
        }
      }
    }
  },
  "condition": {
    "compare": { "ctx.payload.aggregations.by_ip.buckets.0.doc_count": { "gte": 5 } }
  },
  "actions": {
    "notify_slack": {
      "webhook": {
        "url": "https://hooks.slack.com/...",
        "body": "🚨 Brute force detected: {{ctx.payload.aggregations.by_ip.buckets.0.key}} — {{ctx.payload.aggregations.by_ip.buckets.0.doc_count}} failed logins in 5 min"
      }
    }
  }
}
```

## Log Retention Policy

| Log Type | Retention | Reason |
| --- | --- | --- |
| Security events | 1 year | Compliance, forensics |
| Access logs | 90 days | Debugging, audit |
| Application logs | 30 days | Debugging |
| Debug logs | 7 days | Short-term troubleshoot |

## Rules
- Never log sensitive data (passwords, tokens, PII)
- Structured logs (JSON) — easier to parse and search
- Include correlation ID in every log entry
- Timestamp in UTC (ISO 8601)
- Immutable log storage (prevent tampering)

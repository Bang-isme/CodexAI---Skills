# Firewall Rules & Access Control

## Core Principles
- Default DENY all incoming, ALLOW all outgoing
- Whitelist approach: explicitly allow only what's needed
- Stateful inspection: track connection state, not just packets
- Log denied traffic for security monitoring
- Review rules quarterly — remove unused entries

## Linux iptables

### Basic Structure
```bash
# Default policy: DROP everything
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections (stateful)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (rate limited)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow ICMP ping (optional)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
iptables -A INPUT -j DROP
```

## UFW (Uncomplicated Firewall — Ubuntu)

```bash
# Reset and enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow specific services
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow from specific IP only
sudo ufw allow from 10.0.0.0/24 to any port 3306 comment 'MySQL from app subnet'
sudo ufw allow from 10.0.0.0/24 to any port 6379 comment 'Redis from app subnet'

# Rate limit SSH
sudo ufw limit 22/tcp

# Enable logging
sudo ufw logging medium

# Enable
sudo ufw enable
sudo ufw status verbose
```

## AWS Security Groups

```json
// Inbound Rules — Web Server Security Group
[
  { "Protocol": "tcp", "Port": 80,   "Source": "0.0.0.0/0",          "Description": "HTTP from anywhere" },
  { "Protocol": "tcp", "Port": 443,  "Source": "0.0.0.0/0",          "Description": "HTTPS from anywhere" },
  { "Protocol": "tcp", "Port": 22,   "Source": "10.0.0.0/24",        "Description": "SSH from bastion only" }
]

// Inbound Rules — Database Security Group
[
  { "Protocol": "tcp", "Port": 3306, "Source": "sg-app-server",       "Description": "MySQL from app servers only" },
  { "Protocol": "tcp", "Port": 5432, "Source": "sg-app-server",       "Description": "PostgreSQL from app servers" }
]

// ❌ NEVER: Database SG with Source 0.0.0.0/0
// ❌ NEVER: Allow all ports (Port: 0-65535)
```

## Docker / Container Firewall

```bash
# Docker exposes ports on 0.0.0.0 by default — DANGEROUS
# Always bind to 127.0.0.1 for internal services
docker run -p 127.0.0.1:3306:3306 mysql  # ✅ internal only
docker run -p 3306:3306 mysql             # ❌ exposed to world

# Docker Compose
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"  # ✅
    # NOT: "5432:5432"          # ❌
```

## Firewall Audit Checklist
- [ ] Default policy is DENY for INPUT and FORWARD
- [ ] Only ports 22/80/443 exposed to 0.0.0.0/0 (if any)
- [ ] Database ports restricted to app subnet/security group
- [ ] SSH rate limited (max 4 attempts per 60 seconds)
- [ ] Dropped packets are logged
- [ ] No rules using 0.0.0.0/0 for database or cache ports
- [ ] Rules reviewed and cleaned in last 90 days
- [ ] Docker ports bound to 127.0.0.1 for internal services

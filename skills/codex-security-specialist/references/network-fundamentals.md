# Network Fundamentals for Security

## OSI Model — Security at Each Layer

| Layer | Name | Protocols | Security Concerns | Defense |
| --- | --- | --- | --- | --- |
| 7 | Application | HTTP, DNS, SMTP, FTP | XSS, injection, RCE | WAF, input validation |
| 6 | Presentation | SSL/TLS, MIME | Downgrade attacks | TLS 1.2+, HSTS |
| 5 | Session | NetBIOS, RPC | Session hijacking | Token rotation, timeouts |
| 4 | Transport | TCP, UDP | SYN flood, port scan | Firewall rules, rate limiting |
| 3 | Network | IP, ICMP, IPsec | IP spoofing, MITM | IPsec, network segmentation |
| 2 | Data Link | ARP, MAC | ARP poisoning, MAC flood | Port security, 802.1X |
| 1 | Physical | Ethernet, Wi-Fi | Wiretapping, physical access | Physical security, encryption |

## TCP/IP Fundamentals

### Three-Way Handshake
```
Client → SYN → Server
Client ← SYN-ACK ← Server
Client → ACK → Server
```
**Attack**: SYN Flood — send SYN without completing ACK → exhaust server connections.
**Defense**: SYN cookies, connection limits, firewall rate limiting.

### Common Ports to Know

| Port | Service | Security Notes |
| --- | --- | --- |
| 22 | SSH | Change default port, use key auth only |
| 25 | SMTP | Often exploited for relay; restrict access |
| 53 | DNS | DNS amplification attacks; use DNSSEC |
| 80 | HTTP | Redirect to 443 always |
| 443 | HTTPS | Only port exposed to public for web |
| 3306 | MySQL | NEVER expose to public; bind 127.0.0.1 |
| 5432 | PostgreSQL | Same — internal only |
| 6379 | Redis | No default auth; bind + password required |
| 27017 | MongoDB | No default auth; bind + auth required |

### Port Security Rules
```bash
# Show all listening ports
ss -tlnp        # Linux
netstat -tlnp   # Legacy

# Rule: Only ports 22, 80, 443 should be exposed to 0.0.0.0
# All database/cache ports should bind to 127.0.0.1 or Docker network
```

## IP Addressing & Subnetting

### CIDR Notation
```
10.0.0.0/8    → 16,777,216 addresses (Class A private)
172.16.0.0/12 → 1,048,576 addresses (Class B private)
192.168.0.0/16 → 65,536 addresses (Class C private)

# Common subnets
/24 = 256 addresses  (192.168.1.0 - 192.168.1.255)
/28 = 16 addresses   (small subnet for DMZ)
/32 = 1 address      (single host)
```

### Network Segmentation Purpose
```
Internet
    ↓
[DMZ /28] — Web servers, reverse proxy (public-facing)
    ↓ (firewall)
[App Subnet /24] — Application servers (private)
    ↓ (firewall)
[Data Subnet /24] — Databases, caches (most restricted)
    ↓ (firewall)
[Management Subnet /28] — Admin access, monitoring, backups
```

## Network Tools for Security

| Tool | Purpose | Example |
| --- | --- | --- |
| `nmap` | Port scanning, service detection | `nmap -sV -sC target.com` |
| `tcpdump` | Packet capture | `tcpdump -i eth0 port 443 -w capture.pcap` |
| `wireshark` | Packet analysis (GUI) | Analyze capture.pcap |
| `traceroute` | Network path analysis | `traceroute target.com` |
| `dig` | DNS lookup/debugging | `dig +dnssec example.com` |
| `netstat` / `ss` | Local port/connection listing | `ss -tlnp` |
| `curl` | HTTP testing with headers | `curl -I -v https://target.com` |
| `openssl` | SSL/TLS testing | `openssl s_client -connect host:443` |

## Common Attack Vectors

| Attack | Layer | How It Works | Defense |
| --- | --- | --- | --- |
| SYN Flood | Transport | Exhaust TCP connections | SYN cookies, rate limit |
| ARP Poisoning | Data Link | Redirect traffic via fake ARP | Static ARP, VLAN isolation |
| DNS Spoofing | Application | Return fake DNS responses | DNSSEC |
| Man-in-the-Middle | Network | Intercept unencrypted traffic | TLS everywhere, cert pinning |
| Port Scanning | Transport | Discover open services | Firewall, port knocking |
| IP Spoofing | Network | Fake source IP | BCP38 filtering, IPsec |

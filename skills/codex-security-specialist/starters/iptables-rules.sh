#!/bin/bash
# ============================================
# IPTABLES FIREWALL STARTER — Production Server
# Run as root. Save with: iptables-save > /etc/iptables/rules.v4
# ============================================

set -e

echo "🔒 Configuring firewall rules..."

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t mangle -F

# Default policies: DROP incoming, ACCEPT outgoing
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ---- Loopback ----
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# ---- Established connections ----
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ---- Anti-spoofing ----
iptables -A INPUT -s 127.0.0.0/8 ! -i lo -j DROP    # Spoofed loopback
iptables -A INPUT -s 0.0.0.0/8 -j DROP               # Invalid source
iptables -A INPUT -s 169.254.0.0/16 -j DROP           # Link-local
iptables -A INPUT -s 224.0.0.0/4 -j DROP              # Multicast

# ---- SSH (rate limited: max 4 new connections per 60s) ----
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --set --name SSH --rsource
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
  -m recent --update --seconds 60 --hitcount 4 --name SSH --rsource -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# ---- HTTP/HTTPS ----
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# ---- ICMP (limited ping) ----
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# ---- Internal services (allow from app subnet only) ----
# Uncomment and adjust subnet as needed:
# iptables -A INPUT -p tcp --dport 3306 -s 10.0.2.0/24 -j ACCEPT  # MySQL
# iptables -A INPUT -p tcp --dport 5432 -s 10.0.2.0/24 -j ACCEPT  # PostgreSQL
# iptables -A INPUT -p tcp --dport 6379 -s 10.0.2.0/24 -j ACCEPT  # Redis
# iptables -A INPUT -p tcp --dport 27017 -s 10.0.2.0/24 -j ACCEPT # MongoDB

# ---- Log dropped packets ----
iptables -A INPUT -j LOG --log-prefix "IPT_DROP: " --log-level 4
iptables -A INPUT -j DROP

echo "✅ Firewall rules applied."
echo "📝 Save rules: iptables-save > /etc/iptables/rules.v4"
echo "📝 Persist: apt install iptables-persistent"

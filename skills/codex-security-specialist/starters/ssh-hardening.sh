#!/bin/bash
# ============================================
# SSH HARDENING STARTER — Production Server
# Run as root. Backup sshd_config first.
# ============================================

set -e

SSHD_CONFIG="/etc/ssh/sshd_config"
BACKUP="${SSHD_CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

echo "🔒 Hardening SSH configuration..."
echo "📦 Backing up: ${BACKUP}"
cp "$SSHD_CONFIG" "$BACKUP"

# Apply hardened settings
cat > "$SSHD_CONFIG" << 'EOF'
# ============================================
# SSH HARDENED CONFIG
# ============================================

# ---- Network ----
Port 22                          # Consider changing to non-standard port
AddressFamily inet               # IPv4 only (add inet6 if needed)
ListenAddress 0.0.0.0

# ---- Authentication ----
PermitRootLogin no               # NEVER allow root SSH
PasswordAuthentication no        # Keys only
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# ---- Session ----
MaxAuthTries 3                   # Lock after 3 failed attempts
MaxSessions 3                   # Max 3 sessions per connection
LoginGraceTime 30               # 30s to authenticate
ClientAliveInterval 300         # 5 min idle timeout
ClientAliveCountMax 2           # Disconnect after 2 missed keepalives

# ---- Security ----
X11Forwarding no                 # Disable X11 (not needed on servers)
AllowTcpForwarding yes          # Needed for SSH tunnels
AllowAgentForwarding no          # Disable unless needed
PermitTunnel no
PrintMotd no
PrintLastLog yes
TCPKeepAlive no                  # Use ClientAlive* instead
Compression delayed

# ---- Crypto (strong algorithms only) ----
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# ---- Logging ----
SyslogFacility AUTH
LogLevel VERBOSE                 # Log auth attempts in detail

# ---- Allow specific users/groups ----
# AllowUsers deploy admin
# AllowGroups ssh-users

# ---- Banner ----
Banner /etc/ssh/banner
EOF

# Create warning banner
cat > /etc/ssh/banner << 'EOF'
*************************************************************
WARNING: Unauthorized access to this system is prohibited.
All connections are monitored and recorded.
Disconnect IMMEDIATELY if you are not authorized.
*************************************************************
EOF

# Validate config before restart
echo "🔍 Validating configuration..."
sshd -t

if [ $? -eq 0 ]; then
    echo "✅ Configuration valid. Restarting SSH..."
    systemctl restart sshd
    echo "✅ SSH hardened successfully."
    echo ""
    echo "⚠️  IMPORTANT:"
    echo "  1. Ensure your SSH key is in ~/.ssh/authorized_keys"
    echo "  2. Test new SSH connection in ANOTHER terminal before closing this one"
    echo "  3. If locked out, use backup: cp ${BACKUP} ${SSHD_CONFIG} && systemctl restart sshd"
else
    echo "❌ Configuration error! Restoring backup..."
    cp "$BACKUP" "$SSHD_CONFIG"
    echo "Restored original config. No changes applied."
    exit 1
fi

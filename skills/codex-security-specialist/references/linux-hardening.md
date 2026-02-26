# Linux Server Hardening

## Hardening Priority Order
1. User & access control (most critical)
2. SSH configuration
3. Firewall (covered in firewall-rules.md)
4. Service minimization
5. File permissions & integrity
6. Kernel security
7. Audit logging

## User & Access Control

### Principle of Least Privilege
```bash
# Create application user (no shell, no home)
useradd --system --no-create-home --shell /usr/sbin/nologin appuser

# Create admin user with specific group
useradd -m -G sudo -s /bin/bash admin-user
passwd admin-user

# Lock unused accounts
usermod --lock nobody
usermod --expiredate 1 games

# List all users with login shell
awk -F: '$7 !~ /nologin|false/ {print $1, $7}' /etc/passwd

# List sudoers
grep -Po '^[^#]*\S' /etc/sudoers /etc/sudoers.d/*
```

### Sudo Hardening
```bash
# /etc/sudoers.d/hardening
Defaults    timestamp_timeout=5        # Re-auth after 5 min idle
Defaults    passwd_tries=3             # Max 3 password attempts
Defaults    logfile=/var/log/sudo.log  # Log all sudo usage
Defaults    requiretty                 # Require real terminal
Defaults    use_pty                    # Run in pseudo-terminal

# Specific command allowlist (not full sudo)
deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart app, /usr/bin/docker compose up -d
```

### Password Policy
```bash
# /etc/security/pwquality.conf
minlen = 12
dcredit = -1        # At least 1 digit
ucredit = -1        # At least 1 uppercase
lcredit = -1        # At least 1 lowercase
ocredit = -1        # At least 1 special char
maxrepeat = 3       # Max 3 consecutive same chars
enforce_for_root

# /etc/login.defs
PASS_MAX_DAYS   90    # Force password change every 90 days
PASS_MIN_DAYS   7     # Min 7 days between changes
PASS_WARN_AGE   14    # Warn 14 days before expiry
LOGIN_RETRIES   3
```

## Service Minimization

```bash
# List all running services
systemctl list-units --type=service --state=running

# Disable unnecessary services
systemctl disable --now avahi-daemon     # mDNS (not needed on server)
systemctl disable --now cups             # Printing
systemctl disable --now bluetooth        # Bluetooth
systemctl disable --now rpcbind          # NFS (if not used)
systemctl disable --now nfs-server

# List listening ports → identify unknown services
ss -tlnp
# Every listening port should be justified. Kill unknown ones.
```

## File Permissions

```bash
# Critical file permissions
chmod 600 /etc/shadow           # Owner read only
chmod 644 /etc/passwd           # World readable (UIDs only)
chmod 640 /etc/group
chmod 700 /root                 # Root home
chmod 600 /etc/ssh/sshd_config
chmod 600 /etc/crontab

# Ensure no world-writable files (except /tmp)
find / -xdev -type f -perm -0002 -print 2>/dev/null

# Find SUID/SGID binaries (potential privilege escalation)
find / -xdev \( -perm -4000 -o -perm -2000 \) -type f -print 2>/dev/null

# Remove unnecessary SUID
chmod u-s /usr/bin/chfn /usr/bin/chsh /usr/bin/newgrp
```

## Kernel Security (sysctl)

```bash
# /etc/sysctl.d/99-hardening.conf

# Network
net.ipv4.ip_forward = 0                          # No routing (unless gateway)
net.ipv4.conf.all.send_redirects = 0             # Don't send ICMP redirects
net.ipv4.conf.all.accept_redirects = 0           # Ignore ICMP redirects
net.ipv4.conf.all.accept_source_route = 0        # Reject source routing
net.ipv4.conf.all.log_martians = 1               # Log suspicious packets
net.ipv4.conf.all.rp_filter = 1                  # Reverse path filtering
net.ipv4.tcp_syncookies = 1                      # SYN flood protection
net.ipv4.icmp_echo_ignore_broadcasts = 1         # Ignore broadcast pings

# Memory protection
kernel.randomize_va_space = 2                     # Full ASLR
kernel.kptr_restrict = 2                          # Hide kernel pointers
kernel.dmesg_restrict = 1                         # Restrict dmesg access
kernel.yama.ptrace_scope = 2                      # Restrict ptrace

# File system
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0                             # No core dumps for SUID

# Apply
sysctl -p /etc/sysctl.d/99-hardening.conf
```

## Audit Logging (auditd)

```bash
# Install
apt install auditd

# /etc/audit/rules.d/hardening.rules
# Monitor authentication
-w /etc/shadow -p wa -k shadow_changes
-w /etc/passwd -p wa -k passwd_changes
-w /etc/sudoers -p wa -k sudoers_changes
-w /var/log/auth.log -p r -k auth_log_read

# Monitor SSH keys
-w /home/ -p wa -k home_changes
-a always,exit -F dir=/root/.ssh -F perm=wa -k ssh_key_changes

# Monitor privileged commands
-a always,exit -F path=/usr/bin/sudo -F perm=x -k sudo_exec
-a always,exit -F path=/usr/bin/su -F perm=x -k su_exec

# Monitor network connections
-a always,exit -F arch=b64 -S connect -k outgoing_connections

# Search audit logs
ausearch -k shadow_changes --start today
aureport --auth --summary
```

## Auto-Update (Unattended Upgrades)

```bash
# Install
apt install unattended-upgrades

# /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";  # Security updates only
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";  # Manual reboot for control
Unattended-Upgrade::Mail "admin@example.com";
```

## Hardening Checklist
- [ ] Root login disabled (SSH + console)
- [ ] Application uses dedicated non-root user
- [ ] Unnecessary services disabled
- [ ] SUID/SGID binaries audited and minimized
- [ ] Kernel hardening sysctl applied
- [ ] Audit logging enabled (auditd)
- [ ] Automatic security updates enabled
- [ ] Failed login attempts monitored (fail2ban)
- [ ] Cron jobs reviewed — no unauthorized entries
- [ ] /tmp mounted with noexec,nosuid,nodev

# VPN & Tunneling

## When to Use

| Scenario | Solution |
| --- | --- |
| Remote developer access to internal services | WireGuard VPN |
| Site-to-site (office → cloud) | IPsec or WireGuard |
| Quick temporary tunnel for testing | SSH tunnel |
| Access staging/dev database from local | SSH tunnel or WireGuard |
| Zero-trust remote access | WireGuard + identity-aware proxy |

## WireGuard (Recommended — Fast, Simple, Modern)

### Server Configuration
```ini
# /etc/wireguard/wg0.conf (Server)
[Interface]
Address = 10.10.0.1/24
ListenPort = 51820
PrivateKey = SERVER_PRIVATE_KEY

# Enable IP forwarding
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Developer 1
[Peer]
PublicKey = DEVELOPER1_PUBLIC_KEY
AllowedIPs = 10.10.0.2/32

# Developer 2
[Peer]
PublicKey = DEVELOPER2_PUBLIC_KEY
AllowedIPs = 10.10.0.3/32
```

### Client Configuration
```ini
# /etc/wireguard/wg0.conf (Client)
[Interface]
Address = 10.10.0.2/24
PrivateKey = CLIENT_PRIVATE_KEY
DNS = 1.1.1.1

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = vpn.example.com:51820
AllowedIPs = 10.10.0.0/24, 10.0.0.0/24  # VPN subnet + internal subnet
PersistentKeepalive = 25
```

### Key Generation
```bash
wg genkey | tee privatekey | wg pubkey > publickey
# NEVER share private key — distribute public key only
```

## SSH Tunnel (Quick Access — No VPN Setup)

```bash
# Local port forward: access remote DB on localhost:5432
ssh -L 5432:db-server:5432 user@bastion-host
# Now connect: psql -h localhost -p 5432

# Remote port forward: expose local dev server to remote
ssh -R 8080:localhost:3000 user@remote-server
# Remote can access your local app at localhost:8080

# SOCKS proxy: route all traffic through SSH
ssh -D 1080 user@bastion-host
# Configure browser/app to use SOCKS5 proxy localhost:1080

# Jump host (bastion)
ssh -J user@bastion user@internal-server
```

## Security Rules
- WireGuard port (51820/udp) should be the ONLY VPN port exposed
- Rotate keys quarterly or when team member leaves
- Revoke access immediately when developer leaves team
- Log all VPN connections for audit
- Split tunnel: only route internal traffic through VPN (not all traffic)
- Never use VPN as sole authentication — combine with SSH keys + MFA

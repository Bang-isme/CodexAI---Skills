# SSL/TLS & Certificate Management

## TLS Version Decision

| Version | Status | Use? |
| --- | --- | --- |
| SSL 3.0 | Deprecated, vulnerable (POODLE) | ❌ Never |
| TLS 1.0 | Deprecated since 2020 | ❌ Never |
| TLS 1.1 | Deprecated since 2020 | ❌ Never |
| TLS 1.2 | Supported, secure with right ciphers | ✅ Minimum |
| TLS 1.3 | Latest, fastest, most secure | ✅ Preferred |

## Let's Encrypt Setup (Certbot)

```bash
# Install
sudo apt install certbot python3-certbot-nginx

# Issue certificate (auto-configures Nginx)
sudo certbot --nginx -d example.com -d www.example.com

# Auto-renewal (certbot installs cron automatically)
sudo certbot renew --dry-run

# Manual renewal
sudo certbot renew

# Certificate is stored at:
# /etc/letsencrypt/live/example.com/fullchain.pem (cert + chain)
# /etc/letsencrypt/live/example.com/privkey.pem   (private key)
```

## Certificate Chain
```
Root CA (trusted by browser)
  └── Intermediate CA (signed by Root)
       └── Server Certificate (signed by Intermediate)

fullchain.pem = Server Cert + Intermediate (what you serve)
privkey.pem   = Private Key (never share, never expose)
```

## Nginx TLS Hardened Config

```nginx
server {
    listen 443 ssl http2;

    # Certificate
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Protocol versions
    ssl_protocols TLSv1.2 TLSv1.3;

    # Cipher suites (TLS 1.2 — strong only)
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # OCSP Stapling (faster certificate validation)
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    # Session resumption (faster reconnects)
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off; # disable for forward secrecy

    # DH params (optional, for TLS 1.2)
    ssl_dhparam /etc/nginx/dhparam.pem;

    # HSTS (tell browsers to always use HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
}
```

## SSL Testing

```bash
# Test your SSL configuration
# Online: https://www.ssllabs.com/ssltest/

# CLI test
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# Check certificate expiry
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates

# View certificate details
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -text

# nmap SSL scan
nmap --script ssl-enum-ciphers -p 443 example.com
```

## Certificate Monitoring
- Set up alerts for certificates expiring within 30 days
- Monitor certificate transparency logs for unauthorized issuance
- Use CAA DNS records to restrict which CAs can issue certificates

## Self-Signed Certificates (Development Only)

```bash
# Generate self-signed cert (dev only — NEVER production)
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout dev-key.pem -out dev-cert.pem \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

## Certificate Checklist
- [ ] TLS 1.2 minimum, TLS 1.3 preferred
- [ ] HSTS enabled with includeSubDomains
- [ ] OCSP stapling enabled
- [ ] Auto-renewal configured (certbot timer)
- [ ] SSL Labs grade A or A+ achieved
- [ ] No weak ciphers (RC4, DES, 3DES, MD5)
- [ ] Certificate expiry monitoring active
- [ ] CAA DNS record restricts certificate issuers
- [ ] HTTP → HTTPS redirect on port 80

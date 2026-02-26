# DNS Security

## DNS Threats

| Threat | How It Works | Impact | Defense |
| --- | --- | --- | --- |
| DNS Spoofing/Cache Poisoning | Inject fake DNS responses | Redirect users to malicious site | DNSSEC |
| DNS Amplification DDoS | Spoof source IP, use DNS as amplifier | Overwhelm target with traffic | Rate limiting, BCP38 |
| DNS Tunneling | Encode data in DNS queries | Data exfiltration | Monitor unusual DNS patterns |
| Typosquatting | Register similar domain names | Phishing, credential theft | Monitor typo variants |
| Zone Transfer | Query AXFR to dump all records | Expose internal infrastructure | Restrict AXFR to authorized IPs |

## DNSSEC

```
Purpose: Cryptographically sign DNS records to prevent spoofing.

Without DNSSEC:
  dig example.com → 1.2.3.4 (could be spoofed)

With DNSSEC:
  dig +dnssec example.com → 1.2.3.4 + RRSIG (signature verified)
```

```bash
# Verify DNSSEC
dig +dnssec +short example.com
# If "ad" flag in response → authenticated data (DNSSEC valid)

dig @8.8.8.8 example.com +dnssec +multi
```

## DNS over HTTPS (DoH) / DNS over TLS (DoT)

| Feature | DoH | DoT |
| --- | --- | --- |
| Port | 443 (same as HTTPS) | 853 |
| Encryption | TLS via HTTPS | TLS direct |
| Blockable | Hard (looks like HTTPS) | Easy (unique port) |
| Best for | Privacy-focused, browser | Server/resolver config |

```bash
# Test DoH with curl
curl -s 'https://1.1.1.1/dns-query?name=example.com&type=A' \
  -H 'Accept: application/dns-json' | jq
```

## DNS Record Security Best Practices

```
# SPF — prevent email spoofing
example.com. TXT "v=spf1 include:_spf.google.com ~all"

# DKIM — email authentication
selector._domainkey.example.com. TXT "v=DKIM1; k=rsa; p=PUBLIC_KEY"

# DMARC — email policy enforcement
_dmarc.example.com. TXT "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"

# CAA — restrict which CAs can issue certificates
example.com. CAA 0 issue "letsencrypt.org"
example.com. CAA 0 iodef "mailto:security@example.com"
```

## DNS Checklist
- [ ] DNSSEC enabled on domain
- [ ] SPF, DKIM, DMARC configured for email security
- [ ] CAA record restricts certificate issuance
- [ ] Zone transfers restricted (AXFR denied to public)
- [ ] DNS query logging enabled
- [ ] Monitoring for unusual DNS patterns (tunneling)
- [ ] Typo-variant domains monitored or registered

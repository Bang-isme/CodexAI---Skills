# PKI And Certificates Guide

## Why PKI Matters
Public Key Infrastructure (PKI) provides identity, encryption, and integrity via certificate chains rooted in trusted Certificate Authorities (CAs).

## X.509 Certificate Fields

| Field | Purpose |
| --- | --- |
| Subject | Identity of certificate owner (CN, O, OU) |
| Subject Alternative Name (SAN) | Valid hostnames/IPs for TLS validation |
| Issuer | CA that signed the certificate |
| Validity | `Not Before` and `Not After` dates |
| Public Key | Key used for encryption/signature verification |
| Key Usage / Extended Key Usage | Allowed operations (server auth, client auth) |
| Serial Number | Unique cert identifier for revocation |

## Certificate Types
- Public TLS certificates: Internet-facing domains.
- Internal CA certificates: internal services and private networks.
- Client certificates: mTLS client authentication.
- Code-signing certificates: software artifact signing.

## Certificate Lifecycle
1. Generate private key securely.
2. Create CSR (Certificate Signing Request).
3. CA validates and issues certificate.
4. Deploy full chain (leaf + intermediates).
5. Monitor expiry and rotate before deadline.
6. Revoke compromised certificates quickly (CRL/OCSP).

## Node.js mTLS Example
```javascript
import https from "https";
import fs from "fs";

const server = https.createServer(
  {
    key: fs.readFileSync("./server-key.pem"),
    cert: fs.readFileSync("./server-cert.pem"),
    ca: fs.readFileSync("./ca-cert.pem"),
    requestCert: true,
    rejectUnauthorized: true,
  },
  (req, res) => {
    const authorized = req.client.authorized;
    if (!authorized) {
      res.writeHead(401);
      return res.end("Client cert required");
    }
    res.writeHead(200);
    return res.end("mTLS OK");
  }
);

server.listen(8443);
```

## OpenSSL Internal CA Flow
```bash
# Create root CA key/cert
openssl genrsa -out ca-key.pem 4096
openssl req -x509 -new -nodes -key ca-key.pem -sha256 -days 3650 -out ca-cert.pem \
  -subj "/CN=MyCompany Internal CA/O=MyCompany"

# Server key + CSR
openssl genrsa -out server-key.pem 2048
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=api.internal.local/O=MyCompany"

# Sign server cert
openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days 365 -sha256
```

## Operational Best Practices
- Automate renewal (ACME/certbot/internal automation).
- Alert on expiration at least 30 days in advance.
- Use short-lived certs where possible.
- Keep private keys with least privilege permissions.
- Never commit cert private keys to git.
- Enforce complete certificate chain on servers.

## Checklist
- [ ] Certificate auto-renew configured
- [ ] Expiration monitoring and alerting active
- [ ] Revocation process documented and tested
- [ ] mTLS configured for sensitive service-to-service traffic
- [ ] Internal CA root key protected offline/HSM when possible

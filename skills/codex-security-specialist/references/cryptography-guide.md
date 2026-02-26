# Cryptography Guide For Engineers

## Core Rule
Use modern primitives and proven libraries. Do not design custom cryptographic algorithms.

## Algorithm Decision Table

| Use Case | Recommended | Avoid |
| --- | --- | --- |
| Password storage | `argon2id` or `bcrypt` | SHA-256 without salt |
| Symmetric encryption | AES-256-GCM or ChaCha20-Poly1305 | AES-ECB |
| Asymmetric encryption | RSA-3072+ or ECDSA P-256 | RSA-1024 |
| Key exchange | ECDHE | Static RSA key exchange |
| Hash for integrity | SHA-256/SHA-512 | MD5, SHA-1 |
| Message authentication | HMAC-SHA-256 | Plain hash(secret + data) |

## Password Hashing
```javascript
import bcrypt from "bcryptjs";

const SALT_ROUNDS = 12;

export async function hashPassword(password) {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(password, hash) {
  return bcrypt.compare(password, hash);
}
```

## AES-256-GCM (Authenticated Encryption)
```javascript
import crypto from "crypto";

const ALGO = "aes-256-gcm";

export function encrypt(plaintext, key) {
  const iv = crypto.randomBytes(12); // 96-bit nonce for GCM
  const cipher = crypto.createCipheriv(ALGO, key, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();

  return {
    iv: iv.toString("hex"),
    ciphertext: ciphertext.toString("hex"),
    tag: tag.toString("hex"),
  };
}

export function decrypt(payload, key) {
  const decipher = crypto.createDecipheriv(ALGO, key, Buffer.from(payload.iv, "hex"));
  decipher.setAuthTag(Buffer.from(payload.tag, "hex"));
  const plaintext = Buffer.concat([
    decipher.update(Buffer.from(payload.ciphertext, "hex")),
    decipher.final(),
  ]);
  return plaintext.toString("utf8");
}
```

## Signing And Verification (RSA/ECDSA)
```javascript
import crypto from "crypto";

export function signData(data, privateKeyPem) {
  const sign = crypto.createSign("sha256");
  sign.update(data);
  sign.end();
  return sign.sign(privateKeyPem, "base64");
}

export function verifyData(data, signature, publicKeyPem) {
  const verify = crypto.createVerify("sha256");
  verify.update(data);
  verify.end();
  return verify.verify(publicKeyPem, signature, "base64");
}
```

## Key Management Rules
- Generate keys with CSPRNG only.
- Store secrets and keys in KMS/HSM/Vault, never in source code.
- Rotate keys on schedule and on suspected compromise.
- Version keys to support safe re-encryption.
- Restrict key usage by policy (encrypt-only, sign-only).

## Randomness Rules
- Use `crypto.randomBytes` (Node) or platform CSPRNG.
- Never use `Math.random()` for security tokens.
- Session IDs, password reset tokens, API secrets must be high entropy.

## Data At Rest / In Transit
- At rest: encrypt sensitive data with service-managed or customer-managed keys.
- In transit: TLS 1.2+ minimum, prefer TLS 1.3.
- Internal service calls should also be encrypted (mTLS where possible).

## Crypto Anti-Patterns
- Reusing IV/nonces with GCM.
- Using one key for multiple purposes without key separation.
- Storing raw encryption keys in `.env` committed to git.
- Rolling your own JWT signing/verification logic.
- Disabling certificate validation outside isolated local development.

## Quick Checklist
- [ ] Passwords hashed with `argon2id` or `bcrypt`
- [ ] Sensitive payloads encrypted with authenticated mode (GCM/ChaCha20-Poly1305)
- [ ] Keys stored in managed secret system
- [ ] Key rotation policy documented and tested
- [ ] Deprecated algorithms blocked by policy

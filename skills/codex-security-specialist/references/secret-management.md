# Secret Management

## Core Principles
- **Never hardcode secrets** in source code, configs, or Docker images
- **Never commit secrets** to version control (even private repos)
- **Rotate secrets** regularly and on team member departure
- **Encrypt at rest** — secrets stored encrypted, decrypted only when used
- **Audit access** — log who accessed which secret and when
- **Least privilege** — each service gets only the secrets it needs

## Secret Classification

| Type | Risk Level | Rotation | Example |
| --- | --- | --- | --- |
| API keys | High | 90 days | Stripe, SendGrid, AWS |
| Database credentials | Critical | 90 days | MySQL root, Mongo admin |
| JWT signing keys | Critical | 180 days | Access + refresh secrets |
| Encryption keys | Critical | Annual | AES data-at-rest key |
| SSH keys | High | Annual | Deploy keys, bastion |
| Service accounts | High | 90 days | CI/CD, monitoring |
| OAuth client secrets | High | 180 days | Google, GitHub OAuth |

## Environment Variables (Minimum Viable)

```bash
# .env (NEVER committed — in .gitignore)
JWT_SECRET=khd92hf9...
MONGO_URI=mongodb://admin:s3cr3t@...
STRIPE_SECRET_KEY=sk_live_...

# .env.example (committed — no real values)
JWT_SECRET=CHANGE_ME_use_openssl_rand_base64_32
MONGO_URI=mongodb://admin:CHANGE_ME@localhost:27017/app
STRIPE_SECRET_KEY=sk_test_CHANGE_ME
```

```bash
# Generate strong secrets
openssl rand -base64 32   # Random 256-bit key
openssl rand -hex 32      # 64-char hex string
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## HashiCorp Vault (Production)

### Architecture
```
Application → Vault API → Auth (AppRole) → Secret Engine → Return Secret
                                          → Audit Log
```

### Setup
```bash
# Start dev server (testing only)
vault server -dev

# Enable secrets engine
vault secrets enable -path=app kv-v2

# Store secrets
vault kv put app/api jwt_secret="abc123" mongo_uri="mongodb://..."
vault kv put app/payments stripe_key="sk_live_..."

# Read secrets
vault kv get app/api
vault kv get -field=jwt_secret app/api
```

### AppRole Authentication (for services)
```bash
# Create policy
vault policy write app-api - << EOF
path "app/data/api" {
  capabilities = ["read"]
}
path "app/data/payments" {
  capabilities = ["deny"]  # API server can't access payment secrets
}
EOF

# Create AppRole
vault auth enable approle
vault write auth/approle/role/api-server \
  token_policies="app-api" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=24h

# Get Role ID and Secret ID (give to app at deploy time)
vault read auth/approle/role/api-server/role-id
vault write -f auth/approle/role/api-server/secret-id
```

### Application Integration (Node.js)
```javascript
import vault from 'node-vault';

const vc = vault({
  endpoint: process.env.VAULT_ADDR,
  token: process.env.VAULT_TOKEN, // or use AppRole login
});

const loadSecrets = async () => {
  const { data } = await vc.read('app/data/api');
  process.env.JWT_SECRET = data.data.jwt_secret;
  process.env.MONGO_URI = data.data.mongo_uri;
};

// Call at startup before any connections
await loadSecrets();
```

## Docker Secrets

```yaml
# docker-compose.yml — use Docker secrets (not env)
services:
  app:
    image: myapp:latest
    secrets:
      - jwt_secret
      - db_password
    environment:
      JWT_SECRET_FILE: /run/secrets/jwt_secret
      DB_PASSWORD_FILE: /run/secrets/db_password

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt   # external to repo
  db_password:
    file: ./secrets/db_password.txt
```

```javascript
// Read Docker secrets in app
import { readFileSync } from 'fs';

const readSecret = (name) => {
  const filePath = process.env[`${name}_FILE`];
  if (filePath) return readFileSync(filePath, 'utf8').trim();
  return process.env[name]; // fallback to env var
};

const JWT_SECRET = readSecret('JWT_SECRET');
```

## AWS Secrets Manager

```javascript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

const client = new SecretsManagerClient({ region: 'ap-southeast-1' });

const getSecret = async (secretName) => {
  const command = new GetSecretValueCommand({ SecretId: secretName });
  const response = await client.send(command);
  return JSON.parse(response.SecretString);
};

// Usage
const secrets = await getSecret('prod/api/credentials');
// { jwt_secret: "...", mongo_uri: "...", stripe_key: "..." }
```

## Git Pre-Commit Secret Detection

```bash
# Install git-secrets
git secrets --install
git secrets --register-aws  # Detect AWS keys

# Custom patterns
git secrets --add 'sk_live_[a-zA-Z0-9]{20,}'     # Stripe live keys
git secrets --add 'mongodb\+srv://[^:]+:[^@]+@'    # MongoDB URIs with password
git secrets --add '-----BEGIN (RSA |EC )?PRIVATE KEY-----'

# Pre-commit hook: blocks commit if secret found
```

## Rotation Procedure
1. Generate new secret
2. Add new secret to secret store (Vault/AWS SM)
3. Deploy app with new secret support (accept old OR new)
4. Verify app works with new secret
5. Remove old secret from secret store
6. Deploy app with old secret removed

## Checklist
- [ ] No secrets in source code or git history
- [ ] .gitignore includes .env, *.pem, *.key
- [ ] Pre-commit hook detects accidental secret commits
- [ ] Secrets rotated on schedule and on team member departure
- [ ] Each service has only the secrets it needs (least privilege)
- [ ] Secret access is audited and logged
- [ ] Production secrets never used in development/staging

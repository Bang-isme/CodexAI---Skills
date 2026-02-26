# ============================================
# HASHICORP VAULT STARTER — App Secret Management
# ============================================

# --- Storage Backend ---
storage "file" {
  path = "/vault/data"
}

# For production, use:
# storage "consul" {
#   address = "consul:8500"
#   path    = "vault/"
# }

# --- Listener ---
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "false"
  tls_cert_file = "/vault/tls/cert.pem"
  tls_key_file  = "/vault/tls/key.pem"
}

# --- General ---
api_addr     = "https://vault.example.com:8200"
cluster_addr = "https://vault.example.com:8201"
ui           = true

# --- Audit ---
# Enable after initialization:
# vault audit enable file file_path=/var/log/vault/audit.log

# --- Policies ---

# API Server Policy — read-only access to app secrets
# Save as: policies/api-server.hcl
# path "secret/data/app/api" {
#   capabilities = ["read"]
# }
# path "secret/data/app/database" {
#   capabilities = ["read"]
# }
# path "secret/metadata/*" {
#   capabilities = ["list"]
# }

# Admin Policy — full access
# Save as: policies/admin.hcl
# path "secret/*" {
#   capabilities = ["create", "read", "update", "delete", "list"]
# }
# path "sys/*" {
#   capabilities = ["read", "list"]
# }

# --- Docker Compose Usage ---
# services:
#   vault:
#     image: hashicorp/vault:1.15
#     cap_add: [IPC_LOCK]
#     ports: ["8200:8200"]
#     volumes:
#       - vault-data:/vault/data
#       - ./vault/config:/vault/config
#       - ./vault/tls:/vault/tls
#     command: vault server -config=/vault/config/vault.hcl
#     environment:
#       VAULT_ADDR: "https://0.0.0.0:8200"

# --- Init & Unseal (first time only) ---
# vault operator init -key-shares=5 -key-threshold=3
# vault operator unseal <key1>
# vault operator unseal <key2>
# vault operator unseal <key3>
# SAVE UNSEAL KEYS AND ROOT TOKEN SECURELY (offline)

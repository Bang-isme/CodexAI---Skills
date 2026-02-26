# Infrastructure as Code (IaC) Security

## Core Principle
Infrastructure configs ARE code → scan them like code. One misconfigured Terraform resource can expose your entire database to the internet.

## Common IaC Misconfigurations

| Misconfiguration | Risk | Example |
| --- | --- | --- |
| Public S3 bucket | Data exposure | `acl = "public-read"` |
| Open security group | Network exposure | `cidr_blocks = ["0.0.0.0/0"]` on DB port |
| No encryption at rest | Data at rest exposure | `encrypted = false` on EBS/RDS |
| Root API key in config | Credential exposure | `access_key = "AKIA..."` |
| Debug mode in production | Information disclosure | `NODE_ENV = "development"` |
| Missing logging | No audit trail | CloudTrail disabled |
| Wildcard IAM permissions | Privilege escalation | `Action: "*"` |

## Terraform Security Scanning

### tfsec (Aqua Security)
```bash
# Install
brew install tfsec

# Scan
tfsec ./terraform/
tfsec ./terraform/ --format json --out results.json

# Severity filter
tfsec ./terraform/ --minimum-severity HIGH
```

### tfsec Rules Examples
```
AVD-AWS-0086: S3 bucket has public access enabled → CRITICAL
AVD-AWS-0104: RDS encryption is not enabled → HIGH
AVD-AWS-0107: Security group allows ingress from 0.0.0.0/0 → HIGH
AVD-AWS-0057: IAM policy with wildcard action → CRITICAL
```

### Checkov (Bridgecrew)
```bash
# Install
pip install checkov

# Scan Terraform
checkov -d ./terraform/

# Scan Docker
checkov --framework dockerfile -f Dockerfile

# Scan Kubernetes
checkov -d ./k8s/

# Scan CloudFormation
checkov -d ./cloudformation/

# CI integration
checkov -d ./terraform/ --output junitxml --output-file results.xml
```

### Terrascan
```bash
terrascan scan -i terraform -d ./terraform/
terrascan scan -i k8s -d ./k8s/
terrascan scan -i docker -f Dockerfile
```

## Secure Terraform Patterns

### S3 Bucket (Secure)
```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data-${var.environment}"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.data_key.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_logging" "data" {
  bucket        = aws_s3_bucket.data.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}
```

### RDS (Secure)
```hcl
resource "aws_db_instance" "main" {
  engine               = "postgres"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100

  # Security
  storage_encrypted    = true                        # ✅ Encrypt at rest
  kms_key_id          = aws_kms_key.rds.arn
  publicly_accessible  = false                       # ✅ Not public
  multi_az            = true                          # ✅ High availability
  deletion_protection = true                          # ✅ Prevent accidental delete
  skip_final_snapshot = false

  # Network
  db_subnet_group_name   = aws_db_subnet_group.private.name
  vpc_security_group_ids = [aws_security_group.database.id]

  # Monitoring
  performance_insights_enabled = true
  monitoring_interval         = 60
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Credentials from Secrets Manager
  username = "admin"
  password = aws_secretsmanager_secret_version.db_password.secret_string
}
```

## IaC Security CI Pipeline
```yaml
iac-security:
  stage: validate
  script:
    - tfsec ./terraform/ --minimum-severity HIGH --format sarif -o tfsec.sarif
    - checkov -d ./terraform/ --output junitxml -o checkov.xml
    - checkov --framework dockerfile -f Dockerfile
  artifacts:
    reports:
      sast: [tfsec.sarif, checkov.xml]
```

## Checklist
- [ ] All IaC scanned in CI before merge
- [ ] No hardcoded secrets in Terraform/K8s manifests
- [ ] S3 buckets block public access by default
- [ ] RDS/databases not publicly accessible
- [ ] Encryption enabled for all storage resources
- [ ] IAM policies follow least privilege (no wildcards)
- [ ] Security groups restrict access to minimum necessary
- [ ] State files (terraform.tfstate) encrypted and access-controlled

# Cloud Security (AWS Focus)

## Shared Responsibility Model
```
AWS Responsibility: Physical, network, hypervisor, managed service infrastructure
Your Responsibility: OS, application, data, access management, encryption, network config
```

## IAM Best Practices

### Policy Structure
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-app-bucket",
        "arn:aws:s3:::my-app-bucket/*"
      ],
      "Condition": {
        "IpAddress": { "aws:SourceIp": "10.0.0.0/24" }
      }
    }
  ]
}
```

### IAM Rules
```
1. NEVER use root account for daily operations
2. Enable MFA on root and all IAM users
3. Create IAM roles for EC2/ECS (not access keys)
4. Use IAM roles for cross-account access (not shared keys)
5. Use permission boundaries to limit max permissions
6. Review IAM Access Analyzer findings weekly
7. Access keys: rotate every 90 days, delete unused
```

### Service Role Pattern (EC2/ECS)
```
EC2 Instance → Instance Profile → IAM Role → Policy
                                            → S3 read-only
                                            → Secrets Manager read
                                            → CloudWatch logs write
No access keys on the instance!
```

## VPC Security

```
VPC: 10.0.0.0/16
├── Public Subnet (10.0.1.0/24)
│   └── ALB, NAT Gateway
│   └── Security Group: 80/443 from 0.0.0.0/0
│
├── Private App Subnet (10.0.2.0/24)
│   └── ECS/EC2 instances
│   └── Security Group: 3000 from ALB-SG only
│   └── Outbound: NAT Gateway for package updates
│
├── Private Data Subnet (10.0.3.0/24)
│   └── RDS, ElastiCache
│   └── Security Group: 3306/6379 from App-SG only
│   └── No internet access (no NAT route)
│
└── Flow Logs → CloudWatch Logs (monitor all traffic)
```

## S3 Security

```json
// Bucket policy: block public access + enforce encryption
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    },
    {
      "Sid": "DenyHTTP",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    }
  ]
}
```

```bash
# Block all public access (account-wide)
aws s3control put-public-access-block \
  --account-id $ACCOUNT_ID \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

## Encryption

| Data State | Service | Default? | How to Enable |
| --- | --- | --- | --- |
| At rest (S3) | SSE-S3 or SSE-KMS | Optional | Bucket policy or CLI flag |
| At rest (RDS) | KMS encryption | Optional | Enable at creation |
| At rest (EBS) | KMS encryption | Optional | Enable at creation |
| In transit | TLS/HTTPS | Varies | Enforce via policy / ALB |

## Monitoring & Alerts

```
CloudTrail → Log ALL API calls → S3 bucket (encrypted, immutable)
GuardDuty → Threat detection → SNS → Email/Slack alert
Config → Compliance rules → Alert on non-compliant resources
Security Hub → Aggregated view of all security findings
```

## AWS Security Checklist
- [ ] Root account has MFA, no access keys
- [ ] IAM users have MFA enabled
- [ ] EC2/ECS use IAM roles, not access keys
- [ ] VPC has public/private subnet separation
- [ ] Security groups follow least privilege
- [ ] S3 buckets block public access by default
- [ ] Encryption enabled for all data at rest
- [ ] CloudTrail enabled in all regions
- [ ] GuardDuty enabled for threat detection
- [ ] VPC Flow Logs enabled
- [ ] Budget alerts configured

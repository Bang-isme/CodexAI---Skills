# GDPR - General Data Protection Regulation

## Scope
GDPR applies to any product handling personal data of EU/EEA residents, regardless of where the company or infrastructure is located.

## Core Definitions

| Term | Meaning | Example |
| --- | --- | --- |
| Personal data | Data that can identify a person | Name, email, IP, cookie ID |
| Special category data | Sensitive personal data | Health, biometrics, religion |
| Data subject | The individual user | Customer/account owner |
| Controller | Entity deciding purpose/means | Your company |
| Processor | Third party processing data for you | Cloud/email/payment vendors |
| Processing | Any operation on personal data | Collect, store, share, delete |

## Seven GDPR Principles

| Principle | Engineering Requirement |
| --- | --- |
| Lawfulness, fairness, transparency | Clear privacy notices and lawful basis tracking |
| Purpose limitation | Collect/use data only for declared purpose |
| Data minimization | Avoid unnecessary fields |
| Accuracy | Let users update/correct records |
| Storage limitation | Retention and deletion policy enforced |
| Integrity and confidentiality | Encryption, least privilege, monitoring |
| Accountability | Maintain records and audit evidence |

## Lawful Bases

| Basis | Typical Usage |
| --- | --- |
| Consent | Marketing emails, optional analytics cookies |
| Contract | Account creation, order fulfillment |
| Legal obligation | Tax/invoice retention |
| Legitimate interest | Fraud prevention, abuse monitoring |

## Required User Rights Implementation

### Right Of Access (Data Export)
```javascript
// GET /api/user/data-export
const exportUserData = async (req, res) => {
  const userId = req.user.id;
  const [user, orders, activities] = await Promise.all([
    User.findById(userId).select("-password -__v"),
    Order.find({ userId }),
    Activity.find({ userId }),
  ]);

  const payload = {
    exportDate: new Date().toISOString(),
    profile: user,
    orders,
    activityLog: activities,
  };

  res.setHeader("Content-Type", "application/json");
  res.setHeader("Content-Disposition", "attachment; filename=\"my-data.json\"");
  return res.json(payload);
};
```

### Right To Erasure (Delete/Anonymize)
```javascript
// DELETE /api/user/account
const deleteAccount = async (req, res) => {
  const userId = req.user.id;

  // 1) Anonymize core profile
  await User.findByIdAndUpdate(userId, {
    firstName: "[DELETED]",
    lastName: "[DELETED]",
    email: `deleted_${userId}@anonymized.local`,
    phone: null,
    isDeleted: true,
    deletedAt: new Date(),
  });

  // 2) Delete non-essential records
  await Promise.all([
    Session.deleteMany({ userId }),
    Activity.deleteMany({ userId }),
  ]);

  // 3) Preserve legal records in anonymized form
  await Order.updateMany(
    { userId },
    { $set: { customerName: "[DELETED]", customerEmail: "[DELETED]" } }
  );

  // 4) Audit trail
  await AuditLog.create({
    action: "GDPR_DELETION",
    userId,
    executedAt: new Date(),
  });

  return res.json({ message: "Deletion request accepted" });
};
```

### Right To Rectification
- Provide profile update endpoint with validation and audit log.

### Right To Portability
- Export machine-readable formats (JSON, CSV), consistent schema, and clear field labels.

## Consent Management Pattern
```javascript
const consentSchema = new mongoose.Schema({
  userId: { type: mongoose.Types.ObjectId, ref: "User", required: true, index: true },
  analytics: { type: Boolean, default: false },
  marketing: { type: Boolean, default: false },
  functional: { type: Boolean, default: true },
  policyVersion: { type: String, required: true },
  capturedAt: { type: Date, default: Date.now },
  source: { type: String, enum: ["web", "mobile", "api"], default: "web" },
});
```

## Data Breach Timeline
- Detect and classify incident severity quickly.
- Notify supervisory authority within 72 hours when required.
- Notify affected users when high risk to rights/freedoms exists.
- Preserve forensic evidence and incident timeline.

## Processor Management
- Sign Data Processing Agreement (DPA) with each processor.
- Track data residency and transfer mechanisms.
- Verify subprocessors and support deletion/export requests.

## Developer Checklist
- [ ] Every data field has purpose and retention period
- [ ] Access/delete/export endpoints implemented and tested
- [ ] Consent state persisted with policy version
- [ ] Sensitive data encrypted in transit and at rest
- [ ] Logs avoid raw PII unless strictly required
- [ ] Breach response runbook and contacts documented

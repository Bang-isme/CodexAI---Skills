# Multi-Tenancy Patterns

## Scope

Use when building SaaS apps that serve multiple organizations in shared infrastructure.

## Strategy Decision

| Strategy | Isolation | Complexity | Cost | Best For |
| --- | --- | --- | --- | --- |
| Shared DB + tenant column | Low | Low | Low | Early-stage SaaS |
| Shared DB + separate schemas | Medium | Medium | Medium | Mid-scale compliance needs |
| Separate databases | High | High | High | Enterprise strict isolation |

## Shared DB + Tenant Column

```javascript
const tenantMiddleware = (req, res, next) => {
  req.tenantId = req.user?.organizationId;
  if (!req.tenantId) return next(Forbidden('No tenant context'));
  return next();
};

const invoiceSchema = new mongoose.Schema({
  tenantId: { type: String, required: true, index: true },
  number: String,
  amount: Number,
});

const getInvoices = async (req, res) => {
  const invoices = await Invoice.find({ tenantId: req.tenantId });
  res.json({ data: invoices });
};
```

## Safety Rules

- Never query tenant data without tenant filter.
- Prefer middleware/base repository to auto-attach tenantId.
- Unique constraints must include tenantId.
- Validate isolation with tests across 2+ tenants.
- Super-admin bypass must be explicit and audited.

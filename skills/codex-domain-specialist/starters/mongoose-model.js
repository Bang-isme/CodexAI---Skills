// ============================================
// MONGOOSE MODEL STARTER — Tenant-Scoped + Keyset Cursor + Explicit DTO
// ============================================
import mongoose from 'mongoose';

const employeeSchema = new mongoose.Schema(
  {
    tenantId: { type: String, required: true, index: true },
    employeeId: { type: String, required: true, trim: true },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    email: { type: String, required: true, lowercase: true, trim: true },
    departmentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Department' },
    salaryCents: { type: Number, required: true, min: 0, default: 0 },
    role: { type: String, enum: ['user', 'manager', 'admin'], default: 'user' },
    isActive: { type: Boolean, default: true },
  },
  {
    timestamps: true,
    optimisticConcurrency: true,
  }
);

// Workload-driven compound indexes (ESR: Equality -> Sort -> Range)
employeeSchema.index({ tenantId: 1, email: 1 }, { unique: true });
employeeSchema.index({ tenantId: 1, employeeId: 1 }, { unique: true });
employeeSchema.index({ tenantId: 1, departmentId: 1, isActive: 1, _id: -1 });

export const toEmployeeDto = (doc) => ({
  id: String(doc._id || doc.id),
  tenantId: String(doc.tenantId),
  employeeId: doc.employeeId,
  firstName: doc.firstName,
  lastName: doc.lastName,
  fullName: `${doc.firstName} ${doc.lastName}`.trim(),
  email: doc.email,
  departmentId: doc.departmentId ? String(doc.departmentId) : null,
  salaryCents: Number(doc.salaryCents ?? 0),
  role: doc.role,
  isActive: Boolean(doc.isActive),
  createdAt: doc.createdAt instanceof Date ? doc.createdAt.toISOString() : doc.createdAt,
});

// Keyset cursor pagination (never use skip() on large collections)
employeeSchema.statics.listByDepartmentCursor = async function ({
  tenantId,
  departmentId,
  cursor,
  limit = 25,
}) {
  const safeLimit = Math.min(Math.max(Number(limit) || 25, 1), 100);
  const query = {
    tenantId,
    departmentId,
    isActive: true,
    ...(cursor ? { _id: { $lt: new mongoose.Types.ObjectId(cursor) } } : {}),
  };

  const rows = await this.find(query)
    .sort({ _id: -1 })
    .limit(safeLimit + 1)
    .lean();

  const hasMore = rows.length > safeLimit;
  const slice = hasMore ? rows.slice(0, safeLimit) : rows;
  const nextCursor = hasMore ? String(slice[slice.length - 1]._id) : null;

  return {
    data: slice.map(toEmployeeDto),
    pagination: { limit: safeLimit, nextCursor, hasMore },
  };
};

export const Employee = mongoose.model('Employee', employeeSchema);

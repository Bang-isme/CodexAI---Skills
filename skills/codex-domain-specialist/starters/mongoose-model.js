// ============================================
// MONGOOSE MODEL STARTER
// ============================================
import mongoose from 'mongoose';

const employeeSchema = new mongoose.Schema(
  {
    employeeId: { type: String, required: true, unique: true, index: true },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    departmentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Department', index: true },
    role: { type: String, enum: ['user', 'manager', 'admin'], default: 'user' },
    isActive: { type: Boolean, default: true, index: true },
    metadata: { type: Map, of: mongoose.Schema.Types.Mixed },
  },
  {
    timestamps: true, // createdAt, updatedAt
    toJSON: { virtuals: true }, // include virtuals in JSON
    toObject: { virtuals: true },
  }
);

// --- Virtuals ---
employeeSchema.virtual('fullName').get(function () {
  return `${this.firstName} ${this.lastName}`;
});

employeeSchema.virtual('department', {
  ref: 'Department',
  localField: 'departmentId',
  foreignField: '_id',
  justOne: true,
});

// --- Indexes (compound for common queries) ---
employeeSchema.index({ departmentId: 1, isActive: 1 });
employeeSchema.index({ lastName: 1, firstName: 1 });
employeeSchema.index({ email: 1 }, { unique: true });

// --- Methods (instance) ---
employeeSchema.methods.softDelete = function () {
  this.isActive = false;
  return this.save();
};

// --- Statics (model) ---
employeeSchema.statics.findActive = function (filter = {}) {
  return this.find({ ...filter, isActive: true });
};

employeeSchema.statics.findByDepartment = function (departmentId, options = {}) {
  const { page = 1, limit = 20 } = options;
  return this.find({ departmentId, isActive: true })
    .skip((page - 1) * limit)
    .limit(limit)
    .populate('department')
    .lean();
};

// --- Middleware ---
employeeSchema.pre('save', function (next) {
  if (this.isModified('email')) {
    this.email = this.email.toLowerCase().trim();
  }
  next();
});

export const Employee = mongoose.model('Employee', employeeSchema);

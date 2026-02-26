// ============================================
// SEQUELIZE MIGRATION STARTER - Safe Patterns
// ============================================
'use strict';

/**
 * Pattern 1: SAFE ADDITIVE - Add optional column
 */
module.exports = {
  async up(queryInterface, Sequelize) {
    // Pre-check: avoid error if column exists (idempotent)
    const tableDesc = await queryInterface.describeTable('employees');
    if (!tableDesc.middle_name) {
      await queryInterface.addColumn('employees', 'middle_name', {
        type: Sequelize.STRING(100),
        allowNull: true, // always nullable first
        defaultValue: null,
      });
    }

    // Add index
    await queryInterface.addIndex('employees', ['department_id', 'is_active'], {
      name: 'idx_employees_dept_active',
      where: { is_active: true }, // partial index for performance
    });
  },

  async down(queryInterface) {
    await queryInterface.removeIndex('employees', 'idx_employees_dept_active');
    await queryInterface.removeColumn('employees', 'middle_name');
  },
};

/**
 * Pattern 2: PHASED - Add required column (3-step)
 *
 * Migration 1: Add column as NULLABLE
 *   await queryInterface.addColumn('orders', 'tracking_code', {
 *     type: Sequelize.STRING(50), allowNull: true,
 *   });
 *
 * Migration 2: Backfill data
 *   await queryInterface.sequelize.query(
 *     `UPDATE orders SET tracking_code = CONCAT('TRK-', id) WHERE tracking_code IS NULL`
 *   );
 *
 * Migration 3: Set NOT NULL after backfill confirmed
 *   await queryInterface.changeColumn('orders', 'tracking_code', {
 *     type: Sequelize.STRING(50), allowNull: false,
 *   });
 */

/**
 * Pattern 3: LARGE TABLE - Chunked backfill (prevent lock timeouts)
 */
const backfillChunked = async (queryInterface, tableName, updateSQL, batchSize = 5000) => {
  let affected = batchSize;
  let totalUpdated = 0;

  while (affected >= batchSize) {
    const [, metadata] = await queryInterface.sequelize.query(`${updateSQL} LIMIT ${batchSize}`);
    affected = metadata?.affectedRows ?? metadata ?? 0;
    totalUpdated += affected;

    if (affected > 0) {
      // Small delay to reduce lock contention
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }

  return totalUpdated;
};

// Usage:
// await backfillChunked(queryInterface, 'employees',
//   `UPDATE employees SET annual_earnings = 0 WHERE annual_earnings IS NULL`
// );

/**
 * Pattern 4: CREATE TABLE with constraints
 */
const createTableExample = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('earnings_summary', {
      id: { type: Sequelize.INTEGER, primaryKey: true, autoIncrement: true },
      employee_id: {
        type: Sequelize.STRING(20),
        allowNull: false,
        references: { model: 'employees', key: 'employee_id' },
        onUpdate: 'CASCADE',
        onDelete: 'RESTRICT',
      },
      year: { type: Sequelize.INTEGER, allowNull: false },
      total: { type: Sequelize.DECIMAL(12, 2), allowNull: false, defaultValue: 0 },
      computed_at: { type: Sequelize.DATE, defaultValue: Sequelize.literal('CURRENT_TIMESTAMP') },
    });

    // Composite unique constraint
    await queryInterface.addConstraint('earnings_summary', {
      fields: ['employee_id', 'year'],
      type: 'unique',
      name: 'uq_earnings_emp_year',
    });

    // Performance index
    await queryInterface.addIndex('earnings_summary', ['year', 'employee_id'], {
      name: 'idx_earnings_year_emp',
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('earnings_summary');
  },
};

/**
 * Pattern 5: RENAME COLUMN (safe - no data loss)
 */
const renameExample = {
  async up(queryInterface) {
    await queryInterface.renameColumn('employees', 'fname', 'first_name');
  },

  async down(queryInterface) {
    await queryInterface.renameColumn('employees', 'first_name', 'fname');
  },
};

/**
 * SAFETY RULES:
 * 1. Always write both up() and down()
 * 2. Never DROP column in up() without backup plan
 * 3. Add columns as NULLABLE first, backfill, then constrain
 * 4. Large tables (>100k rows): use chunked backfill
 * 5. Test migration on staging with production-size data
 * 6. Run down() in dev to verify rollback before deploying
 */

// ============================================
// SEQUELIZE / SQL MIGRATION STARTER — Zero-Downtime Expand-and-Contract
// ============================================

/**
 * Pattern 1: SAFE ADDITIVE (Expand Phase) + CONCURRENT INDEX
 * Note: CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
 */
export const expandEmployeesMiddleNameMigration = {
  async up(queryInterface, Sequelize) {
    const tableDesc = await queryInterface.describeTable('employees');
    if (!tableDesc.middle_name) {
      await queryInterface.addColumn('employees', 'middle_name', {
        type: Sequelize.STRING(100),
        allowNull: true,
        defaultValue: null,
      });
    }

    await queryInterface.sequelize.query(
      'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_employees_dept_active ON employees (tenant_id, department_id) WHERE is_active = true;'
    );
  },

  async down(queryInterface) {
    await queryInterface.sequelize.query('DROP INDEX CONCURRENTLY IF EXISTS idx_employees_dept_active;');
    await queryInterface.removeColumn('employees', 'middle_name');
  },
};

/**
 * Pattern 2: KEYSET-CHUNKED BACKFILL (Prevent Table Lock & Replication Lag)
 */
export const runKeysetBackfill = async (sequelize, { batchSize = 1000, pauseMs = 50 } = {}) => {
  let lastId = '00000000-0000-0000-0000-000000000000';
  let totalUpdated = 0;

  while (true) {
    const [rows] = await sequelize.query(
      `SELECT id
       FROM orders
       WHERE id > :lastId AND tracking_code IS NULL
       ORDER BY id ASC
       LIMIT :batchSize`,
      { replacements: { lastId, batchSize } }
    );

    if (!Array.isArray(rows) || rows.length === 0) break;

    const ids = rows.map((r) => r.id);
    await sequelize.query(
      `UPDATE orders
       SET tracking_code = CONCAT('TRK-', id)
       WHERE id IN (:ids) AND tracking_code IS NULL`,
      { replacements: { ids } }
    );

    lastId = rows[rows.length - 1].id;
    totalUpdated += rows.length;
    await new Promise((resolve) => setTimeout(resolve, pauseMs));
  }

  return { totalUpdated, lastCursor: lastId };
};

/**
 * Pattern 3: CREATE TABLE with Integer Cents (BIGINT) & Tenant Isolation
 */
export const createEarningsSummaryMigration = {
  async up(queryInterface, Sequelize) {
    await queryInterface.createTable('earnings_summary', {
      id: { type: Sequelize.STRING(36), primaryKey: true, allowNull: false },
      tenant_id: { type: Sequelize.STRING(36), allowNull: false },
      employee_id: {
        type: Sequelize.STRING(36),
        allowNull: false,
        references: { model: 'employees', key: 'id' },
        onUpdate: 'CASCADE',
        onDelete: 'RESTRICT',
      },
      year: { type: Sequelize.INTEGER, allowNull: false },
      total_cents: { type: Sequelize.BIGINT, allowNull: false, defaultValue: 0 },
      version: { type: Sequelize.INTEGER, allowNull: false, defaultValue: 1 },
      computed_at: { type: Sequelize.DATE, allowNull: false, defaultValue: Sequelize.literal('CURRENT_TIMESTAMP') },
    });

    await queryInterface.addConstraint('earnings_summary', {
      fields: ['tenant_id', 'employee_id', 'year'],
      type: 'unique',
      name: 'uq_earnings_tenant_emp_year',
    });
  },

  async down(queryInterface) {
    await queryInterface.dropTable('earnings_summary');
  },
};

export default expandEmployeesMiddleNameMigration;

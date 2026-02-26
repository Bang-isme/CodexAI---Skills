# Data Migration & Seed Patterns

## Core Principles

- Migrations are code and must be version-controlled.
- Every migration has `up()` and `down()` paths.
- Rehearse on staging with production-like data volumes.
- Seed scripts are for development/testing, not production bootstrapping.

## Seed Script Pattern

```javascript
const seedData = async () => {
  if (process.env.NODE_ENV === 'production') {
    console.error('Cannot seed production. Aborting.');
    process.exit(1);
  }

  console.log('Seeding database...');

  await Promise.all([
    User.deleteMany({}),
    Department.deleteMany({}),
  ]);

  const departments = await Department.insertMany([
    { name: 'Engineering' },
    { name: 'Marketing' },
    { name: 'Finance' },
  ]);

  const users = [];
  for (let i = 0; i < 100; i += 1) {
    users.push({
      firstName: `User${i}`,
      lastName: `Test${i}`,
      email: `user${i}@test.com`,
      password: await bcrypt.hash('Test1234!', 10),
      departmentId: departments[i % departments.length]._id,
      role: i === 0 ? 'admin' : 'user',
    });
  }

  await User.insertMany(users);
  console.log(`Seeded: ${departments.length} departments, ${users.length} users`);
};
```

## ETL / Backfill Pattern (Production-Safe)

```javascript
const backfill = async () => {
  const BATCH_SIZE = 1000;
  let processed = 0;
  const cursor = Employee.find({ annualEarnings: null }).lean().cursor();

  for await (const emp of cursor) {
    const earnings = await calculateEarnings(emp.employeeId);
    await Employee.updateOne(
      { _id: emp._id },
      { annualEarnings: earnings, annualEarningsYear: 2026 }
    );

    processed += 1;
    if (processed % BATCH_SIZE === 0) {
      console.log(`Processed ${processed}...`);
      await new Promise((r) => setTimeout(r, 50));
    }
  }

  console.log(`Backfilled ${processed} employees`);
};
```

## Safety Rules

- Run on staging first with production-like volume.
- Process in chunks for large tables/collections.
- Log progress periodically.
- Throttle to protect primary workload.
- Use transactions when atomicity is required.
- Keep rollback/undo strategy documented.

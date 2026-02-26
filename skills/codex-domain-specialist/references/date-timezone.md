# Date and Timezone Patterns

## Scope
Use when handling dates, times, scheduling, and timezone-sensitive calculations.

## Core Principle
Store UTC, display local. Persist timestamps in UTC in the database, then convert to user timezone for UI.

## Day.js Setup

```javascript
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import relativeTime from "dayjs/plugin/relativeTime";
import isBetween from "dayjs/plugin/isBetween";

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(relativeTime);
dayjs.extend(isBetween);
```

## Common Operations

```javascript
dayjs.utc(); // current UTC
dayjs.utc("2026-02-27T10:00:00Z").tz("Asia/Ho_Chi_Minh");

dayjs(date).format("DD/MM/YYYY HH:mm");
dayjs(date).format("MMM D, YYYY");

dayjs(date).fromNow();
dayjs(date).toNow();

dayjs().add(7, "day");
dayjs().subtract(1, "month");
dayjs().startOf("month");
dayjs().endOf("week");

dayjs(a).isBefore(b);
dayjs(a).isAfter(b);
dayjs(date).isBetween("2026-01-01", "2026-12-31");

dayjs(end).diff(start, "day");
dayjs(end).diff(start, "month");
```

## Storage Pattern

```javascript
const schema = new mongoose.Schema({
  createdAt: { type: Date, default: () => new Date() },
  scheduledAt: { type: Date },
  birthDate: { type: Date },
});
```

- MongoDB: store `Date` in UTC.
- PostgreSQL: prefer `TIMESTAMPTZ`.
- MySQL: enforce UTC at application level.

## Timezone-Aware Query

```javascript
const userTz = "Asia/Ho_Chi_Minh";
const startOfMonth = dayjs().tz(userTz).startOf("month").utc().toDate();
const endOfMonth = dayjs().tz(userTz).endOf("month").utc().toDate();

const query = { createdAt: { $gte: startOfMonth, $lte: endOfMonth } };
```

## Birthday Alert Pattern

```javascript
const currentMonth = dayjs().month() + 1;
const employees = await Employee.aggregate([
  { $addFields: { birthMonth: { $month: "$birthDate" } } },
  { $match: { birthMonth: currentMonth } },
  { $sort: { birthDate: 1 } },
]);
```

## Pitfalls
- Do not store localized display strings.
- Do not compare date strings directly.
- Do not store only timezone offsets (`+07:00`); store timezone names.
- Use ISO 8601 in APIs (`2026-02-27T10:00:00Z`).

# MongoDB Aggregation Pipeline Patterns

## Scope
Use for complex queries: grouping, joining, transforming, and analytics.

## Stage Reference

| Stage | Purpose | Example |
| --- | --- | --- |
| `$match` | Filter documents | `{ status: "active" }` |
| `$group` | Aggregate by key | `{ _id: "$dept", total: { $sum: 1 } }` |
| `$project` | Select and compute fields | `{ fullName: { $concat: [...] } }` |
| `$sort` | Order results | `{ total: -1 }` |
| `$limit` / `$skip` | Pagination | `{ $skip: 20 }, { $limit: 10 }` |
| `$lookup` | Join collections | Employees + departments |
| `$unwind` | Flatten arrays | explode `items` |
| `$addFields` | Add computed fields | `{ birthMonth: { $month: "$birthDate" } }` |
| `$facet` | Parallel pipelines | counts + data |
| `$bucket` | Range grouping | salary bands |

## Dashboard Summary Example

```javascript
const dashboardSummary = await Employee.aggregate([
  { $match: { isActive: true } },
  {
    $facet: {
      totalCount: [{ $count: "count" }],
      byDepartment: [
        { $group: { _id: "$departmentId", count: { $sum: 1 }, avgSalary: { $avg: "$salary" } } },
        { $lookup: { from: "departments", localField: "_id", foreignField: "_id", as: "dept" } },
        { $unwind: "$dept" },
        { $project: { department: "$dept.name", count: 1, avgSalary: { $round: ["$avgSalary", 2] } } },
        { $sort: { count: -1 } },
      ],
    },
  },
]);
```

## Lookup Pattern

```javascript
{
  $lookup: {
    from: "departments",
    localField: "departmentId",
    foreignField: "_id",
    as: "department"
  }
},
{ $unwind: { path: "$department", preserveNullAndEmptyArrays: true } }
```

## Monthly Trend Pattern

```javascript
const monthlyTrend = await Order.aggregate([
  { $match: { createdAt: { $gte: startOfYear } } },
  {
    $group: {
      _id: { year: { $year: "$createdAt" }, month: { $month: "$createdAt" } },
      revenue: { $sum: "$total" },
      orders: { $sum: 1 },
      avgOrderValue: { $avg: "$total" },
    },
  },
  { $sort: { "_id.year": 1, "_id.month": 1 } },
]);
```

## Pagination with Count

```javascript
const result = await Employee.aggregate([
  { $match: query },
  {
    $facet: {
      data: [{ $sort: { lastName: 1 } }, { $skip: (page - 1) * limit }, { $limit: limit }],
      total: [{ $count: "count" }],
    },
  },
]);
```

## Performance Rules
- Put `$match` as early as possible.
- Index fields used in `$match` and `$sort`.
- Use `$project` early to drop unused fields.
- Use `$lookup` carefully for large collections.
- Use `allowDiskUse: true` for large pipelines.
- Profile using `explain("executionStats")`.

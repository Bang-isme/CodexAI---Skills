# Search & Filter Patterns

## Core Principle

Filters should be URL-driven (bookmarkable/shareable), debounced, and validated.

## URL-Driven Filters (Frontend)

```jsx
import { useSearchParams } from 'react-router-dom';

function useFilters(defaults = {}) {
  const [params, setParams] = useSearchParams();
  const filters = {
    search: params.get('search') || defaults.search || '',
    department: params.get('department') || '',
    status: params.get('status') || '',
    sort: params.get('sort') || defaults.sort || 'createdAt',
    order: params.get('order') || 'desc',
    page: parseInt(params.get('page') || '1', 10),
  };

  const setFilter = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== 'page') next.set('page', '1');
    setParams(next);
  };

  const clearAll = () => setParams({});
  return { filters, setFilter, clearAll };
}
```

## Debounced Search

```jsx
import { useState, useEffect } from 'react';

function useDebouncedValue(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
```

## Backend Filter Builder

```javascript
const buildMongoQuery = (filters) => {
  const query = {};

  if (filters.search) {
    const regex = new RegExp(escapeRegex(filters.search), 'i');
    query.$or = [{ firstName: regex }, { lastName: regex }, { employeeId: regex }];
  }

  if (filters.department) query.departmentId = filters.department;
  if (filters.status) query.isActive = filters.status === 'active';
  if (filters.gender) query.gender = filters.gender;

  return query;
};

const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
```

## Faceted Search

```javascript
const facets = await Employee.aggregate([
  { $match: baseQuery },
  {
    $facet: {
      byDepartment: [{ $group: { _id: '$departmentId', count: { $sum: 1 } } }],
      byGender: [{ $group: { _id: '$gender', count: { $sum: 1 } } }],
      byStatus: [{ $group: { _id: '$isActive', count: { $sum: 1 } } }],
      total: [{ $count: 'count' }],
    },
  },
]);
```

## UI Pattern

- Show active filter count: `Filters (3)`.
- Show removable chips for each active filter.
- Provide clear-all action.
- Use collapsible filter panel for large filter sets.

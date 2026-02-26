# Data Visualization Patterns

## Scope
Use when building charts, graphs, and dashboards with visual data representation.

## Library Decision

| Library | Best For | Size | Learning Curve |
| --- | --- | --- | --- |
| Chart.js | Simple charts, quick setup | ~60KB | Low |
| Recharts | React dashboards, declarative | ~120KB | Low |
| D3.js | Custom and complex visualizations | ~80KB | High |
| Apache ECharts | Enterprise dashboards, large datasets | ~300KB | Medium |
| Visx | React + D3 composable primitives | Modular | Medium |

## Recharts Setup (React Recommended)

```jsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

function RevenueChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
        <XAxis dataKey="month" stroke="var(--text-secondary)" fontSize={12} />
        <YAxis
          stroke="var(--text-secondary)"
          fontSize={12}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface-0)",
            border: "1px solid var(--border-light)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "var(--shadow-md)",
          }}
          formatter={(value) => [`$${value.toLocaleString()}`, ""]}
        />
        <Legend />
        <Line type="monotone" dataKey="revenue" stroke="var(--brand-600)" strokeWidth={2} />
        <Line type="monotone" dataKey="expenses" stroke="var(--error)" strokeWidth={2} strokeDasharray="5 5" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

## Chart Type Decision

| Data | Chart Type | When |
| --- | --- | --- |
| Trend over time | Line chart | Revenue by month, user growth |
| Category comparison | Vertical bar chart | Sales by department |
| Part of whole | Donut or pie chart | Budget allocation (max 6 slices) |
| Distribution | Histogram | Age ranges, salary bands |
| Correlation | Scatter plot | Hours vs productivity |
| Hierarchy | Treemap | File sizes, market cap |
| Flow | Sankey diagram | User journey, conversion funnel |
| Single KPI | Stat card + sparkline | Total revenue, active users |

## Dashboard Layout Pattern

```jsx
function Dashboard() {
  return (
    <div className="page">
      <div className="stats-grid">{/* KPI cards */}</div>
      <div className="content-grid">
        <div className="card">{/* Revenue chart */}</div>
        <div className="card">{/* Category chart */}</div>
      </div>
      <div className="content-grid">
        <div className="card" style={{ gridColumn: "span 2" }}>{/* Table */}</div>
        <div className="card">{/* Donut chart */}</div>
      </div>
    </div>
  );
}
```

## Color Palettes

```javascript
const sequential = ["#ecfdf5", "#a7f3d0", "#34d399", "#059669", "#065f46"];
const categorical = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];
const diverging = { positive: "#10b981", negative: "#ef4444", neutral: "#6b7280" };
```

## Rules
- Always use `ResponsiveContainer`; avoid fixed widths.
- Limit pie and donut charts to 6 slices; group the rest as `Other`.
- Format large numbers (`1,234,567` -> `1.2M`).
- Show loading skeleton while fetching data.
- Provide accessible table fallback for screen readers.
- Use animation on first load only, not on every refresh.

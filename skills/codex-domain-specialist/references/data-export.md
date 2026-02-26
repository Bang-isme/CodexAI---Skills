# Data Export Patterns

## Scope
Use when exporting data to CSV, Excel, or PDF from backend or frontend.

## CSV Export (Backend Streaming)

```javascript
const exportCsv = async (req, res) => {
  const query = buildFilter(req.query);

  res.setHeader("Content-Type", "text/csv; charset=utf-8");
  res.setHeader("Content-Disposition", `attachment; filename="employees-${Date.now()}.csv"`);
  res.write("\ufeff");
  res.write("Employee ID,First Name,Last Name,Email,Department,Hire Date\n");

  const cursor = Employee.find(query).populate("department").lean().cursor();
  for await (const emp of cursor) {
    const row = [
      emp.employeeId,
      escapeCsv(emp.firstName),
      escapeCsv(emp.lastName),
      emp.email,
      emp.department?.name || "",
      dayjs(emp.hireDate).format("YYYY-MM-DD"),
    ].join(",");
    res.write(row + "\n");
  }

  res.end();
};

const escapeCsv = (value) => {
  if (value == null) return "";
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
};
```

## Excel Export (ExcelJS)

```javascript
import ExcelJS from "exceljs";

const exportExcel = async (req, res) => {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet("Employees");

  sheet.columns = [
    { header: "ID", key: "employeeId", width: 15 },
    { header: "Name", key: "name", width: 25 },
    { header: "Email", key: "email", width: 30 },
    { header: "Department", key: "department", width: 20 },
  ];

  sheet.getRow(1).font = { bold: true, size: 12 };
  const employees = await Employee.find().populate("department").lean();
  employees.forEach((emp) =>
    sheet.addRow({
      employeeId: emp.employeeId,
      name: `${emp.firstName} ${emp.lastName}`,
      email: emp.email,
      department: emp.department?.name || "",
    })
  );

  res.setHeader("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
  res.setHeader("Content-Disposition", `attachment; filename="employees-${Date.now()}.xlsx"`);
  await workbook.xlsx.write(res);
  res.end();
};
```

## Frontend CSV Download

```javascript
const downloadCsv = (data, columns, filename) => {
  const header = columns.map((c) => c.label).join(",");
  const rows = data.map((row) => columns.map((c) => escapeCsv(row[c.key])).join(","));
  const csv = "\ufeff" + [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
};
```

## Rules
- Stream large exports; avoid loading entire dataset into memory.
- Add BOM (`\ufeff`) for Excel UTF-8 CSV compatibility.
- Escape commas, quotes, and newlines.
- Enforce export limits (for example 50k rows) or switch to background jobs.
- Log export activity for audit.
- Remove sensitive fields before exporting.

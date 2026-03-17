# Vietnamese Typography & Text Handling

## Scope and Triggers

Use this reference when:
- Building UI for Vietnamese-speaking users
- Working with Vietnamese text data (names, addresses, content)
- Setting up i18n with `vi` locale
- Handling diacritics (dấu) in search, sort, or display
- Configuring database collation for Vietnamese text

## Recommended Fonts (Google Fonts, Full Vietnamese Support)

### Primary Choices

| Font | Style | Best For | Import |
| --- | --- | --- | --- |
| **Be Vietnam Pro** | Sans-serif | Vietnamese-first projects | `family=Be+Vietnam+Pro:wght@300;400;500;600;700` |
| **Nunito** | Rounded sans | Friendly UI, dashboards | `family=Nunito:wght@300;400;600;700` |
| **Source Sans 3** | Sans-serif | Enterprise, long-form text | `family=Source+Sans+3:wght@300;400;600;700` |
| **Montserrat** | Geometric sans | Modern headings + body | `family=Montserrat:wght@300;400;500;600;700` |
| **Open Sans** | Humanist sans | Universal readability | `family=Open+Sans:wght@300;400;600;700` |

### Monospace (Code Blocks)

| Font | Import |
| --- | --- |
| **JetBrains Mono** | `family=JetBrains+Mono:wght@400;500;700` |
| **Fira Code** | `family=Fira+Code:wght@400;500;700` |

### Implementation

```html
<!-- Always specify Vietnamese subset -->
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap&subset=vietnamese" rel="stylesheet">
```

```css
:root {
  --font-family-vi: 'Be Vietnam Pro', 'Nunito', 'Source Sans 3', system-ui, sans-serif;
  --font-family-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

body {
  font-family: var(--font-family-vi);
}
```

### Font fallback stack rule

Always include a Vietnamese-capable fallback. System fonts on Windows (`Segoe UI`), macOS (`SF Pro`), and Linux (`Noto Sans`) support Vietnamese, so `system-ui` is a safe fallback.

## Encoding Checklist

### HTML

```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
```

### Database

```sql
-- MySQL / MariaDB
CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- PostgreSQL (default UTF-8, verify collation)
CREATE DATABASE mydb ENCODING 'UTF8' LC_COLLATE 'vi_VN.UTF-8';
```

```javascript
// MongoDB (default UTF-8, set collation for sorting)
db.createCollection('users', {
  collation: { locale: 'vi', strength: 1 }
});

// Mongoose schema with Vietnamese collation
const userSchema = new Schema({ name: String });
userSchema.index({ name: 1 }, { collation: { locale: 'vi' } });
```

### API Headers

```javascript
// Express.js
app.use((req, res, next) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  next();
});
```

### File I/O

```javascript
// Node.js - always specify utf-8
fs.readFileSync(path, { encoding: 'utf-8' });
fs.writeFileSync(path, data, { encoding: 'utf-8' });
```

## Vietnamese Text Processing

### Accent-Insensitive Search (Remove Diacritics)

```javascript
/**
 * Remove Vietnamese diacritics for search normalization.
 * "Nguyễn Văn Ân" → "nguyen van an"
 */
function removeViDiacritics(str) {
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .trim();
}

// Usage: search matching
const searchNormalized = removeViDiacritics(searchTerm);
const results = items.filter(item =>
  removeViDiacritics(item.name).includes(searchNormalized)
);
```

### MongoDB Text Search with Vietnamese

```javascript
// Create text index with Vietnamese language (not supported natively)
// Use accent-insensitive approach instead:
userSchema.add({ nameSearch: String }); // normalized field

userSchema.pre('save', function () {
  this.nameSearch = removeViDiacritics(this.name);
});

// Query
const q = removeViDiacritics(searchInput);
const results = await User.find({ nameSearch: { $regex: q, $options: 'i' } });
```

### Vietnamese Sorting

```javascript
// JavaScript Intl collation
const sorted = names.sort((a, b) =>
  a.localeCompare(b, 'vi', { sensitivity: 'base' })
);

// MongoDB query with Vietnamese collation
db.collection('users')
  .find({})
  .collation({ locale: 'vi' })
  .sort({ name: 1 });
```

### Vietnamese Date/Number Formatting

```javascript
// Date
new Intl.DateTimeFormat('vi-VN', {
  year: 'numeric', month: 'long', day: 'numeric'
}).format(date);
// → "28 tháng 2, 2026"

// Currency
new Intl.NumberFormat('vi-VN', {
  style: 'currency', currency: 'VND'
}).format(amount);
// → "1.500.000 ₫"

// Number (Vietnamese uses dot for thousands, comma for decimals)
new Intl.NumberFormat('vi-VN').format(1500000.5);
// → "1.500.000,5"
```

## Data Export with Vietnamese

### CSV Export (BOM for Excel)

```javascript
// Add UTF-8 BOM so Excel opens Vietnamese correctly
const BOM = '\uFEFF';
const csvContent = BOM + generateCSV(data);

res.setHeader('Content-Type', 'text/csv; charset=utf-8');
res.setHeader('Content-Disposition', 'attachment; filename="bao-cao.csv"');
res.send(csvContent);
```

### Excel Export (exceljs)

```javascript
const workbook = new ExcelJS.Workbook();
workbook.creator = 'System';
// exceljs handles UTF-8 natively, Vietnamese works out of the box
```

## SEO for Vietnamese Content

```html
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="description" content="Mô tả trang bằng tiếng Việt">
  <link rel="alternate" hreflang="vi" href="https://example.com/vi/">
  <link rel="alternate" hreflang="en" href="https://example.com/en/">
</head>
```

## Anti-Patterns

1. ❌ Bad: Using fonts without Vietnamese subset (`Inter` default may miss some glyphs).
   ✅ Good: Use `Be Vietnam Pro` or explicitly request `&subset=vietnamese`.

2. ❌ Bad: Storing Vietnamese in `latin1` / `utf8` (3-byte MySQL charset).
   ✅ Good: Use `utf8mb4` with `utf8mb4_unicode_ci` collation.

3. ❌ Bad: Searching Vietnamese text with exact match (misses diacritics variants).
   ✅ Good: Normalize with `removeViDiacritics()` for search, keep original for display.

4. ❌ Bad: Exporting CSV without BOM — Excel shows mojibake for Vietnamese.
   ✅ Good: Prepend `\uFEFF` BOM to CSV output.

5. ❌ Bad: Sorting Vietnamese with default `Array.sort()`.
   ✅ Good: Use `localeCompare('vi')` or database collation `locale: 'vi'`.

6. ❌ Bad: Hardcoding date/number format (MM/DD/YYYY, 1,500,000.00).
   ✅ Good: Use `Intl.DateTimeFormat('vi-VN')` and `Intl.NumberFormat('vi-VN')`.

## Cross-References

- `i18n-patterns.md` for multi-language setup.
- `frontend-rules.md` for typography scale and font tokens.
- `data-export.md` for CSV/Excel export patterns.
- `database-rules.md` for collation and encoding setup.
- `seo-rules.md` for metadata and hreflang patterns.
- `search-filter.md` for search normalization patterns.

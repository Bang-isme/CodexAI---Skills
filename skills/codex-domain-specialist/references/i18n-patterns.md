# i18n Patterns

Internationalization patterns for multi-language web applications using i18next, React-Intl, and framework-native solutions.

## i18next Setup (Most Common)

### Installation

```bash
npm install i18next react-i18next i18next-http-backend i18next-browser-languagedetector
```

### Configuration

```typescript
// src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'vi', 'ja', 'ko'],
    defaultNS: 'common',
    ns: ['common', 'auth', 'dashboard', 'errors'],

    interpolation: {
      escapeValue: false, // React already escapes
    },

    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

### File Structure

```
public/
└── locales/
    ├── en/
    │   ├── common.json
    │   ├── auth.json
    │   ├── dashboard.json
    │   └── errors.json
    └── vi/
        ├── common.json
        ├── auth.json
        ├── dashboard.json
        └── errors.json
```

### Translation Files

```json
// locales/en/common.json
{
  "app_name": "My Application",
  "nav": {
    "home": "Home",
    "dashboard": "Dashboard",
    "settings": "Settings",
    "logout": "Log out"
  },
  "actions": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "confirm": "Are you sure?"
  },
  "status": {
    "loading": "Loading...",
    "error": "Something went wrong",
    "empty": "No data found"
  }
}
```

```json
// locales/vi/common.json
{
  "app_name": "Ứng Dụng Của Tôi",
  "nav": {
    "home": "Trang chủ",
    "dashboard": "Bảng điều khiển",
    "settings": "Cài đặt",
    "logout": "Đăng xuất"
  },
  "actions": {
    "save": "Lưu",
    "cancel": "Hủy",
    "delete": "Xóa",
    "confirm": "Bạn có chắc chắn?"
  },
  "status": {
    "loading": "Đang tải...",
    "error": "Đã xảy ra lỗi",
    "empty": "Không có dữ liệu"
  }
}
```

## Usage in React Components

### Basic Translation

```tsx
import { useTranslation } from 'react-i18next';

function Navbar() {
  const { t } = useTranslation('common');

  return (
    <nav>
      <a href="/">{t('nav.home')}</a>
      <a href="/dashboard">{t('nav.dashboard')}</a>
      <button>{t('nav.logout')}</button>
    </nav>
  );
}
```

### With Interpolation

```json
// locales/en/dashboard.json
{
  "welcome": "Welcome back, {{name}}!",
  "items_count": "You have {{count}} item",
  "items_count_plural": "You have {{count}} items",
  "last_login": "Last login: {{date, datetime}}"
}
```

```tsx
function Dashboard({ user }) {
  const { t } = useTranslation('dashboard');

  return (
    <div>
      <h1>{t('welcome', { name: user.name })}</h1>
      <p>{t('items_count', { count: user.items.length })}</p>
    </div>
  );
}
```

### Language Switcher

```tsx
function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const languages = [
    { code: 'en', label: 'English', flag: '🇺🇸' },
    { code: 'vi', label: 'Tiếng Việt', flag: '🇻🇳' },
    { code: 'ja', label: '日本語', flag: '🇯🇵' },
  ];

  return (
    <select
      value={i18n.language}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
    >
      {languages.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {lang.flag} {lang.label}
        </option>
      ))}
    </select>
  );
}
```

## Pluralization

### English (Simple)

```json
{
  "message": "You have {{count}} message",
  "message_plural": "You have {{count}} messages",
  "message_0": "You have no messages"
}
```

### Vietnamese (No Plural Form)

Vietnamese doesn't have grammatical plurals. Use the same key:

```json
{
  "message": "Bạn có {{count}} tin nhắn"
}
```

### Complex Pluralization (Arabic, etc.)

```json
{
  "item_0": "No items",
  "item_one": "{{count}} item",
  "item_two": "{{count}} items",
  "item_few": "{{count}} items",
  "item_many": "{{count}} items",
  "item_other": "{{count}} items"
}
```

## Date & Number Formatting

```typescript
// Use Intl API for locale-aware formatting
const formatDate = (date: Date, locale: string) =>
  new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);

const formatCurrency = (amount: number, locale: string, currency: string) =>
  new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);

// Usage
formatDate(new Date(), 'vi-VN');  // "26 tháng 4, 2026"
formatDate(new Date(), 'en-US');  // "April 26, 2026"
formatCurrency(50000, 'vi-VN', 'VND');  // "50.000 ₫"
formatCurrency(29.99, 'en-US', 'USD');  // "$29.99"
```

## Namespace Strategy

| Namespace | Content | Loaded |
|---|---|---|
| `common` | Nav, buttons, status, errors | Always |
| `auth` | Login, register, password reset | Auth pages only |
| `dashboard` | Dashboard-specific strings | Dashboard route |
| `admin` | Admin panel strings | Admin route |
| `errors` | Error messages, validation | On demand |
| `emails` | Email templates (server-side) | Server only |

```tsx
// Load specific namespace
const { t } = useTranslation('dashboard');

// Load multiple namespaces
const { t } = useTranslation(['dashboard', 'common']);
```

## RTL (Right-to-Left) Support

```tsx
// Set document direction based on language
useEffect(() => {
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  document.documentElement.dir = rtlLanguages.includes(i18n.language) ? 'rtl' : 'ltr';
  document.documentElement.lang = i18n.language;
}, [i18n.language]);
```

```css
/* CSS logical properties for RTL-safe styling */
.sidebar {
  margin-inline-start: 1rem;  /* replaces margin-left */
  padding-inline-end: 1rem;   /* replaces padding-right */
  border-inline-start: 2px solid;  /* replaces border-left */
}
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Hardcoded strings in components | Extract to translation files |
| Concatenating translated strings | Use interpolation: `t('greeting', { name })` |
| Translating with template literals | Use `t()` function, not backticks |
| Missing fallback language | Set `fallbackLng: 'en'` in config |
| Loading all translations upfront | Use namespaces + lazy loading |
| Hardcoded date/number formats | Use `Intl.DateTimeFormat` / `Intl.NumberFormat` |
| Forgetting `lang` attribute | Set `<html lang="vi">` dynamically |
| Pluralizing in Vietnamese | Vietnamese has no grammatical plurals — use one form |

## Next.js i18n

```javascript
// next.config.js
module.exports = {
  i18n: {
    locales: ['en', 'vi', 'ja'],
    defaultLocale: 'en',
    localeDetection: true,
  },
};
```

```typescript
// pages/index.tsx — use getStaticProps for SSG
export async function getStaticProps({ locale }) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ['common', 'home'])),
    },
  };
}
```

# Internationalization (i18n) Patterns

## Setup (react-i18next)

```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n.use(Backend).use(LanguageDetector).use(initReactI18next).init({
  fallbackLng: 'en',
  supportedLngs: ['en', 'vi', 'ja'],
  ns: ['common', 'dashboard', 'auth'],
  defaultNS: 'common',
  interpolation: { escapeValue: false },
  backend: { loadPath: '/locales/{{lng}}/{{ns}}.json' },
});
```

## Usage

```jsx
const { t, i18n } = useTranslation('dashboard');
<h1>{t('welcome', { name: user.firstName })}</h1>
<button onClick={() => i18n.changeLanguage('vi')}>Vietnamese</button>
```

## Rules

- Do not hardcode user-facing strings.
- Split by namespaces per feature.
- Support pluralization.
- Use Intl for date/number formatting.
- Support RTL where required.

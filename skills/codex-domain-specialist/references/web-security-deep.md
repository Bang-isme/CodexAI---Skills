# Web Security Deep Dive

## CORS Configuration

```javascript
import cors from 'cors';

const allowedOrigins = ['https://app.example.com', 'https://admin.example.com'];
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) callback(null, true);
    else callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 86400,
}));
```

## CSP

```javascript
import helmet from 'helmet';
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", 'https://fonts.googleapis.com'],
      imgSrc: ["'self'", 'data:', 'https:'],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"],
    },
  },
}));
```

## CSRF

```javascript
import csrf from 'csurf';
app.use(csrf({ cookie: { httpOnly: true, secure: true, sameSite: 'strict' } }));
```

## Injection Prevention

```javascript
// SQL
await db.query('SELECT * FROM users WHERE email = $1', [email]);

// NoSQL
import mongoSanitize from 'express-mongo-sanitize';
app.use(mongoSanitize());
```

## Security Headers Checklist

- Strict-Transport-Security
- X-Content-Type-Options: nosniff
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy

# Email & Notification Patterns

## Core Principles

- Send emails through queue workers.
- Use templates, not inline HTML in route handlers.
- Include unsubscribe links for non-transactional emails.
- Log outbound email events for auditability.

## Email Architecture

API Handler -> Queue Job -> Worker -> SMTP/Provider -> Audit Log.

## Nodemailer Setup

```javascript
import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  host: config.smtpHost,
  port: config.smtpPort,
  secure: config.smtpPort === 465,
  auth: { user: config.smtpUser, pass: config.smtpPass },
  pool: true,
  maxConnections: 5,
  maxMessages: 100,
  rateLimit: 10,
});

const sendEmail = async ({ to, subject, html, text }) => {
  const info = await transporter.sendMail({
    from: `"${config.appName}" <${config.smtpUser}>`,
    to,
    subject,
    html,
    text,
  });
  logger.info('Email sent', { messageId: info.messageId, to, subject });
  return info;
};
```

## In-App Notifications

```javascript
const notificationSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
  type: { type: String, enum: ['info', 'warning', 'success', 'error'], default: 'info' },
  title: { type: String, required: true },
  message: String,
  read: { type: Boolean, default: false, index: true },
  link: String,
}, { timestamps: true });

notificationSchema.index({ userId: 1, read: 1, createdAt: -1 });
```

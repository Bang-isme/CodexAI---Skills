# File Upload Patterns

## Core Principles

- Never trust client input.
- Validate MIME type, extension, and file signature where possible.
- Enforce size limits at proxy and app layers.
- Store uploads outside web root or in object storage.
- Generate unique server-side filenames.

## Multipart Upload (Express + Multer)

```javascript
import multer from 'multer';
import path from 'path';
import crypto from 'crypto';

const ALLOWED_MIMES = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
const MAX_SIZE = 10 * 1024 * 1024;

const storage = multer.diskStorage({
  destination: './uploads',
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const unique = crypto.randomBytes(16).toString('hex');
    cb(null, `${unique}${ext}`);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: MAX_SIZE, files: 5 },
  fileFilter: (req, file, cb) => {
    if (!ALLOWED_MIMES.includes(file.mimetype)) {
      return cb(new AppError('File type not allowed', 400));
    }
    cb(null, true);
  },
});
```

## Presigned URL Pattern (S3)

1. Client requests presigned upload URL.
2. API returns short-lived URL (for example 5 minutes).
3. Client uploads directly to storage.
4. Client notifies API.
5. API verifies object and stores metadata.

## Security Checklist

- Size limit at nginx and app.
- MIME and extension validation.
- Server-generated filename.
- Upload dir not executable.
- Virus scan in production.
- Block executable types.

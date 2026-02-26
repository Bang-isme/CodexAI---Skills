# Background Jobs & Queue Patterns

## Scope

Use when processing tasks asynchronously: emails, reports, image processing, data sync, and scheduled tasks.

## Core Principles

- Jobs must be idempotent: running twice should produce the same final state.
- Always set timeout and retry limits.
- Dead-letter failed jobs for manual review.
- Monitor queue depth and processing latency.

## Bull Queue Setup (Redis-backed)

```javascript
import Queue from 'bull';

const emailQueue = new Queue('email', process.env.REDIS_URL, {
  defaultJobOptions: {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
    removeOnComplete: 100,
    removeOnFail: 500,
    timeout: 30000,
  },
});

// Producer
await emailQueue.add('welcome', {
  to: user.email,
  template: 'welcome',
  data: { firstName: user.firstName },
}, { priority: 1 });

// Consumer
emailQueue.process('welcome', 5, async (job) => {
  const { to, template, data } = job.data;
  await sendEmail(to, template, data);
  return { sent: true };
});

emailQueue.on('failed', (job, err) => {
  logger.error('Job failed', { jobId: job.id, type: job.name, error: err.message });
});

emailQueue.on('stalled', (job) => {
  logger.warn('Job stalled', { jobId: job.id });
});
```

## Scheduled Jobs (Cron)

```javascript
emailQueue.add('daily-report', {}, {
  repeat: { cron: '0 2 * * *' },
  jobId: 'daily-report-singleton',
});
```

## Job Priority

| Priority | Use Case |
| --- | --- |
| 1 (highest) | Password reset, OTP emails |
| 5 (default) | Welcome emails, notifications |
| 10 (low) | Reports, analytics, data sync |

## Anti-Patterns

- Processing heavy work in request handlers.
- No timeout on jobs.
- No retry cap.
- Storing req/res objects inside job payload.

## Review Checklist

- Are jobs idempotent?
- Are timeout/retry/backoff configured?
- Is failed job handling and DLQ policy defined?
- Are queue metrics monitored?

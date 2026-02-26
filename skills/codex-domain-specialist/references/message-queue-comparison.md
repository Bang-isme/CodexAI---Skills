# Message Queue Comparison

## Scope
Use when selecting a broker for asynchronous communication between services.

## Decision Table

| Feature | Redis Streams | RabbitMQ | Apache Kafka |
| --- | --- | --- | --- |
| Best for | Simple queue workloads | Complex routing and RPC | High-throughput event streaming |
| Throughput | ~100k msg/s | ~50k msg/s | ~1M msg/s |
| Persistence | Optional (AOF/RDB) | Disk + memory | Disk log |
| Ordering | Per-stream FIFO | Per-queue FIFO | Per-partition FIFO |
| Consumer groups | Yes | Yes | Yes |
| Dead-letter queue | Manual | Built-in | Manual |
| Replay | By ID | No | By offset |
| Complexity | Low | Medium | High |

## Tool Selection
- Redis already in stack and low ops overhead needed: Redis Streams or BullMQ.
- Routing patterns, priorities, retries, request-reply: RabbitMQ.
- Event log and replay at scale: Kafka.

## Redis Streams (BullMQ)

```javascript
import { Queue, Worker } from "bullmq";

const queue = new Queue("notifications", {
  connection: { host: "localhost", port: 6379 },
});

await queue.add("email", { to: "user@test.com", template: "welcome" });

const worker = new Worker(
  "notifications",
  async (job) => {
    if (job.name === "email") await sendEmail(job.data);
  },
  { connection: { host: "localhost", port: 6379 }, concurrency: 5 }
);
```

## RabbitMQ

```javascript
import amqplib from "amqplib";

const conn = await amqplib.connect("amqp://localhost");
const ch = await conn.createChannel();
await ch.assertQueue("tasks", { durable: true });
ch.sendToQueue("tasks", Buffer.from(JSON.stringify(data)), { persistent: true });

ch.consume(
  "tasks",
  async (msg) => {
    const payload = JSON.parse(msg.content.toString());
    await processTask(payload);
    ch.ack(msg);
  },
  { noAck: false }
);
```

## Pattern Mapping

| Pattern | Queue Type |
| --- | --- |
| Work queue | Any broker with competing consumers |
| Pub/Sub fan-out | RabbitMQ fanout exchange or Kafka topics |
| Request-reply | RabbitMQ + correlation ID |
| Event log replay | Kafka or Redis Streams |
| Priority queue | RabbitMQ priority or BullMQ priority |
| Scheduled messages | BullMQ or RabbitMQ plugin |

# Event Sourcing and CQRS

## When to Use

- Immutable audit trail is required.
- Business workflows are state-machine heavy.
- Replay/rebuild capability is needed.
- Read and write models diverge significantly.

## Event Sourcing Basics

Commands -> Events -> State projection.

Instead of only storing current state, store an ordered stream of domain events.

## Event Store

```javascript
const eventSchema = new mongoose.Schema({
  streamId: { type: String, required: true, index: true },
  type: { type: String, required: true },
  version: { type: Number, required: true },
  data: { type: mongoose.Schema.Types.Mixed, required: true },
  metadata: {
    correlationId: String,
    causationId: String,
    userId: String,
    timestamp: { type: Date, default: Date.now },
  },
}, { timestamps: true });

eventSchema.index({ streamId: 1, version: 1 }, { unique: true });

const appendEvent = async (streamId, event, expectedVersion) => {
  const currentVersion = await Event.countDocuments({ streamId });
  if (currentVersion !== expectedVersion) {
    throw new Error('Concurrency conflict: reload and retry');
  }
  return Event.create({ streamId, ...event, version: expectedVersion + 1 });
};
```

## CQRS

- Write side: command validation + event append.
- Read side: event projection to optimized read models.

## Projection Pattern

```javascript
const projectOrderSummary = async (orderId) => {
  const events = await Event.find({ streamId: `order:${orderId}` }).sort({ version: 1 });
  let state = { id: orderId, status: 'unknown', items: [], total: 0 };

  for (const event of events) {
    switch (event.type) {
      case 'OrderCreated':
        state = { ...state, status: 'created', items: event.data.items, total: event.data.total };
        break;
      case 'OrderPaid':
        state.status = 'paid';
        state.paidAt = event.metadata.timestamp;
        break;
      case 'OrderShipped':
        state.status = 'shipped';
        state.trackingCode = event.data.trackingCode;
        break;
      case 'OrderCancelled':
        state.status = 'cancelled';
        state.cancelReason = event.data.reason;
        break;
    }
  }

  return state;
};
```

## Rules

- Events are immutable (no edits/deletes).
- Use past-tense event names.
- Ensure idempotent consumer behavior.
- Version event schemas for evolution.
- Add snapshots for long streams.

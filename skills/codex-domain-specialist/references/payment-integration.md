# Payment Integration

## Core Principles

- Never store raw card data; use tokenization.
- Use idempotency keys for every charge/refund path.
- Persist and audit payment events.
- Process webhooks for async status changes.

## Stripe Payment Intent Example

```javascript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

const createPayment = async (req, res) => {
  const { amount, currency = 'usd', orderId } = req.body;

  const paymentIntent = await stripe.paymentIntents.create({
    amount: Math.round(amount * 100),
    currency,
    metadata: { orderId, userId: req.user.id },
    idempotencyKey: `order-${orderId}`,
  });

  await Payment.create({
    orderId,
    userId: req.user.id,
    stripePaymentIntentId: paymentIntent.id,
    amount,
    currency,
    status: 'pending',
  });

  res.json({ clientSecret: paymentIntent.client_secret });
};
```

## Webhook Handler Pattern

```javascript
const handleStripeWebhook = async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;

  try {
    event = stripe.webhooks.constructEvent(req.rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    return res.status(400).json({ error: 'Invalid signature' });
  }

  const existing = await WebhookEvent.findOne({ eventId: event.id });
  if (existing) return res.json({ received: true });

  switch (event.type) {
    case 'payment_intent.succeeded':
      await Payment.findOneAndUpdate(
        { stripePaymentIntentId: event.data.object.id },
        { status: 'completed', paidAt: new Date() }
      );
      break;
    case 'payment_intent.payment_failed':
      await Payment.findOneAndUpdate(
        { stripePaymentIntentId: event.data.object.id },
        { status: 'failed', failureReason: event.data.object.last_payment_error?.message }
      );
      break;
  }

  await WebhookEvent.create({ eventId: event.id, type: event.type, processedAt: new Date() });
  return res.json({ received: true });
};
```

## Security Checklist

- Stripe keys only in env.
- Verify webhook signature every time.
- Server-side amount validation.
- Idempotency keys on charge/refund.
- Use provider SDK/Elements for PCI boundaries.
- Reconcile provider dashboard with DB records regularly.

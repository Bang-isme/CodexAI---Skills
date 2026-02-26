# Design Patterns (JavaScript/TypeScript)

## Scope

Use when structuring code for reusability, maintainability, and testability.

## Creational Patterns

### Factory Pattern

```javascript
class NotificationFactory {
  static create(type, data) {
    switch (type) {
      case 'email': return new EmailNotification(data);
      case 'sms': return new SmsNotification(data);
      case 'push': return new PushNotification(data);
      default: throw new Error(`Unknown type: ${type}`);
    }
  }
}
```

### Builder Pattern

```javascript
class QueryBuilder {
  #query = {};
  where(field, value) { this.#query[field] = value; return this; }
  sort(field, order = 'asc') { this.#sort = { [field]: order }; return this; }
  limit(n) { this.#limit = n; return this; }
  build() { return { query: this.#query, sort: this.#sort, limit: this.#limit }; }
}
```

### Singleton Pattern

```javascript
class Database {
  static #instance;
  static getInstance() {
    if (!Database.#instance) Database.#instance = new Database();
    return Database.#instance;
  }
}
```

## Structural Patterns

### Repository Pattern

```javascript
class UserRepository {
  async findById(id) { return User.findById(id).lean(); }
  async create(data) { return User.create(data); }
  async update(id, data) { return User.findByIdAndUpdate(id, data, { new: true }); }
  async delete(id) { return User.findByIdAndDelete(id); }
}
```

### Adapter Pattern

```javascript
class PaymentAdapter {
  constructor(provider) { this.provider = provider; }
  async charge(amount, currency, token) {
    if (this.provider === 'stripe') return this.#chargeStripe(amount, currency, token);
    if (this.provider === 'paypal') return this.#chargePaypal(amount, currency, token);
    throw new Error('Unsupported provider');
  }
}
```

## Behavioral Patterns

### Strategy Pattern

```javascript
const pricingStrategies = {
  standard: (base) => base,
  premium: (base) => base * 0.9,
  enterprise: (base) => base * 0.75,
};
```

### Observer Pattern

```javascript
import { EventEmitter } from 'events';
const appEvents = new EventEmitter();
appEvents.emit('user:created', { userId: '123' });
appEvents.on('user:created', async (data) => sendWelcomeEmail(data));
```

### Middleware / Chain of Responsibility

```javascript
router.post('/users', validate(schema), authenticate, authorize('admin'), createUserHandler);
```

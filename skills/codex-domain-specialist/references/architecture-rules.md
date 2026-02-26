# Architecture Rules

## Scope and Triggers

Use when designing system structure, choosing patterns, or refactoring for scale.

## Core Principles

- Start monolith, extract services only when complexity demands.
- Dependencies flow inward (business rules never depend on frameworks).
- Each module has one clear owner and one clear API.
- Design for failure: every external call can fail.

## Monolith vs Microservice Decision

| Factor | Stay Monolith | Extract Service |
| --- | --- | --- |
| Team size | < 10 developers | 10+ with clear domain teams |
| Deploy frequency | Same release cycle | Different release cadence needed |
| Scale requirements | Uniform scaling | Component needs independent scaling |
| Data coupling | Shared database is fine | Needs separate data ownership |
| Complexity | Can reason about in one head | Too complex for single codebase |

### Monolith Best Practices

- Use modular monolith: clear module boundaries, explicit APIs between modules.
- One database but separate schemas per module.
- Extract to microservice later by replacing module API with HTTP/gRPC.

### Microservice Rules

- Each service owns its data (no shared database).
- Communication: sync (REST/gRPC) for queries, async (events/queues) for commands.
- API gateway for external clients.
- Distributed tracing (correlation IDs) is mandatory.
- Circuit breaker for all inter-service calls.
- Eventual consistency is default; strong consistency requires saga pattern.

## Clean Architecture Layers

```text
+-----------------------------+
| Frameworks (Express, React) | <- Replaceable
+-----------------------------+
| Adapters (Controllers, DB)  | <- Interface implementations
+-----------------------------+
| Use Cases (Application)     | <- Business workflows
+-----------------------------+
| Entities (Domain)           | <- Core business rules
+-----------------------------+
```

## SOLID Principles

| Principle | Rule | Example |
| --- | --- | --- |
| S - Single Responsibility | One reason to change | UserService: only user business logic |
| O - Open/Closed | Extend without modifying | Plugin system, strategy pattern |
| L - Liskov Substitution | Subtypes replaceable | Any Repository implements same interface |
| I - Interface Segregation | Small focused interfaces | IReadRepository vs IWriteRepository |
| D - Dependency Inversion | Depend on abstractions | Service depends on IRepository, not MongoRepository |

## Domain-Driven Design (DDD) Essentials

- Bounded Context: each domain area has its own model (User in Auth != User in Billing).
- Aggregate Root: entry point for a cluster of domain objects (Order -> OrderItems).
- Value Object: immutable, defined by attributes (Money, Email, Address).
- Domain Event: something that happened (OrderPlaced, PaymentCompleted).
- Repository: collection-like interface for aggregates.

## Event-Driven Architecture

Producer -> Event Bus (Kafka/RabbitMQ/Redis Streams) -> Consumer(s)

Rules:
- Events are immutable facts (past tense: UserCreated, OrderShipped).
- Consumers must be idempotent (same event processed twice = same result).
- Include correlation ID and timestamp in every event.
- Dead-letter queue for failed processing.

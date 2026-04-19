# Testing Anti-Patterns

**Load this reference when:** writing or changing tests, adding mocks, or tempted to add test-only methods to production code.

## Overview

Common mistakes when writing tests. Reference this before adding mocks, test utilities, or test-only methods.

**Core principle:** Test what the code does, not what the mocks do.

## The Iron Laws

```
1. NEVER test mock behavior
2. NEVER add test-only methods to production classes
3. NEVER mock without understanding dependencies
4. ALWAYS mock complete data structures, not partial fields
```

## Anti-Pattern 1: Testing Mock Behavior

**Bad:**
```python
def test_sends_notification(mock_notifier):
    mock_notifier.send.return_value = True
    result = mock_notifier.send("hello")
    assert result is True  # Testing the mock, not the code
```

**Good:**
```python
def test_sends_notification():
    notifier = InMemoryNotifier()  # Real implementation, in-memory
    service = NotificationService(notifier)
    service.notify_user("user-1", "hello")
    assert notifier.messages == [("user-1", "hello")]
```

**Rule:** Test your code's behavior, not your mock's configuration.

### Gate Function

```
BEFORE asserting on any mock element:
  Ask: "Am I testing real component behavior or just mock existence?"
  IF testing mock existence: STOP — Delete the assertion or unmock
```

## Anti-Pattern 2: Test-Only Methods

**Bad:**
```python
class UserService:
    def create_user(self, name):
        self._users.append(name)

    def _get_users_for_testing(self):  # Test-only method in production code
        return self._users
```

**Good:**
```python
class UserService:
    def create_user(self, name):
        self._users.append(name)

    def list_users(self):  # Useful in production too
        return list(self._users)
```

**Rule:** If you need a method only for testing, your API is incomplete.

### Gate Function

```
BEFORE adding any method to production class:
  Ask: "Is this only used by tests?"
  IF yes: STOP — Put it in test utilities instead
```

## Anti-Pattern 3: Mocking Without Understanding

**Bad:**
```python
@patch('module.database')
@patch('module.cache')
@patch('module.logger')
@patch('module.metrics')
def test_process(mock_metrics, mock_logger, mock_cache, mock_db):
    # 4 mocks = you don't understand the code
    mock_db.query.return_value = [{"id": 1}]
    mock_cache.get.return_value = None
    process()
    mock_db.query.assert_called_once()
```

**Good:**
```python
def test_process():
    db = InMemoryDatabase([{"id": 1}])
    processor = Processor(db)
    result = processor.process()
    assert result == [{"id": 1, "processed": True}]
```

**Rule:** If you need 3+ mocks, your code is too coupled. Refactor with dependency injection.

### Gate Function

```
BEFORE mocking any method:
  1. Ask: "What side effects does the real method have?"
  2. Ask: "Does this test depend on any of those side effects?"
  IF depends on side effects:
    Mock at lower level, NOT the high-level method
```

## Anti-Pattern 4: Testing Implementation, Not Behavior

**Bad:**
```typescript
test('uses correct SQL query', () => {
  userRepo.findByEmail('a@b.com');
  expect(db.query).toHaveBeenCalledWith(
    'SELECT * FROM users WHERE email = ?', ['a@b.com']
  );
});
```

**Good:**
```typescript
test('finds user by email', async () => {
  await userRepo.save({ name: 'Alice', email: 'a@b.com' });
  const user = await userRepo.findByEmail('a@b.com');
  expect(user.name).toBe('Alice');
});
```

**Rule:** Test WHAT the code does (behavior), not HOW it does it (implementation).

## Anti-Pattern 5: Flaky Tests with Arbitrary Delays

**Bad:**
```python
def test_async_operation():
    start_operation()
    time.sleep(2)  # Guess: 2 seconds is enough?
    assert get_result() is not None
```

**Good:**
```python
def test_async_operation():
    start_operation()
    result = wait_for(lambda: get_result() is not None, timeout=5.0)
    assert result is not None
```

**Rule:** Wait for conditions, not arbitrary time. See `codex-systematic-debugging/references/condition-based-waiting.md`.

## Anti-Pattern 6: Shared Mutable State Between Tests

**Bad:**
```python
users = []  # Shared state

def test_add_user():
    users.append("Alice")
    assert len(users) == 1

def test_add_another_user():
    users.append("Bob")
    assert len(users) == 1  # FAIL: users has ["Alice", "Bob"]
```

**Good:**
```python
def test_add_user():
    users = []
    users.append("Alice")
    assert len(users) == 1

def test_add_another_user():
    users = []
    users.append("Bob")
    assert len(users) == 1  # PASS
```

**Rule:** Each test must set up and tear down its own state.

## Anti-Pattern 7: Assert Everything at Once

**Bad:**
```python
def test_user_creation():
    user = create_user("Alice", "a@b.com", 30)
    assert user.name == "Alice"
    assert user.email == "a@b.com"
    assert user.age == 30
    assert user.id is not None
    assert user.created_at is not None
    assert user.is_active is True
    assert user.role == "user"
```

**Good:**
```python
def test_user_has_correct_name():
    user = create_user("Alice", "a@b.com", 30)
    assert user.name == "Alice"

def test_user_is_active_by_default():
    user = create_user("Alice", "a@b.com", 30)
    assert user.is_active is True

def test_user_has_default_role():
    user = create_user("Alice", "a@b.com", 30)
    assert user.role == "user"
```

**Rule:** One assertion per test. "and" in test name = split it.

## Quick Reference

| Pattern | Symptom | Fix |
|---------|---------|-----|
| Mock behavior | Testing mock returns | Use real or in-memory impl |
| Test-only methods | `_for_testing()` suffix | Make it a real API method |
| Over-mocking | 3+ `@patch` decorators | Dependency injection |
| Implementation testing | Asserting SQL/API calls | Assert observable behavior |
| Flaky delays | `sleep()` in tests | Condition-based waiting |
| Shared state | Tests fail in different order | Isolate state per test |
| Assert everything | Giant test function | One assertion per test |

# Root Cause Tracing

Technique for tracing backward from symptom to source.

## The Technique

1. Start at the ERROR (the symptom)
2. Ask: "What value is wrong here?"
3. Ask: "Where does this value come from?"
4. Follow the value BACKWARD through the call stack
5. At each level ask: "Is the value wrong HERE or was it already wrong when passed in?"
6. Keep going until you find where the value FIRST becomes wrong
7. That is the root cause - fix HERE, not at the symptom

## Example

Error: "Cannot read property 'name' of undefined" at line 42 -> user is undefined at line 42 -> user comes from getUser(id) at line 38 -> id comes from req.params.userId at line 35 -> req.params.userId is "undefined" (string) - WRONG! -> Router sends string "undefined" because URL was /users/undefined -> Frontend sent fetch(/users/${user.id}) but user.id was undefined -> ROOT CAUSE: Frontend didn't check if user was loaded before navigating

Fix at root (frontend guard), not at symptom (null check at line 42).

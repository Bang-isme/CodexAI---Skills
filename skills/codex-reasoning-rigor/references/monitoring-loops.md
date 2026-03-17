# Monitoring Loops

Attach a monitoring loop to any workflow that will repeat or can drift.

## Minimum Monitoring Contract

- `signal`: what to observe
- `healthy`: what good looks like
- `drift`: what degradation looks like
- `action`: what to do when the signal goes red

## Good Signals

- test count or pass rate
- validator score
- artifact completeness
- sync drift between local pack and global pack
- repeated manual override or fallback use
- number of warnings left unclosed at handoff

## Anti-Drift Rule

If a workflow improvement depends on human memory alone, it will decay.
Prefer:

- scripts
- manifests
- templates
- validators
- recurring quality checks

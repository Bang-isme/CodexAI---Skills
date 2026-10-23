# DESIGN.md CLI Commands

The native contract script in this skill is `scripts/design_contract.py`. It provides a zero-dependency Python engine for scaffolding, linting, diffing, exporting, and inspecting `DESIGN.md` visual contracts.

## Local Entry Points

```bash
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" doctor
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" scaffold --name "Atlas Console" --output DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" lint DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" diff DESIGN-old.md DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" export DESIGN.md --format tailwind
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" export DESIGN.md --format dtcg
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" spec
```

## Command Overview

| Command | Purpose | Notes |
| --- | --- | --- |
| `doctor` | Check engine and template readiness | Reports native engine status and YAML parser |
| `scaffold` | Write a canonical starter `DESIGN.md` file | Refuses to overwrite existing file unless `--force` is passed |
| `lint <file>` | Validate token structure, references, and section order | Exits non-zero when errors exist |
| `diff <before> <after>` | Compare token changes and lint regressions | Exits non-zero on error/warning regressions |
| `export <file> --format tailwind` | Export tokens to Tailwind theme JSON | Emits deterministic JSON |
| `export <file> --format dtcg` | Export tokens to W3C Design Tokens (DTCG) JSON | Emits deterministic JSON |
| `spec` | Print the `DESIGN.md` contract specification and lint rules | Supports `--rules` and `--rules-only` |

## Recommended Workflow

1. `doctor` before first use in a new environment
2. `scaffold` if the repo has no `DESIGN.md`
3. `lint` before code generation that depends on the contract
4. `diff` in review flows when tokens or rationale changed
5. `export` when engineering needs Tailwind or DTCG output

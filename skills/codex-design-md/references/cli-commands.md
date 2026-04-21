# DESIGN.md CLI Commands

The wrapper script in this skill is `scripts/design_contract.py`. It adds a local scaffold flow plus a bundled Python engine for lint, diff, export, and spec. When explicitly requested, it can still try the upstream DESIGN.md CLI.

You do not need an upstream source checkout to use this skill. The bundled Python engine is the default path.

## Local Entry Points

```bash
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" doctor
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" scaffold --name "Atlas Console" --output DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" lint DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" diff DESIGN-old.md DESIGN.md
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" export DESIGN.md --format tailwind
python "<SKILLS_ROOT>/codex-design-md/scripts/design_contract.py" spec
```

## Upstream Behavior

The wrapper runtime model is:

1. bundled Python engine inside this skill
2. local built repo at `<DESIGN_MD_SOURCE_REPO>/packages/cli/dist/index.js` when `--prefer local`
3. local source repo with Bun at `<DESIGN_MD_SOURCE_REPO>/packages/cli/src/index.ts` when `--prefer local`
4. published package via `npx --yes --package @google/design.md design.md` when `--prefer npx`

`<DESIGN_MD_SOURCE_REPO>` is optional. The wrapper resolves it in this order:

1. `--source-repo <path>`
2. environment variable `CODEX_DESIGN_MD_SOURCE_REPO`
3. nearby auto-discovery for folders named `design.md-main` or `design.md`

## Command Mapping

| Wrapper Command | Upstream Equivalent | Notes |
| --- | --- | --- |
| `doctor` | none | reports bundled and upstream runtime availability |
| `scaffold` | none | writes a canonical starter `DESIGN.md` file |
| `lint <file>` | `design.md lint <file>` | bundled engine by default, exits non-zero on errors |
| `diff <before> <after>` | `design.md diff <before> <after>` | bundled engine by default, exits non-zero on regressions |
| `export <file> --format tailwind` | `design.md export <file> --format tailwind` | bundled engine by default, emits JSON |
| `export <file> --format dtcg` | `design.md export <file> --format dtcg` | bundled engine by default, emits JSON |
| `spec` | `design.md spec` | reads the local spec file and can append bundled lint-rule descriptions |

## Recommended Workflow

1. `doctor` before first use in a new environment
2. `scaffold` if the repo has no `DESIGN.md`
3. `lint` before code generation that depends on the contract
4. `diff` in review flows when tokens or rationale changed
5. `export` when engineering needs Tailwind or DTCG output

## Failure Modes

- The bundled engine is intentionally lighter than the upstream implementation; use the upstream repo when you need exact parity
- `--prefer npx` or `--prefer local` will fall back to the bundled engine if the upstream path is unavailable or silent
- Overwriting an existing `DESIGN.md`: blocked unless `--force` is passed to `scaffold`

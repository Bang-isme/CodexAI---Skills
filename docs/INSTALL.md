# Install CodexAI Skills

Choose one host. You do not need GitHub CLI, Node.js, or another downloaded skill pack for normal use. The Python installer is for adapters and local copies; marketplace installs are available where a native manifest exists.

## Host support and install

| Host | Package path | Install |
| --- | --- | --- |
| **Codex** | Codex compatibility plugin and Git-backed marketplace entry ([official docs](https://developers.openai.com/plugins/build/plugins)) | Run `codex plugin marketplace add Bang-isme/CodexAI---Skills --sparse .agents/plugins`. In the Codex desktop app, open the plugin directory, choose **CodexAI Skills**, then install `codexai-agentic-workflow`. |
| **Claude Code** | Claude plugin manifest and repository marketplace ([official docs](https://code.claude.com/docs/en/plugin-marketplaces)) | Run `claude plugin marketplace add Bang-isme/CodexAI---Skills`, then `claude plugin install codexai-agentic-workflow@codexai-skills`. |
| **Cursor** | Cursor plugin marketplace manifest plus native skills ([plugins](https://prod.cursor.com/docs/plugins), [skills](https://prod.cursor.com/docs/skills)) | In Cursor, open **Customize → Plugins → Add/Import from GitHub Repository** and enter `Bang-isme/CodexAI---Skills`; install `codexai-agentic-workflow` at user or project scope. Or clone/download this repo and run `python skills/.system/scripts/install.py --host cursor --scope user --apply`. |
| **Antigravity** | Native package candidate with IDE/CLI installer; live-host smoke testing is still required for a production support claim | From the extracted or cloned repository, run `python skills/.system/scripts/install.py --host antigravity --scope user --apply`. This installs the current package candidate for the user. |

All four host adapters are listed at the same level. Their packaging and validation status differs; the table describes that status instead of implying identical native support. This package does **not** currently provide a native Gemini CLI extension.

The local gates validate checked-in manifests, paths, versions, and Antigravity package output. They do not launch these host applications. Live install flows were not smoke-tested in the current environment; test with each actual host version before making a host-specific compatibility claim. Antigravity remains a package candidate until that smoke test passes.

For a project-only copy, run the local installer from this repository root:

```sh
python skills/.system/scripts/install.py --host <codex|claude|cursor|antigravity> --scope repo --repo-root . --apply
```

The host must be explicit. The default scope is `user`; the installer does not silently write bridges into the current project. Preview first by omitting `--apply`. To inspect a user install:

```sh
python skills/.system/scripts/install.py doctor --host <codex|claude|cursor|antigravity> --scope user
```

## Use the design workflow

- Ask for a page or component and invoke `codex-frontend-design` (Codex alias: `$design`) for the fast path.
- Ask for a multi-screen product prototype when you need a route/state contract, a selected visual direction, a runnable prototype, responsive captures, and a final review.
- For a new visual identity or several alternatives, explicitly ask for design studio or multiple directions.

The broad prototype path needs an app that can run and browser capture tooling (Playwright and Chromium). If a browser, route, state, viewport, or screenshot slice is missing, the visual result must stay `DEGRADED`; it is not an approval. Captures emulate CSS viewport sizes, not physical devices, and cannot objectively certify taste.

## Update and troubleshoot

- Update marketplace installs through that host's plugin manager.
- For script-installed copies, get the newer repository release and rerun its same `install.py --host … --scope … --apply` command.
- Run `python skills/.system/scripts/install.py doctor --host <host> --scope user` to inspect the adapter wiring. This does not verify that a rendered UI looks correct.
- GitHub CLI (`gh`) is optional and only needed for tasks that use GitHub automation, such as creating pull requests.

See [the Vietnamese guide](huong-dan-vi.md), [project artifact layout](project-artifact-layout.md), and [technical reference](../skills/README.md).

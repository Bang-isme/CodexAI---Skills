# Hướng Dẫn Sử Dụng CodexAI Skill Pack

> Phiên bản: `18.1.0` | Cập nhật: 2026-10-02

## 1. Giới Thiệu

CodexAI Skill Pack cung cấp quy trình làm việc bằng văn bản cho các coding agent, cùng hướng dẫn tích hợp cho Codex, Claude Code, Cursor, và Antigravity. Phạm vi kiểm chứng khác nhau theo host; xem [hướng dẫn cài đặt](INSTALL.md) trước khi cài.

Với công việc vừa/lớn, pack thường hướng dẫn agent đi qua các bước:

`Phân tích yêu cầu -> Lập đặc tả -> Lập kế hoạch -> Route đúng agent/domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Handoff/Commit`

### Breaking 18.0.0

- Không còn skill redirect `codex-design-system`, `codex-ui-ux-design`, `codex-creative-direction`. Dùng `codex-frontend-design` (`$design` / `$ux` / `$direction`).
- Không còn agent `ui-ux-designer`, `creative-director`, `creative-designer`. Dùng `design-lead`.

## 2. Điểm mạnh chính

| Vấn đề thường gặp | Pack giải quyết thế nào |
| --- | --- |
| AI hiểu sai mục tiêu hoặc trôi scope | `codex-intent-context-analyzer` giúp làm rõ goal, scope, constraints, ambiguity |
| Thiếu context giữa các phiên dài | `codex-context-engine`, `codex-role-docs`, và `codex-project-memory` lưu genome, role docs, decisions, handoff |
| Tri thức ngầm nằm trong đầu người làm | `$knowledge` tạo `.codex/knowledge/INDEX.md` từ genome, role docs, decisions, commit history, và config |
| Prototype fullstack bắt đầu quá mơ hồ | `$prototype` hướng dẫn luồng spec-first: `$hook -> $init-profile -> $genome -> $init-docs -> $spec -> $plan -> implement -> $check-full` |
| Output generic, thiếu bằng chứng | `codex-reasoning-rigor`, `output_guard.py`, và `editorial_review.py` hướng dẫn ghi rõ file, command, risk, next step |
| Thiết kế UI cho nhiều phạm vi | `codex-frontend-design`: fast cho page/component, prototype cho luồng nhiều màn hình, studio cho hướng mới hoặc nhiều phương án; có implementation và visual gate hỗ trợ |
| Không có gate trước khi kết luận | `auto_gate.py` gom preflight, security, lint/test, role docs, spec, knowledge, visual mechanical, bundle |

## 3. Cài đặt và bắt đầu

1. Chọn một host và làm theo [hướng dẫn cài đặt theo host](INSTALL.md). Tài liệu ghi rõ cách cài và giới hạn xác minh của Codex, Claude Code, Cursor, và Antigravity.
2. Nếu cài từ source bằng installer, chạy doctor cho đúng một host sau khi cài. Ví dụ: `python ".\skills\.system\scripts\install.py" doctor --host cursor --scope user --format text` (đổi `cursor` theo host đã cài). Doctor kiểm tra wiring của host, không xác nhận chất lượng UI render.
3. Dùng alias như `$plan`, `$create`, `$design`, hoặc `$check`; nạp `codex-master-instructions` trước.

Không dùng `skills/*` khi sync thủ công, vì wildcard đó có thể bỏ sót `.system`, `.agents`, và `.workflows`. CodexAI hiện chưa có native extension cho Gemini CLI; xem bảng hỗ trợ trong [hướng dẫn cài đặt](INSTALL.md).

## 3b. Cài Đặt Hoặc Sync Global Skills

Chạy từ root repo `CodexAI---Skills`. Không dùng `skills/*`, vì wildcard đó có thể bỏ sót `.system`, `.agents`, và `.workflows`.

Generic CLI/IDE harness:

```powershell
python ".\skills\.system\scripts\trust_harness.py" --project-root "." --skills-root ".\skills" --setup generic --apply --evidence ".\.codexai\evidence\trust-harness.json" --format text
```

Lệnh này tạo `.codexai/skills`, `AGENTS.md` bridge, và file mô tả hook `.codexai/hooks/pre_prompt.json`; đồng thời chạy contract, prompt-router corpus, Python unit tests, responsive Node tests (nếu có Node.js), và kiểm tra dry-run gói release. Thiếu Node.js hoặc có Node test bị skip (ví dụ browser fixture không có Playwright/Chromium) được báo là warning. Host cần hỗ trợ và thực thi hook thì mới tự gọi router được; các kiểm tra này không chứng minh tích hợp đã hoạt động trên mọi IDE/CLI.

Ưu tiên cài theo Codex-native target:

```powershell
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope user --dry-run --format text
python ".\skills\.system\scripts\install_codex_native.py" --source ".\skills" --scope user --apply --format text
```

Repo này cũng có `.codex-plugin/plugin.json` và `.agents/plugins/marketplace.json` để test plugin discovery theo native plugin lifecycle.

Nếu dùng Claude Code, repo cũng có `.claude-plugin/plugin.json` và `hooks/hooks.json`. Có thể cài standalone vào `~/.claude/skills`:

```powershell
python ".\skills\.system\scripts\install_claude_native.py" --source ".\skills" --scope user --dry-run --format text
python ".\skills\.system\scripts\install_claude_native.py" --source ".\skills" --scope user --apply --format text
```

Hoặc test plugin trực tiếp:

```powershell
python ".\skills\.system\scripts\validate_claude_plugin.py" --plugin-root "." --format text
claude --plugin-dir .
```

### Windows PowerShell

```powershell
python ".\skills\.system\scripts\sync_global_skills.py" --source-root ".\skills" --global-root "$env:USERPROFILE\.codex\skills" --dry-run --format text
python ".\skills\.system\scripts\sync_global_skills.py" --source-root ".\skills" --global-root "$env:USERPROFILE\.codex\skills" --apply --format text
```

### macOS / Linux

```bash
python ./skills/.system/scripts/sync_global_skills.py --source-root ./skills --global-root "$HOME/.codex/skills" --dry-run --format text
python ./skills/.system/scripts/sync_global_skills.py --source-root ./skills --global-root "$HOME/.codex/skills" --apply --format text
```

## 4. Kiểm Tra Sau Cài Đặt

Cách nhanh nhất là chạy pipeline hợp nhất (alias `$pipeline`):

```bash
python skills/.system/scripts/pipeline.py --stage all --format text            # lint, contracts, test, build, doctor
python skills/.system/scripts/pipeline.py --stage lint,contracts --format text # kiểm tra nhanh trước khi commit
```

Hoặc chạy từng bước:

```bash
python -m unittest discover -s skills/tests -p "test_*.py"
node --test skills/tests/responsive_capture_stitch.test.mjs skills/tests/responsive_capture_core.test.mjs skills/tests/responsive_capture_browser.test.mjs
python skills/.system/scripts/check_pack_health.py --skills-root skills --global-root "$HOME/.codex/skills" --format text
python skills/.system/scripts/validate_codex_plugin.py --plugin-root . --format text
python skills/.system/scripts/validate_claude_plugin.py --plugin-root . --format text
python skills/.system/scripts/trust_harness.py --project-root . --skills-root skills --setup generic --evidence .codexai/evidence/trust-harness.json --format text
```

Trên Windows PowerShell:

```powershell
python ".\skills\.system\scripts\check_pack_health.py" --skills-root ".\skills" --global-root "$env:USERPROFILE\.codex\skills" --format text
```

Pass criteria:

- Source VERSION và global VERSION giống nhau.
- Global có `.system/manifest.json`, `.system/REGISTRY.md`, `.agents/`, `.workflows/`.
- Native Codex agent role files không có field không hợp lệ như `prompt`.

## 5. Các Lệnh Nên Dùng

| Lệnh | Chức năng |
| --- | --- |
| `$hook` / `$preflight` | Chạy preflight để detect domain, agent, readiness gaps, profile/spec/knowledge status |
| `$init-profile` | Tạo `.codex/profile.json` để route ổn định hơn và giảm đoán sai |
| `$codex-genome` / `$genome` | Tạo genome nhiều góc nhìn cho project |
| `$init-docs`, `$check-docs` | Khởi tạo và kiểm tra role-based project docs |
| `$spec` | Tạo hoặc kiểm tra `.codex/specs/<slug>/SPEC.md` |
| `$prototype` | Chạy workflow fullstack/MVP theo hướng spec-first |
| `$plan` | Tạo plan có acceptance criteria và verify method |
| `$sdd` / `$dispatch` | Delegate task độc lập cho subagents với review hai lớp |
| `$knowledge` | Tạo `.codex/knowledge/INDEX.md` để làm tri thức ngầm trở nên rõ ràng |
| `$check`, `$check-full`, `$check-deploy` | Chạy `auto_gate.py` theo mức quick/full/deploy |
| `$health` | Kiểm tra manifest, registry, aliases, dot directories, global sync, và encoding |
| `$design` / `$ux` / `$direction` | `codex-frontend-design`: fast cho page/component; prototype cho luồng nhiều màn hình; studio khi cần nhiều hướng hoặc identity mới |
| `$pipeline` | Chạy `pipeline.py --stage all`: lint, contracts, test, build, doctor trong một lệnh, xuất report JSON |
| `$release-gate` | Chạy `local_release_gate.py` (dry-run) trước khi tạo tag `vX.Y.Z` để kích hoạt GitHub Release |
| `$doctor` | `install.py doctor --host <host> --scope user` kiểm tra wiring sau khi cài; thay `<host>` bằng một host cụ thể |
| `$think` / `$decide` | Tạo decision surface ngắn: options, evidence, cost, risk, verification |

## 6. Quy Trình Full-Cycle Prototype

Khi người dùng chỉ đưa một yêu cầu cơ bản như “tạo prototype fullstack”, agent nên dùng chuỗi sau:

1. Chạy `$hook` để biết project hiện có gì và thiếu gì.
2. Chạy `$init-profile` nếu chưa có `.codex/profile.json`.
3. Chạy `$genome` để có context kiến trúc.
4. Chạy `$init-docs` nếu thiếu tài liệu dự án; mặc định tạo project brief và ADR template. Chọn role folder khi dự án thực sự cần.
5. Chạy `$spec` để ghi rõ problem, goals, non-goals, requirements, acceptance criteria, và FE/BE/data/QA impact.
6. Chạy `$plan` để chia task nhỏ, có verify command và rollback.
7. Triển khai bằng `$sdd` nếu task độc lập, hoặc inline nếu task phụ thuộc chặt.
8. Cập nhật role docs và chạy `$knowledge`.
9. Chạy `$check-full` trước khi kết luận.

## 7. Nguyên Tắc Vận Hành

- Không claim “xong” nếu chưa có bằng chứng kiểm tra mới.
- Không bulk-load toàn bộ reference; dùng `$hook` để chọn đúng domain.
- Không sửa file ngoài `file_ownership` của agent hiện tại; nếu cần, handoff sang agent đúng.
- Với workflow `$prototype` cho MVP/fullstack nhiều domain, tạo spec trước khi triển khai. Page/component UI nhỏ có thể dùng fast path `$design` mà không cần spec.
- Không coi missing role docs/spec/knowledge là blocker mặc định; chúng là advisory trừ khi project policy yêu cầu.

# Hướng Dẫn Sử Dụng CodexAI Skill Pack

> Phiên bản: `18.0.0` | Cập nhật: 2026-09-21

## 1. Giới Thiệu

CodexAI Skill Pack giúp Codex làm việc theo một quy trình kỹ thuật rõ ràng thay vì phản hồi tùy hứng theo từng prompt.

Luồng chuẩn của pack:

`Phân tích yêu cầu -> Lập đặc tả -> Lập kế hoạch -> Route đúng agent/domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Handoff/Commit`

### Số liệu hiện tại

| Hạng mục | Giá trị |
| --- | --- |
| Core skills | 30 |
| Entry-point scripts | 74 |
| Shared helpers | 2 |
| References | 190+ |
| Starters | 29 |
| Artifact templates | 9 |
| Agent personas | 10 |
| Workflow aliases | 8 |
| Kiểm thử | 461 unit + 87 smoke = 548 bài test |

## 2. Điểm mạnh chính

| Vấn đề thường gặp | Pack giải quyết thế nào |
| --- | --- |
| AI hiểu sai mục tiêu hoặc trôi scope | `codex-intent-context-analyzer` khóa goal, scope, constraints, ambiguity |
| Thiếu context giữa các phiên dài | `codex-context-engine`, `codex-role-docs`, và `codex-project-memory` lưu genome, role docs, decisions, handoff |
| Tri thức ngầm nằm trong đầu người làm | `$knowledge` tạo `.codex/knowledge/INDEX.md` từ genome, role docs, decisions, commit history, và config |
| Prototype fullstack bắt đầu quá mơ hồ | `$prototype` ép chạy spec-first: `$hook -> $init-profile -> $genome -> $init-docs -> $spec -> $plan -> implement -> $check-full` |
| Output generic, thiếu bằng chứng | `codex-reasoning-rigor`, `output_guard.py`, và `editorial_review.py` ép file, command, risk, next step |
| UI đẹp nhưng UX khó dùng | `design-lead`, `codex-frontend-design` (fast/studio), `frontend-specialist`, và visual mechanical gate |
| Không có gate trước khi kết luận | `auto_gate.py` gom preflight, security, lint/test, role docs, spec, knowledge, visual mechanical, bundle |

## 3. Cài đặt trong 3 bước

1. Cài host: `python ".\skills\.system\scripts\install.py" --host cursor --scope repo --repo-root "." --apply --format text`
2. Doctor: `python ".\skills\.system\scripts\install.py" doctor --host all --repo-root "." --format text`
3. Dùng alias: `$plan`, `$create`, `$design`, `$check`. Nạp `codex-master-instructions` trước.

Chi tiết từng host (Codex / Claude / Antigravity) nằm dưới đây. Không dùng `skills/*`, vì wildcard đó có thể bỏ sót `.system`, `.agents`, và `.workflows`.

## 3b. Cài Đặt Hoặc Sync Global Skills

Chạy từ root repo `CodexAI---Skills`. Không dùng `skills/*`, vì wildcard đó có thể bỏ sót `.system`, `.agents`, và `.workflows`.

Generic CLI/IDE harness:

```powershell
python ".\skills\.system\scripts\trust_harness.py" --project-root "." --skills-root ".\skills" --setup generic --apply --evidence ".\.codexai\evidence\trust-harness.json" --format text
```

Lệnh này tạo `.codexai/skills`, `AGENTS.md` bridge, và `.codexai/hooks/pre_prompt.json` để IDE/CLI bất kỳ có thể gọi router trước mỗi prompt.

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

Cách nhanh nhất là chạy pipeline hợp nhất (cùng bộ gate với CI; alias `$pipeline`):

```bash
python skills/.system/scripts/pipeline.py --stage all --format text            # lint, contracts, test, build, doctor
python skills/.system/scripts/pipeline.py --stage lint,contracts --format text # kiểm tra nhanh trước khi commit
```

Hoặc chạy từng bước:

```bash
python -m pytest skills/tests -q
python skills/tests/smoke_test.py
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
| `$pipeline` | Chạy `pipeline.py --stage all`: lint, contracts, test, build, doctor trong một lệnh, xuất report JSON |
| `$release-gate` | Chạy `local_release_gate.py` (dry-run) trước khi tạo tag `vX.Y.Z` để kích hoạt GitHub Release |
| `$doctor` | `install.py doctor --host all` kiểm tra wiring Codex/Claude/Cursor/Antigravity |
| `$think` / `$decide` | Tạo decision surface ngắn: options, evidence, cost, risk, verification |

## 6. Quy Trình Full-Cycle Prototype

Khi người dùng chỉ đưa một yêu cầu cơ bản như “tạo prototype fullstack”, agent nên dùng chuỗi sau:

1. Chạy `$hook` để biết project hiện có gì và thiếu gì.
2. Chạy `$init-profile` nếu chưa có `.codex/profile.json`.
3. Chạy `$genome` để có context kiến trúc.
4. Chạy `$init-docs` để tạo FE/BE/DevOps/Admin/QA docs.
5. Chạy `$spec` để khóa problem, goals, non-goals, requirements, acceptance criteria, FE/BE/data/QA impact.
6. Chạy `$plan` để chia task nhỏ, có verify command và rollback.
7. Triển khai bằng `$sdd` nếu task độc lập, hoặc inline nếu task phụ thuộc chặt.
8. Cập nhật role docs và chạy `$knowledge`.
9. Chạy `$check-full` trước khi kết luận.

## 7. Nguyên Tắc Vận Hành

- Không claim “xong” nếu chưa có bằng chứng kiểm tra mới.
- Không bulk-load toàn bộ reference; dùng `$hook` để chọn đúng domain.
- Không sửa file ngoài `file_ownership` của agent hiện tại; nếu cần, handoff sang agent đúng.
- Không triển khai prototype/fullstack trước khi có spec.
- Không coi missing role docs/spec/knowledge là blocker mặc định; chúng là advisory trừ khi project policy yêu cầu.

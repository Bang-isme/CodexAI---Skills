# Hướng Dẫn Sử Dụng CodexAI Skill Pack

> Phiên bản: `15.0.0` | Cập nhật: 2026-04-26

## 1. Giới thiệu

CodexAI Skill Pack giúp Codex làm việc theo một quy trình kỹ thuật rõ ràng thay vì phản hồi tùy hứng theo từng prompt.

Luồng chuẩn của pack:

`Phân tích yêu cầu -> Lập kế hoạch -> Route đúng domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Commit`

### Số liệu hiện tại

| Hạng mục | Giá trị |
| --- | --- |
| Core skills | 25 |
| Entry-point scripts | 53 |
| Shared helpers | 2 |
| References | 185+ |
| Starters | 29 |
| Artifact templates | 9 |
| Agent personas | 8 |
| Workflow aliases | 7 |
| Kiểm thử | 168 unit + 55 smoke = 223 bài test |

## 2. Điểm mạnh chính

| Vấn đề thường gặp | Pack giải quyết thế nào |
| --- | --- |
| AI hiểu sai mục tiêu hoặc trôi scope | `codex-intent-context-analyzer` khóa goal, scope, constraints, ambiguity |
| Kế hoạch nghe hay nhưng khó triển khai | `codex-plan-writer` chia task nhỏ, có dependency và verify method |
| Output generic, thiếu bằng chứng | `codex-reasoning-rigor` + `output_guard.py` ép file, command, risk, next step |
| Output đúng nhưng đọc vẫn giống AI | `editorial_review.py` kiểm tra tone, decision clarity, tradeoff, scanability |
| UI đẹp nhưng UX khó dùng | `frontend-specialist` + `codex-design-system` áp dụng design tokens, UX golden rules, accessibility |
| Không có gate trước khi kết thúc | `codex-execution-quality-gate` gom security, lint/test, output quality, UX/a11y, trend tracking |
| Mất micro-context giữa các phiên dài | `codex-role-docs` và `codex-project-memory` lưu role docs, decision, handoff, genome |
| Scrum không vận hành nhất quán | `codex-scrum-subagents` cài role kit, workflow, native custom agents |

## 3. Cài đặt hoặc sync global skills

Chạy các lệnh dưới đây từ root của repo `CodexAI---Skills`. Các lệnh này copy cả thư mục bắt đầu bằng dấu chấm như `.system`, `.agents`, và `.workflows`. Không dùng `skills/*`, vì wildcard đó có thể bỏ sót metadata runtime trên một số môi trường.

### Windows PowerShell

```powershell
$source = Resolve-Path ".\skills"
$target = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $target | Out-Null
Get-ChildItem -Force -LiteralPath $source | ForEach-Object {
  Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
}
```

### macOS / Linux

```bash
mkdir -p "$HOME/.codex/skills"
cp -R ./skills/. "$HOME/.codex/skills/"
```

## 4. Kiểm tra sau cài đặt

```bash
# Unit tests
python -m pytest skills/tests -q

# Smoke checks
python skills/tests/smoke_test.py
```

Kiểm tra các file runtime quan trọng đã được sync:

```bash
test -f "$HOME/.codex/skills/.system/REGISTRY.md"
test -f "$HOME/.codex/skills/.system/manifest.json"
test -f "$HOME/.codex/skills/.system/scripts/check_boundaries.py"
```

Trên Windows PowerShell:

```powershell
Test-Path "$env:USERPROFILE\.codex\skills\.system\REGISTRY.md"
Test-Path "$env:USERPROFILE\.codex\skills\.system\manifest.json"
Test-Path "$env:USERPROFILE\.codex\skills\.system\scripts\check_boundaries.py"
```

## 5. Các lệnh nên dùng trước

| Lệnh | Chức năng |
| --- | --- |
| `$codex-genome` | Tạo genome nhiều góc nhìn cho project |
| `$codex-intent-context-analyzer` | Phân tích yêu cầu thành intent có cấu trúc |
| `$codex-plan-writer` hoặc `$plan` | Tạo plan có thể verify |
| `$codex-workflow-autopilot` hoặc `$route` | Chọn workflow phù hợp |
| `$codex-reasoning-rigor` hoặc `$rigor` | Ép output cụ thể, có tradeoff và evidence |
| `$codex-execution-quality-gate` hoặc `$gate` | Chạy quality gate |
| `$check`, `$check-full`, `$check-deploy` | Chạy `auto_gate.py` theo mức quick/full/deploy |
| `$output-guard` hoặc `$guard` | Chấm mức cụ thể và bằng chứng của output |
| `$editorial-review` hoặc `$editorial` | Kiểm tra output có đọc như artifact kỹ thuật đáng tin cậy không |
| `$init-docs`, `$check-docs` | Khởi tạo và kiểm tra role-based project docs |
| `$scrum-install` | Cài Scrum `.agent` kit và native `.codex/agents` |
| `$story-ready-check` | Kiểm tra story đã đủ rõ để làm chưa |
| `$release-readiness` | Chạy ceremony quyết định ship |
| `$log-decision` | Lưu quyết định kỹ thuật |
| `$session-summary` | Tạo handoff cuối phiên |
| `$codex-doctor` hoặc `$doctor` | Kiểm tra môi trường cài skill |

## 6. Quy trình khuyến nghị

### Với task code bình thường

1. Chạy intent analyzer để khóa mục tiêu, constraints, và missing info.
2. Nếu task không nhỏ, tạo plan có checkpoint và verify command.
3. Route đúng domain hoặc agent persona.
4. Triển khai theo từng bước nhỏ, giữ đúng file ownership.
5. Chạy quality gate trước khi kết luận hoàn thành.
6. Ghi role docs, decision hoặc session summary nếu thay đổi tạo context dài hạn.

### Với plan, review, handoff, hoặc báo cáo

1. Bật `codex-reasoning-rigor`.
2. Chạy `output_guard.py` để kiểm tra evidence và specificity.
3. Chạy `editorial_review.py` để kiểm tra tone, structure, và accountability.
4. Chạy `run_gate.py --strict-output` nếu deliverable cần chất lượng phát hành.

Mục tiêu là output không chỉ đúng, mà còn:

- có quyết định rõ
- có file, command, số liệu hoặc bằng chứng thật
- có risk, tradeoff, và next step
- đọc giống một deliverable kỹ thuật do người chịu trách nhiệm viết

## 7. Các nhóm skill

### Core pipeline

- `codex-master-instructions`
- `codex-intent-context-analyzer`
- `codex-plan-writer`
- `codex-workflow-autopilot`
- `codex-reasoning-rigor`
- `codex-role-docs`
- `codex-scrum-subagents`

### Domain và design

- `codex-domain-specialist`
- `codex-security-specialist`
- `codex-design-system`
- `codex-design-md`
- `codex-document-writer`

### Quality, memory, delivery

- `codex-execution-quality-gate`
- `codex-project-memory`
- `codex-docs-change-sync`
- `codex-git-autopilot`
- `codex-doc-renderer`

## 8. Ghi chú vận hành

- `.codex/profile.yaml` là file tùy chọn của từng project. Nếu thiếu, domain specialist sẽ tự detect từ file và package signals.
- `.system/REGISTRY.md` là registry lệnh runtime. Nếu file này thiếu trong global skills, quá trình sync chưa đầy đủ.
- `auto_gate.py` là entry point chính cho quick/full/deploy gate.
- Role docs nằm trong project đang làm việc tại `.codex/project-docs/`, không phải global skill context.
- Hooks và CI gate là runtime enforcement. Nếu chưa cài hooks hoặc CI, AI vẫn phải tự chạy gate trước khi kết luận.

## 9. Tài liệu liên quan

- README public: [../README.md](../README.md)
- README kỹ thuật: [../skills/README.md](../skills/README.md)
- Changelog: [../skills/CHANGELOG.md](../skills/CHANGELOG.md)

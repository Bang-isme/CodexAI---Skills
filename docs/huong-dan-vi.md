# Hướng Dẫn Sử Dụng CodexAI Skill Pack

> Phiên bản: `12.6.0` | Cập nhật: 2026-03-18

## 1. Giới thiệu

CodexAI Skill Pack giúp Codex làm việc giống một đối tác kỹ thuật có quy trình, thay vì chỉ phản hồi theo prompt.

Luồng chuẩn của pack:

`Phân tích yêu cầu -> Lập kế hoạch -> Route đúng domain -> Triển khai -> Kiểm tra -> Lưu tri thức -> Commit`

### Số liệu hiện tại

| Hạng mục | Giá trị |
| --- | --- |
| Core skills | 14 |
| Entry-point scripts | 43 |
| Shared helpers | 2 |
| References | 149 |
| Starters | 29 |
| Artifact templates | 6 |
| Kiểm thử | 98 unit + 49 smoke = 147 bài test |

## 2. Điểm mạnh chính

| Vấn đề thường gặp | Pack giải quyết thế nào |
| --- | --- |
| AI hiểu sai ý hoặc trôi mục tiêu | `codex-intent-context-analyzer` khóa goal, scope, ambiguity |
| Kế hoạch nghe hay nhưng khó làm | `codex-plan-writer` chia task nhỏ, có verify rõ |
| Output generic, thiếu bằng chứng | `codex-reasoning-rigor` + `output_guard.py` |
| Output không generic nhưng vẫn "mùi AI" | `editorial_review.py` chấm tone, decision, tradeoff, structure |
| Không có gate trước khi kết thúc | `codex-execution-quality-gate` gom lint, test, security, output quality |
| Mất context giữa các phiên | `codex-project-memory` lưu decision, handoff, summary, genome |
| Scrum không được vận hành nhất quán | `codex-scrum-subagents` cài role kit, workflow, native custom agents |

## 3. Cài đặt

### Windows PowerShell

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

### macOS / Linux

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

## 4. Kiểm tra sau cài đặt

```bash
# Unit tests
python -m pytest skills/tests -q

# Smoke checks
python skills/tests/smoke_test.py
```

## 5. Các lệnh nên dùng trước

| Lệnh | Chức năng |
| --- | --- |
| `$codex-genome` | Tạo genome cho project |
| `$codex-intent-context-analyzer` | Phân tích yêu cầu thành intent có cấu trúc |
| `$codex-plan-writer` | Tạo plan có thể verify |
| `$codex-workflow-autopilot` | Chọn workflow phù hợp |
| `$codex-reasoning-rigor` | Ép output sâu hơn, bớt generic |
| `$codex-execution-quality-gate` | Chạy quality gate |
| `$output-guard` | Chấm độ cụ thể và mức evidence |
| `editorial_review.py` | Kiểm tra output có đọc giống artifact do con người viết hay chưa |
| `$scrum-install` | Cài Scrum `.agent` kit và native `.codex/agents` |
| `$story-ready-check` | Kiểm tra story đã đủ rõ để làm chưa |
| `$release-readiness` | Chạy ceremony quyết định ship hay chưa |
| `$log-decision` | Lưu quyết định kỹ thuật |
| `$session-summary` | Tạo handoff cuối phiên |
| `$codex-doctor` | Kiểm tra môi trường cài skill |

## 6. Quy trình khuyến nghị

### Với task code bình thường

1. Chạy intent analyzer.
2. Nếu task không nhỏ, tạo plan.
3. Route đúng domain/security context.
4. Triển khai theo từng bước nhỏ.
5. Chạy quality gate trước khi chốt.
6. Ghi decision hoặc session summary nếu context quan trọng.

### Với plan, review, handoff

Đây là nơi pack khác biệt nhất:

1. Bật `codex-reasoning-rigor`
2. Chạy `output_guard.py`
3. Chạy `editorial_review.py`
4. Chạy `run_gate.py --strict-output`

Mục tiêu là output không chỉ đúng, mà còn:

- có quyết định rõ
- có file/command/evidence thật
- có risk/tradeoff/follow-up
- đọc giống một deliverable kỹ thuật do con người chịu trách nhiệm viết

## 7. Các nhóm skill

### Core pipeline

- `codex-master-instructions`
- `codex-intent-context-analyzer`
- `codex-context-engine`
- `codex-plan-writer`
- `codex-workflow-autopilot`
- `codex-reasoning-rigor`
- `codex-scrum-subagents`

### Knowledge packs

- `codex-domain-specialist`: 66 references, 19 starters
- `codex-security-specialist`: 30 references, 10 starters

### Quality, memory, delivery

- `codex-execution-quality-gate`
- `codex-project-memory`
- `codex-docs-change-sync`
- `codex-git-autopilot`
- `codex-doc-renderer`

## 8. Ghi chú vận hành

- `plan`, `review`, `handoff` hiện mặc định bị kiểm tra strict-output nếu bạn đưa file hoặc text deliverable vào `run_gate.py`.
- `quality_trend.py` bây giờ theo dõi thêm gate pass rate, output score, editorial score.
- Scrum kit hỗ trợ `project`, `personal`, và `both` cho native custom agents.

## 9. Tài liệu liên quan

- README public: [../README.md](../README.md)
- README kỹ thuật: [../skills/README.md](../skills/README.md)
- Changelog: [../skills/CHANGELOG.md](../skills/CHANGELOG.md)

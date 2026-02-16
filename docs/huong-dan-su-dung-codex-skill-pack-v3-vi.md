# Hướng Dẫn Sử Dụng Codex Skill Pack (v3+)

Tài liệu này dành cho developer Việt muốn dùng bộ skill để biến Codex thành copilot kỹ thuật có quy trình rõ ràng, chạy được end-to-end từ phân tích yêu cầu đến xác minh trước khi chốt `done`.

## 1. Bộ skill này giải quyết vấn đề gì

Các vấn đề phổ biến khi dùng AI coding:
- Hiểu sai yêu cầu và code lệch mục tiêu.
- Trả lời nhanh nhưng không có workflow kiểm soát.
- Thiếu kiểm tra trước khi kết luận hoàn thành.
- Không lưu được ngữ cảnh dự án dài hạn.

Skill pack giải quyết bằng cách:
- Chuẩn hóa phân tích intent và missing info trước khi code.
- Bắt buộc đi theo workflow phù hợp (`build/fix/debug/review/docs`).
- Áp rule theo domain để giảm sai kiến trúc.
- Chạy quality gate và các check bổ sung.
- Lưu project memory để dùng xuyên phiên.

## 2. Triết lý instruction-first

Skill pack không vận hành như pipeline script cứng.  
Lõi chính là behavior trong `SKILL.md`; script chỉ là helper khi cần chạy tool thực (git, lint, test, scan, audit).

Thứ tự làm việc điển hình:

```text
Request
  -> codex-master-instructions
  -> codex-intent-context-analyzer
  -> codex-workflow-autopilot
  -> codex-domain-specialist
  -> implementation
  -> codex-docs-change-sync
  -> codex-execution-quality-gate
  -> codex-project-memory
```

## 3. Danh sách 8 skills hiện có

### 3.1 `codex-master-instructions`
- Vai trò: luật nền ưu tiên cao nhất.
- Chức năng: phân loại request, quy tắc chất lượng code, dependency awareness, completion self-check.

### 3.2 `codex-intent-context-analyzer`
- Vai trò: phân tích yêu cầu thành JSON contract.
- Chức năng: trích xuất `intent`, `goal`, `constraints`, `missing_info`, `complexity`, `normalized_prompt`.
- Có Socratic Gate cho yêu cầu phức tạp.

### 3.3 `codex-workflow-autopilot`
- Vai trò: route từ intent đã confirm sang workflow thực thi.
- Chức năng: behavioral modes, BMAD phases, checkpoint logic.
- Teaching mode: `$teach`, `explain`, `walk me through`.
- Helper script: `scripts/explain_code.py`.

### 3.4 `codex-domain-specialist`
- Vai trò: áp luật kỹ thuật theo domain.
- Domain hiện có: frontend, backend, mobile, debugging, security.
- Dùng khi task chạm file/concern chuyên biệt.

### 3.5 `codex-docs-change-sync`
- Vai trò: map diff code sang docs cần cập nhật.
- Chức năng: report-only (MVP), không tự sửa docs trừ khi user yêu cầu.
- Helper script: `scripts/map_changes_to_docs.py`.

### 3.6 `codex-execution-quality-gate`
- Vai trò: verification trước khi chốt hoàn thành.
- Blocking checks:
  - `security_scan.py` (critical findings).
  - `run_gate.py` lint/test fail (exit 1).
- Advisory checks:
  - `bundle_check.py`
  - `tech_debt_scan.py`
  - `suggest_improvements.py`
  - `predict_impact.py`
  - `quality_trend.py`
  - `pre_commit_check.py`
  - `smart_test_selector.py`
  - `ux_audit.py`
  - `accessibility_check.py`
  - `lighthouse_audit.py`
  - `playwright_runner.py`

### 3.7 `codex-plan-writer`
- Vai trò: viết plan file cho task medium/large.
- Chức năng: task breakdown có dependencies, verify method, rollback strategy.

### 3.8 `codex-project-memory`
- Vai trò: lưu tri thức dự án và lịch sử quyết định.
- Scripts hiện có:
  - `decision_logger.py`
  - `generate_handoff.py`
  - `generate_session_summary.py`
  - `build_knowledge_graph.py`
  - `track_skill_usage.py`

## 4. Cấu trúc thư mục chuẩn

```text
CodexAI---Skills/
├── README.md
├── docs/
│   └── huong-dan-su-dung-codex-skill-pack-v3-vi.md
└── skills/
    ├── codex-master-instructions/
    ├── codex-intent-context-analyzer/
    ├── codex-workflow-autopilot/
    ├── codex-domain-specialist/
    ├── codex-docs-change-sync/
    ├── codex-execution-quality-gate/
    ├── codex-plan-writer/
    └── codex-project-memory/
```

## 5. Yêu cầu môi trường

- Python `>= 3.8`
- Git
- Node.js + npm/npx (để chạy Lighthouse/Playwright wrapper)
- Codex extension/environment hỗ trợ skill loading

## 6. Cài đặt vào Codex

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

Kiểm tra nhanh:
1. Mở session Codex mới.
2. Gọi trigger:
   - `$codex-intent-context-analyzer`
   - `$codex-workflow-autopilot`
   - `$codex-execution-quality-gate`
3. Nếu phản hồi đúng behavior/contract là setup thành công.

## 7. Trigger cheat sheet

- Analyzer: `$codex-intent-context-analyzer`
- Workflow: `$codex-workflow-autopilot`
- Domain: `$codex-domain-specialist`
- Docs sync: `$codex-docs-change-sync`
- Gate: `$codex-execution-quality-gate`
- Plan: `$codex-plan-writer`
- Teaching mode: `$teach`

Quality gate triggers:
- `$pre-commit`
- `$smart-test`
- `$suggest`
- `$impact`
- `$quality-record`
- `$quality-report`
- `$ux-audit`
- `$a11y-check`
- `$lighthouse <url>`
- `$e2e check`
- `$e2e generate <url>`
- `$e2e run`

Project memory triggers:
- `$log-decision`
- `$handoff`
- `$session-summary`
- `$build-graph`
- `$skill-track`
- `$skill-report`

## 8. Workflow đề xuất cho developer

### 8.1 Luồng chuẩn feature/fix

1. Phân tích yêu cầu (`intent analyzer`).
2. Confirm scope.
3. Sinh workflow (`workflow autopilot`).
4. Áp rule domain (`domain specialist`).
5. Implement + test.
6. Map docs (`docs-change-sync`).
7. Run gate (`execution-quality-gate`).
8. Nếu task quan trọng: log decision (`project-memory`).

### 8.2 Luồng cho task lớn

1. Analyzer bật Socratic Gate.
2. Autopilot đi BMAD phases.
3. Tạo plan bằng `codex-plan-writer`.
4. User approve plan.
5. Implement theo task breakdown.
6. Phase X verification.

### 8.3 Luồng handoff giữa người/AI

1. Chạy `generate_handoff.py`.
2. Chạy `generate_session_summary.py`.
3. Nếu refactor lớn, chạy `build_knowledge_graph.py`.
4. Dán `handoff.md` cho AI mới để tiếp tục không mất ngữ cảnh.

## 9. Ví dụ prompt dùng ngay

### 9.1 Feature mới

```text
$codex-intent-context-analyzer
Thêm filter trạng thái đơn hàng cho trang admin React, có test cơ bản và cập nhật docs liên quan.
```

### 9.2 Bug production

```text
$codex-workflow-autopilot
API login trả 500 ngẫu nhiên, debug theo quy trình có bằng chứng và regression test.
```

### 9.3 Quality gate trước khi merge

```text
$codex-execution-quality-gate
Chạy Phase X verification cho nhánh hiện tại trước khi kết luận done.
```

### 9.4 Handoff

```text
$handoff
Tạo file handoff đầy đủ để mình chuyển context sang AI khác.
```

## 10. Command line examples

### 10.1 Docs sync

```powershell
python "$env:USERPROFILE\.codex\skills\codex-docs-change-sync\scripts\map_changes_to_docs.py" --project-root "D:\your-project" --diff-scope auto
```

### 10.2 Gate core

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\security_scan.py" --project-root "D:\your-project"
```

### 10.3 Gate mở rộng

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\smart_test_selector.py" --project-root "D:\your-project" --source staged
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\ux_audit.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\accessibility_check.py" --project-root "D:\your-project" --level AA
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\lighthouse_audit.py" --url "http://localhost:3000"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\playwright_runner.py" --project-root "D:\your-project" --mode check
```

### 10.4 Project memory

```powershell
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\decision_logger.py" --project-root "D:\your-project" --title "cursor-pagination" --decision "Use cursor pagination" --alternatives "Offset pagination" --reasoning "Better performance at scale" --context "Dashboard API"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\generate_handoff.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\generate_session_summary.py" --project-root "D:\your-project" --since today
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\build_knowledge_graph.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\track_skill_usage.py" --skills-root "$env:USERPROFILE\.codex\skills" --report
```

## 11. Output contracts quan trọng

### 11.1 Intent analyzer JSON

```json
{
  "intent": "build | fix | review | debug | docs | other",
  "goal": "string",
  "pain_points": ["string"],
  "constraints": ["string"],
  "missing_info": ["string"],
  "normalized_prompt": "string",
  "complexity": "simple | complex",
  "needs_confirmation": true
}
```

### 11.2 Workflow autopilot JSON

```json
{
  "mode": "brainstorm | thinking-partner | implement | debug | review | devils-advocate | teach | ship",
  "workflow_type": "build | fix | review | debug | docs",
  "steps": ["step1", "step2"],
  "exit_criteria": ["criterion1"],
  "estimated_scope": "small | medium | large",
  "phase": "analysis | planning | solutioning | implementation | verification"
}
```

### 11.3 Gate policy tóm tắt

- Blocking:
  - security critical findings
  - lint fail (`exit 1`)
  - test fail (`exit 1`)
- Advisory/non-blocking:
  - bundle/tech debt/suggestions/impact/trend
  - UX/a11y/Lighthouse/Playwright
- Thiếu tool external phải trả JSON có hướng dẫn cài đặt, không crash.

## 12. Troubleshooting

### 12.1 Không thấy skill trong Codex

- Kiểm tra đúng path `~/.codex/skills`.
- Kiểm tra mỗi skill có `SKILL.md` + `agents/openai.yaml`.
- Reload session/extension.

### 12.2 Script báo `no_git`

- Bạn đang chạy ngoài git repo.
- Trỏ `--project-root` vào thư mục có `.git`.

### 12.3 Lighthouse không chạy

- Cài: `npm install -g lighthouse` hoặc dùng `npx lighthouse`.
- Đảm bảo URL đang chạy thực.

### 12.4 Playwright chưa cài

- `npm init playwright@latest`
- `npx playwright install chromium`

### 12.5 Python script lỗi

- Kiểm tra `python --version`.
- Dùng Python `>= 3.8`.

## 13. Best practices cho team

1. Luôn bắt đầu bằng analyzer trước khi code.
2. Không skip gate nếu chưa có lý do rõ.
3. Task medium/large bắt buộc có plan.
4. Log decision cho thay đổi kiến trúc.
5. Dùng handoff/session summary cho chuyển ca hoặc đổi AI.

## 14. Repository description đề xuất

Bạn có thể dùng ngay cho phần Description trên GitHub:

`Instruction-first Codex skill pack for end-to-end developer workflow: intent analysis, workflow routing, domain rules, docs sync, quality gate, and project memory with practical helper scripts.`

Phiên bản tiếng Việt:

`Bộ skill instruction-first cho Codex, hỗ trợ full workflow developer: phân tích yêu cầu, route workflow, rule theo domain, sync docs, quality gate và project memory với helper scripts thực chiến.`


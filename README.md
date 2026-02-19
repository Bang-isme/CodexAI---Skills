<img width="263" height="225" alt="image" src="https://github.com/user-attachments/assets/9fcfbd06-769e-4b2e-b245-f7701d3a5a9d" />

# CodexAI Skill Pack

Bộ skill mở rộng cho OpenAI Codex theo triết lý **instruction-first**: ưu tiên hành vi và workflow trong `SKILL.md`, chỉ dùng script cho các phần cần chạy tool thật (git/lint/test/security/audit).

Mục tiêu:
- Phân tích đúng yêu cầu trước khi code.
- Triển khai theo workflow kỹ thuật rõ ràng (build/fix/debug/review/docs).
- Áp rule theo domain để giảm lỗi kiến trúc.
- Không bỏ sót docs và quality gate.
- Lưu trí nhớ dự án để làm việc xuyên phiên.

## 1. Tính năng chính

- 8 skills cốt lõi cho full vòng đời dev.
- 18 helper scripts (advisory + verification + project memory).
- Quality gate có kiểm tra mở rộng: pre-commit, smart test, tech debt, UX/a11y, Lighthouse, Playwright.
- Project memory: decision log, handoff, session summary, knowledge graph, skill usage analytics.
- Thiết kế graceful degradation: thiếu tool external vẫn trả JSON hướng dẫn, không crash.

## 2. Kiến trúc hoạt động

```text
User request
  -> codex-master-instructions (luật nền)
  -> codex-intent-context-analyzer (phân tích intent + missing info)
  -> codex-workflow-autopilot (route workflow + mode)
  -> codex-domain-specialist (áp rule domain)
  -> implementation
  -> codex-docs-change-sync (gợi ý docs cần cập nhật)
  -> codex-execution-quality-gate (verify trước khi chốt done)
  -> codex-project-memory (ghi nhớ quyết định/ngữ cảnh dự án)
```

## 3. Danh sách skills

| Skill | Vai trò | Trigger tiêu biểu | Scripts |
| --- | --- | --- | --- |
| `codex-master-instructions` | Luật nền ưu tiên cao nhất (phân loại request, chất lượng code, completion check) | tự động khi task code/review | không có |
| `codex-intent-context-analyzer` | Parse yêu cầu thành JSON contract (`intent`, `goal`, `constraints`, `missing_info`, `complexity`) | trước mọi task có chỉnh code/docs | không có |
| `codex-workflow-autopilot` | Sinh workflow theo intent + behavioral mode (implement/debug/review/teach/...) | `$codex-workflow-autopilot`, `$teach` | `explain_code.py` |
| `codex-domain-specialist` | Chọn rule theo domain frontend/backend/mobile/debug/security | `$codex-domain-specialist` hoặc theo signal file | không có |
| `codex-docs-change-sync` | Map code diff -> docs candidates (report-only) | `$codex-docs-change-sync` | `map_changes_to_docs.py` |
| `codex-execution-quality-gate` | Verification trước khi complete: lint/test/security + optional checks | `$codex-execution-quality-gate`, `$pre-commit`, `$smart-test`, `$ux-audit`, `$a11y-check`, `$lighthouse`, `$e2e ...` | 11 scripts |
| `codex-plan-writer` | Viết plan file có checklist verify cho task medium/large | `$codex-plan-writer` | không có |
| `codex-project-memory` | Ghi nhớ kiến thức dự án xuyên phiên | `$log-decision`, `$handoff`, `$session-summary`, `$build-graph`, `$skill-track` | 5 scripts |

## 4. Cấu trúc repo

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

- OpenAI Codex/extension có hỗ trợ skill loading.
- Python `>= 3.8`.
- Git (bắt buộc cho các script dựa trên diff/log).
- Node.js + npm/npx (cho check dùng Lighthouse/Playwright).

## 6. Cài đặt

### 6.1. Cài toàn bộ skills

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### 6.2. Verify nhanh

1. Mở session Codex mới.
2. Gọi một trigger explicit:
   - `$codex-intent-context-analyzer`
   - `$codex-workflow-autopilot`
   - `$codex-execution-quality-gate`
3. Nếu Codex phản hồi đúng behavior/contract của skill là cài thành công.

## 7. Workflow dùng chuẩn cho developer

### 7.1. Feature/fix flow

1. Phân tích yêu cầu bằng `codex-intent-context-analyzer`.
2. Confirm scope với user.
3. Sinh workflow bằng `codex-workflow-autopilot`.
4. Áp rule domain bằng `codex-domain-specialist`.
5. Implement + test.
6. Sync docs candidates bằng `codex-docs-change-sync`.
7. Chạy quality gate trước khi chốt done.

### 7.2. Task lớn (medium/large)

1. Intent analyzer bật Socratic Gate.
2. Workflow autopilot vào BMAD phases.
3. Dùng `codex-plan-writer` tạo plan file ở project root.
4. Sau khi plan được approve mới implement.
5. Kết thúc bắt buộc qua Phase X verification.

### 7.3. Dự án dài hạn

1. Log quyết định kiến trúc bằng `codex-project-memory`.
2. Trước khi đổi AI hoặc handoff thành viên mới, tạo `handoff.md`.
3. Cuối session tạo `session summary`.
4. Trước refactor lớn, build knowledge graph.

## 8. Trigger cheat sheet

- Analyzer: `$codex-intent-context-analyzer`
- Workflow: `$codex-workflow-autopilot`
- Teaching mode: `$teach`, `explain`, `walk me through`
- Docs mapping: `$codex-docs-change-sync`
- Gate tổng: `$codex-execution-quality-gate`
- Pre-commit: `$pre-commit`
- Smart test: `$smart-test`
- Suggestions: `$suggest`
- Impact predictor: `$impact`
- Quality trend: `$quality-record`, `$quality-report`
- UX/A11y: `$ux-audit`, `$a11y-check`
- Lighthouse: `$lighthouse <url>`
- E2E: `$e2e check`, `$e2e generate <url>`, `$e2e run`
- Memory: `$log-decision`, `$handoff`, `$session-summary`, `$skill-track`, `$skill-report`, `$build-graph`

## 9. CLI examples (thực thi script trực tiếp)

### 9.1. Docs sync

```powershell
python "$env:USERPROFILE\.codex\skills\codex-docs-change-sync\scripts\map_changes_to_docs.py" --project-root "D:\your-project" --diff-scope auto
```

### 9.2. Quality gate core

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\security_scan.py" --project-root "D:\your-project"
```

### 9.3. Quality gate mở rộng

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\pre_commit_check.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\smart_test_selector.py" --project-root "D:\your-project" --source staged
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\ux_audit.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\accessibility_check.py" --project-root "D:\your-project" --level AA
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\lighthouse_audit.py" --url "http://localhost:3000"
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\playwright_runner.py" --project-root "D:\your-project" --mode check
```

### 9.4. Project memory

```powershell
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\decision_logger.py" --project-root "D:\your-project" --title "cursor-pagination" --decision "Use cursor pagination" --alternatives "Offset pagination" --reasoning "Better performance at scale" --context "Dashboard API"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\generate_handoff.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\generate_session_summary.py" --project-root "D:\your-project" --since today
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\build_knowledge_graph.py" --project-root "D:\your-project"
python "$env:USERPROFILE\.codex\skills\codex-project-memory\scripts\track_skill_usage.py" --skills-root "$env:USERPROFILE\.codex\skills" --report
```

## 10. Output contracts quan trọng

### 10.1. Intent Analyzer JSON (trong chat)

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

### 10.2. Workflow JSON (trong chat)

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

### 10.3. Gate policy summary

- Blocking: security critical, lint fail (exit 1), test fail (exit 1).
- Advisory: bundle, tech debt, suggestions, impact, quality trend, UX/a11y, Lighthouse, Playwright.
- Optional scripts thiếu tool phải trả warning/error JSON có hướng dẫn cài đặt, không crash.

## 11. Recommended team process

1. Tạo branch theo feature/fix.
2. Trước khi code luôn analyze intent + xác nhận scope.
3. Task lớn phải có plan file được approve.
4. Commit nhỏ, message rõ.
5. Trước merge luôn chạy quality gate.
6. Task kiến trúc quan trọng phải log decision để tránh lặp tranh luận.

## 12. Troubleshooting

### Không thấy skill trong Codex

- Kiểm tra đúng path `~/.codex/skills`.
- Kiểm tra mỗi skill có đủ `SKILL.md` và `agents/openai.yaml`.
- Reload session/extension.

### Script báo `no_git` hoặc không đọc được diff

- Chạy trong đúng git repository.
- Kiểm tra `git status` và quyền truy cập thư mục.

### Lighthouse không chạy

- Cài tool: `npm install -g lighthouse` hoặc dùng `npx lighthouse`.
- Đảm bảo URL đã chạy thật (`http://localhost:3000`...).

### Playwright chưa cài

- Khởi tạo: `npm init playwright@latest`
- Cài browser: `npx playwright install chromium`

### Python script không chạy

- Kiểm tra `python --version`.
- Ưu tiên Python 3.8+.

## 13. Security và privacy

- Dữ liệu memory được lưu local trong `<project-root>/.codex/`.
- File handoff/summary có thể chứa thông tin nhạy cảm.
- Luôn review nội dung trước khi share ra ngoài.

## 14. Tài liệu bổ sung

- Hướng dẫn tiếng Việt chi tiết: `docs/huong-dan-su-dung-codex-skill-pack-v3-vi.md`
- Policy gate: `skills/codex-execution-quality-gate/references/gate-policy.md`
- Rule domain: `skills/codex-domain-specialist/references/`

---

Nếu bạn muốn mở rộng pack, nên làm theo nguyên tắc:
- thêm behavior trước trong `SKILL.md`,
- chỉ thêm script khi cần thao tác tool/runtime thật,
- giữ output contract JSON ổn định để dễ integrate vào workflow dev.

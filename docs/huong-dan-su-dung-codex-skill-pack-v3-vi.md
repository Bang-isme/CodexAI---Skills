# Hướng Dẫn Sử Dụng Codex Skill Pack v3 Cho Developer Việt

## 1. Mục tiêu của bộ skill

Bộ skill này giúp Codex làm việc giống một AI engineering copilot có quy trình rõ ràng:

- Hiểu đúng yêu cầu trước khi code
- Tách việc lớn thành workflow có kiểm soát
- Code theo luật domain
- Không quên docs và quality gate
- Giảm trả lời lan man, tăng tính "ship được"

Kết quả mong đợi:

- Ít rework do hiểu sai bài toán
- Ít bug lọt do thiếu test/gate
- Đội dev có format làm việc thống nhất

## 2. Kiến trúc instruction-first (vì sao khác script pipeline)

Codex extension hoạt động theo mô hình:

1. Đọc instruction từ `SKILL.md`
2. Chọn hành vi phù hợp theo ngữ cảnh
3. Chỉ chạy script ở các phần AI không làm native tốt

Trong pack này:

- Lõi hành vi: `SKILL.md`
- Utility scripts:
  - mapping docs theo git diff
  - gate lint/test
  - security scan
  - bundle/dependency check

## 3. Danh sách 7 skills và vai trò

1. `codex-master-instructions`
- Luật tổng: phân loại request, quy tắc clean code, self-check trước khi kết thúc.

2. `codex-intent-context-analyzer`
- Phân tích prompt thành JSON chuẩn:
  - `intent`, `goal`, `pain_points`, `constraints`, `missing_info`, `normalized_prompt`, `complexity`
- Bật Socratic Gate cho request phức tạp.

3. `codex-workflow-autopilot`
- Mapping intent sang workflow thực thi.
- Có behavioral modes và BMAD phases cho bài toán lớn.

4. `codex-domain-specialist`
- Tự áp luật theo domain:
  - frontend, backend, mobile, debugging, security

5. `codex-docs-change-sync`
- Map code changes -> docs candidates (report-only trong MVP).

6. `codex-execution-quality-gate`
- Phase X verification:
  - lint/test
  - security scan
  - bundle/dependency check

7. `codex-plan-writer`
- Sinh file plan `{task-slug}.md` cho yêu cầu complex.

## 4. Cài đặt bộ skill vào Codex

### 4.1. Đường dẫn chuẩn

- Windows: `C:\Users\<user>\.codex\skills\`
- macOS/Linux: `~/.codex/skills/`

### 4.2. Copy từ repo này

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### 4.3. Kiểm tra nhanh

- Mở lại Codex extension session.
- Thử explicit trigger:
  - `$codex-intent-context-analyzer`
  - `$codex-workflow-autopilot`
  - `$codex-execution-quality-gate`

Nếu extension nhận skill và trả về format phù hợp thì cài đặt thành công.

## 5. Cách dùng theo workflow developer

## 5.1. Luồng chuẩn cho feature nhỏ (simple)

1. User nêu yêu cầu.
2. Intent analyzer phân tích nhanh.
3. Workflow autopilot sinh steps ngắn.
4. Domain specialist áp rule đúng stack.
5. Implement.
6. Quality gate trước khi chốt.

Prompt gợi ý:

```text
$codex-intent-context-analyzer
Mình cần thêm filter theo trạng thái đơn hàng ở trang admin React, có test cơ bản.
```

Sau khi confirm intent:

```text
$codex-workflow-autopilot
Dựa trên intent đã xác nhận, tạo workflow để triển khai.
```

## 5.2. Luồng cho task phức tạp (complex)

1. Intent analyzer + Socratic Gate.
2. Workflow autopilot vào BMAD:
   - Analysis
   - Planning
   - Solutioning
   - Implementation
   - Phase X verification
3. Plan writer tạo `{task-slug}.md`.
4. User approve plan.
5. Implement theo task breakdown.
6. Docs sync + quality gate.

Prompt gợi ý:

```text
Build hệ thống phân quyền theo role cho backend Node.js + dashboard React.
Yêu cầu có migration, test, và hướng dẫn vận hành.
```

## 5.3. Luồng fix bug/debug production

1. Trigger debug mode.
2. Reproduce -> isolate -> root-cause.
3. Fix + regression test.
4. Chạy gate và tóm tắt evidence.

Prompt gợi ý:

```text
API login trả 500 ngẫu nhiên. Hãy debug theo quy trình có bằng chứng.
```

## 6. Contract output cần nắm

## 6.1. Intent analysis JSON

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

## 6.2. Workflow JSON

```json
{
  "mode": "brainstorm | implement | debug | review | teach | ship",
  "workflow_type": "build | fix | review | debug | docs",
  "steps": ["step1", "step2"],
  "exit_criteria": ["criterion1"],
  "estimated_scope": "small | medium | large",
  "phase": "analysis | planning | solutioning | implementation | verification"
}
```

## 7. Dùng helper scripts trực tiếp (khi cần)

## 7.1. Docs change sync

Windows:

```powershell
python "$env:USERPROFILE\.codex\skills\codex-docs-change-sync\scripts\map_changes_to_docs.py" --project-root "D:\your-project" --diff-scope auto
```

macOS/Linux:

```bash
python "$HOME/.codex/skills/codex-docs-change-sync/scripts/map_changes_to_docs.py" --project-root "/path/to/project" --diff-scope auto
```

`--diff-scope auto` sẽ thử theo thứ tự:

1. staged
2. unstaged
3. last-commit

## 7.2. Quality gate

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\run_gate.py" --project-root "D:\your-project"
```

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\security_scan.py" --project-root "D:\your-project"
```

```powershell
python "$env:USERPROFILE\.codex\skills\codex-execution-quality-gate\scripts\bundle_check.py" --project-root "D:\your-project"
```

## 8. Quy trình làm việc đề xuất cho team dev

## 8.1. Nhánh và commit

1. Tạo branch theo feature/fix.
2. Dùng analyzer + workflow trước khi code.
3. Code theo task nhỏ, commit nhỏ, message rõ.
4. Chạy gate trước mỗi lần chốt.

## 8.2. Review mindset

Khi review, ưu tiên:

1. Bug và regression risk
2. Thiếu test
3. Security và performance impact
4. Docs lệch so với code

## 8.3. Definition of Done (DoD)

Chỉ coi là xong khi:

- Intent đã confirm
- Workflow đã đi đủ các bước chính
- Gate không còn blocking issue
- Docs quan trọng đã được xem xét

## 9. Troubleshooting thường gặp

1. Không thấy skill trong Codex
- Kiểm tra đúng path `~/.codex/skills`
- Kiểm tra mỗi folder có `SKILL.md` và `agents/openai.yaml`
- Reload extension/session

2. Script Python không chạy
- Kiểm tra `python --version` (khuyến nghị >= 3.8)
- Kiểm tra path script đúng OS

3. `map_changes_to_docs.py` trả `no_git`
- Bạn đang chạy ngoài git repo
- Chuyển `--project-root` vào đúng thư mục có `.git`

4. `run_gate.py` báo không detect lint/test
- Repo chưa có config lint/test
- Bổ sung tooling hoặc chấp nhận warning trong MVP

5. Security scan cảnh báo nhiều
- Script này đang theo hướng an toàn, có thể cảnh báo rộng
- Nên xử lý warning quan trọng trước, sau đó tinh chỉnh rule

## 10. Nâng cấp skill pack an toàn

1. Backup folder hiện tại trong `~/.codex/skills`.
2. Pull phiên bản mới từ repo.
3. Copy đè 7 modules.
4. Chạy smoke test:
   - `map_changes_to_docs.py --diff-scope auto`
   - `run_gate.py --project-root <repo>`
   - `security_scan.py --project-root <repo>`

## 11. Prompt mẫu dùng ngay

1. Phân tích yêu cầu:

```text
$codex-intent-context-analyzer
Tôi muốn refactor module auth để hỗ trợ refresh token và tránh breaking API cũ.
```

2. Tạo workflow:

```text
$codex-workflow-autopilot
Hãy lập workflow cho intent đã confirm, ưu tiên an toàn production.
```

3. Áp domain rules:

```text
$codex-domain-specialist
Task này chạm vào backend routes + frontend auth guard, áp rule liên quan.
```

4. Đồng bộ docs:

```text
$codex-docs-change-sync
Map giúp tôi file docs nào cần cập nhật từ thay đổi hiện tại.
```

5. Chạy gate:

```text
$codex-execution-quality-gate
Chạy Phase X verification trước khi kết luận hoàn thành.
```

6. Viết plan:

```text
$codex-plan-writer
Tạo plan file cho yêu cầu complex này, task nhỏ và có verify rõ ràng.
```

## 12. Kết luận

Nếu áp đúng quy trình, bộ skill v3 giúp Codex làm việc giống một developer có kỷ luật:

- hiểu bài toán trước khi đụng code
- chia việc rõ
- ưu tiên chất lượng và khả năng ship
- hạn chế "làm xong rồi mới vá"

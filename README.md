# Codex Skill Pack v3 (Vietnamese Guide)

Bộ skill này mở rộng Codex theo kiến trúc instruction-first, tập trung vào workflow thực chiến của developer:

- Phân tích intent và bóc tách yêu cầu mơ hồ
- Tự động dựng workflow build/fix/debug/review/docs
- Áp dụng luật theo domain (frontend/backend/mobile/security)
- Đồng bộ gợi ý cập nhật tài liệu theo git diff
- Chạy quality gate trước khi chốt "done"

## Skill modules

1. `codex-master-instructions`
2. `codex-intent-context-analyzer`
3. `codex-workflow-autopilot`
4. `codex-domain-specialist`
5. `codex-docs-change-sync`
6. `codex-execution-quality-gate`
7. `codex-plan-writer`

## Cấu trúc repo

```text
skills/
  codex-master-instructions/
  codex-intent-context-analyzer/
  codex-workflow-autopilot/
  codex-domain-specialist/
  codex-docs-change-sync/
  codex-execution-quality-gate/
  codex-plan-writer/
docs/
  huong-dan-su-dung-codex-skill-pack-v3-vi.md
```

## Đọc hướng dẫn đầy đủ

Xem file:
`docs/huong-dan-su-dung-codex-skill-pack-v3-vi.md`

## Cài nhanh vào Codex

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

macOS/Linux:

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

# Hướng Dẫn Sử Dụng CodexAI Skill Pack

> **Phiên bản**: `12.5.0` | **Cập nhật**: 2026-03-18

---

## 1. Giới Thiệu

CodexAI Skill Pack là bộ kỹ năng giúp Codex hoạt động như **đối tác lập trình chuyên nghiệp** thay vì chỉ trả lời prompt đơn lẻ. Hệ thống này buộc Codex phải tuân theo quy trình rõ ràng: phân tích yêu cầu → lập kế hoạch → tra cứu kiến thức chuyên môn → triển khai → kiểm tra chất lượng → lưu trữ kiến thức.

### Tổng Quan Số Liệu

| Hạng mục | Giá trị |
| --- | --- |
| Kỹ năng (skills) | 14 |
| Script CLI | 36 |
| Tài liệu tham khảo (references) | 146 (66 fullstack + 30 bảo mật + 50 khác) |
| Mẫu khởi tạo (starters) | 29 (19 fullstack + 10 bảo mật) |
| Scrum subagent kit | 10 role briefs + 10 native Codex agents + 7 workflows + 12 aliases + 6 artifact templates |
| Kiểm thử | 83 unit + 47 smoke = 130 bài test |

---

## 2. Kiến Trúc Hệ Thống

```
┌──────────────────────────────────────────────┐
│         Master Instructions (P0)              │
│    Quy tắc hành vi chung, chính sách hoàn thành│
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Intent Analyzer    │  Phân tích yêu cầu
         │  Xác nhận trước khi │  viết code
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Plan Writer        │  (task vừa/lớn)
         │  Chia nhỏ công việc │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Workflow Autopilot │  Chọn luồng xử lý
         │  build/fix/debug/...│
         └──┬────────────┬────┘
            │            │
   ┌────────▼───┐  ┌────▼───────────┐
   │  Domain    │  │  Security      │
   │  Specialist│  │  Specialist    │
   │  59 refs   │  │  30 refs       │
   └────────────┘  └────────────────┘
            │            │
         ┌──▼────────────▼──────┐
         │  Quality Gate         │  Kiểm tra trước khi xong
         │  lint+test+security   │
         └──────────┬───────────┘
                    │
         ┌──────────▼───────────┐
         │  Memory + Git        │  Lưu + Commit
         └──────────────────────┘
```

---

## 3. Cài Đặt

### Windows (PowerShell)

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

### macOS / Linux

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### Xác Nhận Cài Đặt

```bash
# Kiểm tra cấu trúc và CLI quan trọng (47 kiểm tra)
python skills/tests/smoke_test.py --verbose

# Kiểm tra logic (82 bài test)
python -m pytest skills/tests -v
```

---

## 4. Bắt Đầu Nhanh — Các Lệnh Quan Trọng

| Lệnh | Chức năng |
| --- | --- |
| `$codex-genome` | Tạo tài liệu ngữ cảnh dự án (genome) |
| `$codex-intent-context-analyzer` | Phân tích yêu cầu thành JSON có cấu trúc |
| `$codex-workflow-autopilot` | Chọn luồng làm việc phù hợp |
| `$codex-reasoning-rigor` | Ép output bớt generic, tăng reasoning và evidence |
| `$codex-execution-quality-gate` | Chạy kiểm tra chất lượng toàn diện |
| `$output-guard` | Chấm độ generic và độ có-evidence của deliverable |
| `$scrum-install` | Cài bộ Scrum `.agent` và native `.codex/agents` vào project |
| `$story-ready-check` | Kiểm tra story đã đủ rõ để triển khai chưa |
| `$release-readiness` | Chạy ceremony quyết định ship hay chưa |
| `$codex-doctor` | Kiểm tra sức khỏe hệ thống skill |
| `$log-decision` | Ghi lại quyết định kiến trúc |
| `$session-summary` | Tạo báo cáo tổng kết phiên làm việc |
| `$changelog` | Tạo changelog từ lịch sử commit |
| `$teach` | Chế độ giảng dạy — giải thích code |

---

## 5. Quy Trình Làm Việc Khuyến Nghị

### A. Tạo Tính Năng Mới

```
1. 🎯 PHÂN TÍCH  →  Chạy Intent Analyzer
                     Xác định mục tiêu, ràng buộc, độ phức tạp

2. 📋 LẬP KẾ HOẠCH  →  Chạy Plan Writer (nếu task vừa/lớn)
                        Chia thành bước nhỏ 2-5 phút, mỗi bước có cách kiểm tra

3. 🔀 TRA CỨU  →  Domain/Security routing tự động
                   Tải tối đa 4 tài liệu tham khảo phù hợp

4. 💻 TRIỂN KHAI  →  Code theo từng bước trong kế hoạch

5. ✅ KIỂM TRA  →  Chạy Quality Gate
                    Lint + Tests + Security scan + Accessibility

6. 📄 TÀI LIỆU  →  Docs Change Sync tự phát hiện docs cần cập nhật

7. 💾 LƯU  →  Ghi decision, tạo session summary
               Giữ kiến thức cho phiên tiếp theo

8. 🚀 COMMIT  →  Git Autopilot
                  Conventional commit + ký GPG + push
```

### B. Sá»­a Lá»—i (Bugfix)

1. **Tái tạo lỗi** — xác nhận lỗi xảy ra ổn định
2. **Khoanh vùng** — tìm file/function liên quan
3. **Route** — tải tham khảo debugging + domain phù hợp
4. **Sửa tối thiểu** — ưu tiên thay đổi nhỏ để giảm regression
5. **Test** — chạy test liên quan + quality gate
6. **Ghi gốc rễ** — `$log-decision` ghi nguyên nhân vào memory

### C. Phát Hành (Release)

1. Chạy `pytest` + `smoke_test`
2. Chạy quality gate cho project
3. Kiểm tra VERSION và CHANGELOG đồng bộ
4. Commit có ký (signed) + push

---

## 6. Chi Tiết 14 Kỹ Năng

### Nhóm Core — Luôn hoạt động

| Kỹ năng | Nhiệm vụ |
| --- | --- |
| **master-instructions** | Quy tắc hành vi tổng quan — chính sách "xong" phải có bằng chứng, tự dừng sau 3 lần thất bại liên tiếp |
| **intent-context-analyzer** | Phân tích yêu cầu → JSON có cấu trúc. Cổng Socratic: hỏi ≥3 câu cho yêu cầu phức tạp |
| **context-engine** | Tải genome dự án (nếu có) — giúp Codex hiểu cấu trúc, tech stack, convention |

### Nhóm Lập Kế Hoạch

| Kỹ năng | Nhiệm vụ |
| --- | --- |
| **plan-writer** | Tạo kế hoạch chi tiết: mỗi task 2-5 phút, có file cụ thể, cách kiểm tra, cách rollback |
| **workflow-autopilot** | Chọn luồng (build/fix/debug/review/docs) + chế độ hành vi (thinking-partner, devil's-advocate, teach) |
| **reasoning-rigor** | Chống output generic: ép task contract, evidence ladder, monitoring loop, và output contract có thể kiểm chứng |

### Nhóm Scrum & Điều Phối

| Kỹ năng | Nhiệm vụ |
| --- | --- |
| **scrum-subagents** | Cài bộ `.agent` theo SCRUM cho từng dự án, đồng thời render native Codex custom agents vào `.codex/agents`: Product Owner, Scrum Master, architect, dev, QA, security, DevOps, UX + 7 workflow ceremony/release, kèm validator, lệnh `diff/update`, và 12 command alias như `$scrum-install`, `$story-ready-check`, `$retro`, `$release-readiness` |

### Nhóm Kiến Thức Chuyên Sâu

| Kỹ năng | Phạm vi | Refs | Starters |
| --- | --- | ---: | ---: |
| **domain-specialist** | Full-stack: Frontend, Backend, DB, Auth, Architecture, DevOps, Testing | 66 | 19 |
| **security-specialist** | Bảo mật: Network → Infra → Offensive/Defensive → DevSecOps → Compliance → Advanced | 30 | 10 |

**Domain Specialist** routing:
- 12 domain chính (React, Next.js, Backend, Database, Mobile, Security, Auth, Data, Testing, Architecture, Integration, DevOps)
- 45+ tín hiệu routing (ví dụ: "chart, graph" → tải `data-visualization.md`)
- 10 combo (ví dụ: "Build CRUD page" → tải `react-crud-page.jsx` + 3 refs)
- Tối đa 4 tài liệu mỗi lần tải

**Security Specialist** phạm vi:
- v10.0: Network (TCP/IP, firewall, VPN, DNS, SSL, phân đoạn mạng)
- v10.1: Infrastructure (Linux hardening, secrets, containers, cloud)
- v10.2: Offensive/Defensive (OWASP, pentest, vulnerability scan, incident response)
- v10.3: DevSecOps (CI/CD security, SAST/DAST/SCA, IaC, supply chain)
- v10.4: Compliance (ISO 27001, GDPR, SOC 2, mã hóa, PKI)
- v10.5: Advanced (Zero Trust, DDoS, IDS/IPS, audit framework)

### Nhóm Kiểm Tra & Chất Lượng

| Kỹ năng | Nhiệm vụ | Scripts |
| --- | --- | ---: |
| **execution-quality-gate** | Kiểm tra chất lượng: lint, test, security scan, output guard repo-aware, strict-output mặc định cho plan/review/handoff, UX, a11y, Lighthouse, tech debt, quality trend có gate/output signals | 16 |
| **project-memory** | Lưu trữ xuyên phiên: quyết định, tóm tắt, handoff, genome, changelog, growth report | 11 |
| **docs-change-sync** | Phát hiện tài liệu cần cập nhật khi code thay đổi | 1 |
| **git-autopilot** | Commit tự động: Conventional Commits + ký GPG + gate trước khi push | 1 |
| **doc-renderer** | Chuyển DOCX → PDF → PNG để kiểm tra layout | 1 |

---

## 7. Kiểm Soát Chất Lượng

Quality Gate gồm các lớp kiểm tra:

| Ưu tiên | Kiểm tra | Chặn hoàn thành? |
| --- | --- | --- |
| P0 | Lint, phát hiện secret, kiểm tra debug code | ✅ Có |
| P1 | Chạy test liên quan (smart selection) | ✅ Có |
| P2 | Security scan | ✅ Có |
| P3 | Dự đoán ảnh hưởng (blast radius) | ⚠️ Cảnh báo |
| P4-P6 | Tech debt, đề xuất cải thiện, xu hướng chất lượng | ℹ️ Tham khảo |
| P7-P9 | UX audit, accessibility, Lighthouse | ⚠️ Cảnh báo |

**Quy tắc vàng**: Không được kết luận "xong" nếu kiểm tra blocking chưa pass.

---

## 8. Xử Lý Sự Cố

### Skill không được nhận diện
- Kiểm tra đường dẫn `~/.codex/skills/`
- Đảm bảo mỗi skill có file `SKILL.md` với YAML frontmatter hợp lệ
- Mở phiên Codex mới (skill chỉ được tải khi khởi tạo phiên)

### Script lỗi do thiếu git context
- Truyền đúng `--project-root` trỏ đến thư mục gốc project
- Đảm bảo chạy trong repo có thư mục `.git`
- Kiểm tra `git status` — một số script cần staged changes

### Badge "Verified" không hiện trên GitHub
- Khóa GPG phải được thêm vào GitHub: Settings → SSH and GPG Keys
- Commit phải được ký (`git commit -S`)
- Email trên commit phải khớp với identity GitHub

### Quality Gate liên tục fail
- Chạy `$codex-doctor` để kiểm tra cài đặt
- Kiểm tra xem script có thiếu dependency không (Node.js, npm packages)
- Circuit breaker: sau 3 lần thất bại liên tiếp, Codex tự dừng và yêu cầu đánh giá lại

### Genome cũ / không chính xác
- Kiểm tra timestamp trong `genome.md`
- Sử dụng `$codex-genome --force` để tạo lại
- Nếu số file thực tế khác >20% so với genome, Codex sẽ tự đề xuất refresh

---

## 9. Thực Hành Tốt

1. **Bắt đầu bằng intent, không code ngay** — Intent Analyzer giúp tránh hiểu nhầm từ đầu
2. **Task lớn bắt buộc có plan** — Plan Writer chia task thành bước có thể kiểm tra
3. **Chạy gate trước khi commit** — Quality Gate bắt lỗi trước khi code lên production
4. **Ghi decision khi đổi kiến trúc** — `$log-decision` giúp team hiểu "tại sao" không chỉ "cái gì"
5. **Giữ VERSION, CHANGELOG, genome đồng bộ** — tránh mismatch gây nhầm lẫn
6. **Dùng genome cho project lớn** — giảm hallucination đáng kể cho repo 50+ files
7. **Handoff cuối phiên** — `$session-summary` hoặc `$handoff` để phiên sau tiếp tục mượt

---

## 10. Cấu Trúc Repository

```
CodexAI---Skills/
├── README.md                     ← Tổng quan (English)
├── LICENSE                       ← MIT
├── docs/
│   └── huong-dan-vi.md           ← File này
└── skills/
├── VERSION                   ← 12.5.0
    ├── CHANGELOG.md              ← Lịch sử phiên bản
    ├── README.md                 ← Chi tiết kỹ thuật
    ├── tests/                    ← 130 bài test
    ├── codex-reasoning-rigor/
    ├── codex-master-instructions/
    ├── codex-intent-context-analyzer/
    ├── codex-context-engine/
    ├── codex-plan-writer/
    ├── codex-workflow-autopilot/
    ├── codex-domain-specialist/  ← 59 refs + 19 starters
    ├── codex-security-specialist/← 30 refs + 10 starters
    ├── codex-execution-quality-gate/ ← 16 scripts
    ├── codex-project-memory/     ← 11 scripts
    ├── codex-docs-change-sync/
    ├── codex-git-autopilot/
    ├── codex-doc-renderer/
    └── codex-scrum-subagents/
```

---

## 11. Tài Liệu Liên Quan

| Tài liệu | Nội dung |
| --- | --- |
| [README.md](../README.md) | Tổng quan công khai (English) |
| [skills/README.md](../skills/README.md) | Chi tiết kỹ thuật nội bộ, tất cả lệnh, hướng dẫn tuỳ chỉnh |
| [CHANGELOG.md](../skills/CHANGELOG.md) | Lịch sử phiên bản từ v1.0 đến v12.5.0 |

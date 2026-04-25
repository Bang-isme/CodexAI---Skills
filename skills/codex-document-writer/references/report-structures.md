# Report Structures

Use this reference when writing formal reports, project reports, academic-style reports, or professional deliverables. Each structure includes the section order, what to put in each section, and common mistakes.

## Report Type Selection

| Report Purpose | Use Structure | Key Differentiator |
|---|---|---|
| Presenting project progress | Progress Report | Timeline-oriented, deliverable status |
| Analyzing a problem with data | Analytical Report | Evidence → finding → recommendation |
| Proposing a solution | Proposal | Problem → solution → cost → timeline |
| Comparing options | Comparison Report | Decision matrix, pros/cons framework |
| Documenting research | Research Report | Methodology → data → analysis → conclusion |
| Summarizing a sprint/release | Sprint Report | Goals → achieved → blocked → metrics |
| Documenting an incident | Incident Report | Timeline → root cause → impact → remediation |
| Academic/university assignment | Academic Report | Formal structure with references |

## Progress Report

```markdown
# <Project Name> — Progress Report
**Period:** <date range>  |  **Author:** <name>  |  **Status:** 🟢 On Track / 🟡 At Risk / 🔴 Blocked

## Executive Summary
<2-3 sentences: what was planned, what was achieved, what's next.>

## Deliverable Status

| Deliverable | Planned Date | Status | % Complete | Notes |
|---|---|---|---|---|
| <item> | <date> | ✅ Done / 🔄 In Progress / ❌ Blocked | <n>% | <context> |

## Key Accomplishments
- <Specific achievement with measurable result.>

## Issues & Risks

| Issue | Impact | Severity | Mitigation | Owner |
|---|---|---|---|---|
| <issue> | <effect on timeline/quality> | High/Med/Low | <action> | <name> |

## Metrics

| Metric | Target | Actual | Trend |
|---|---|---|---|
| <metric> | <target> | <actual> | ↑ / → / ↓ |

## Next Period Plan
- <Planned deliverable with target date.>

## Blockers Requiring Escalation
- <Blocker that needs management decision.>
```

## Analytical Report

```markdown
# <Analysis Topic>
**Date:** <date>  |  **Author:** <name>

## Purpose
This analysis examines <subject> to determine <specific question> for <audience>.

## Methodology
- Data sources: <where the data came from>
- Analysis period: <time range>
- Tools used: <specific tools>
- Limitations: <what was not analyzed>

## Key Findings

### Finding 1: <Title>
**Evidence:** <data/chart/command output>
**Implication:** <what this means for the project>

### Finding 2: <Title>
**Evidence:** <data/chart/command output>
**Implication:** <what this means for the project>

## Data Summary

| Dimension | Before | After | Change |
|---|---|---|---|
| <metric> | <value> | <value> | <+/-/%> |

## Recommendations
1. <Action> because <evidence-based reason>. **Priority:** High/Med/Low.
2. <Action> because <reason>. **Priority:** High/Med/Low.

## Appendix
- <Raw data, full command outputs, or detailed calculations.>
```

## Proposal

```markdown
# Proposal: <Solution Name>
**Date:** <date>  |  **Author:** <name>  |  **For:** <decision maker>

## Problem Statement
<What is wrong, who is affected, what is the cost of inaction.>

## Proposed Solution
<What will be built/changed, how it addresses the problem.>

## Architecture Overview
<Mermaid diagram or description of the technical approach.>

## Scope

| In Scope | Out of Scope |
|---|---|
| <item> | <item> |

## Timeline

| Phase | Duration | Deliverable |
|---|---|---|
| <phase> | <weeks> | <output> |

## Cost Estimate

| Item | One-Time Cost | Monthly Cost |
|---|---|---|
| <item> | <amount> | <amount> |
| **Total** | **<sum>** | **<sum>** |

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| <risk> | High/Med/Low | High/Med/Low | <action> |

## Success Criteria
- <Measurable condition that proves the solution works.>

## Decision Required
<Approve / Reject / Modify — with deadline.>
```

## Sprint Report

```markdown
# Sprint <N> Report
**Sprint Goal:** <one sentence>
**Period:** <start> – <end>  |  **Team:** <team name>

## Sprint Summary

| Metric | Value |
|---|---|
| Stories planned | <n> |
| Stories completed | <n> |
| Story points committed | <n> |
| Story points delivered | <n> |
| Velocity | <n> |
| Bugs found | <n> |
| Bugs fixed | <n> |

## Completed Stories

| Story | Points | Assignee | Notes |
|---|---|---|---|
| <title> | <pts> | <name> | <context> |

## Incomplete / Carried Over

| Story | Reason | Action |
|---|---|---|
| <title> | <blocker> | <carry to Sprint N+1 / descoped> |

## Technical Debt

| Item | Severity | Sprint to Address |
|---|---|---|
| <debt> | High/Med/Low | <planned sprint> |

## Retrospective Highlights
- **What went well:** <item>
- **What to improve:** <item>
- **Action item:** <specific action with owner>

## Next Sprint Preview
- Sprint Goal: <next goal>
- Key stories: <list>
```

## Incident Report

```markdown
# Incident Report: <Title>
**Severity:** P1/P2/P3  |  **Date:** <date>  |  **Duration:** <minutes/hours>
**Author:** <name>  |  **Status:** Resolved / Monitoring

## Timeline

| Time | Event |
|---|---|
| <HH:MM> | <what happened> |
| <HH:MM> | <detection / alert triggered> |
| <HH:MM> | <response action taken> |
| <HH:MM> | <resolution confirmed> |

## Impact
- Users affected: <count or percentage>
- Services affected: <list>
- Data loss: <yes/no — details>
- Revenue impact: <estimate if applicable>

## Root Cause
<Specific technical cause, not "human error".>

## Resolution
<What was done to fix it, with specific commands/changes.>

## Corrective Actions

| Action | Owner | Deadline | Status |
|---|---|---|---|
| <preventive action> | <name> | <date> | ❌ Not Started / 🔄 In Progress / ✅ Done |

## Lessons Learned
- <Specific lesson with concrete follow-up.>
```

## Academic Report (Vietnamese-friendly)

```markdown
# <Tiêu đề báo cáo>

## Thông tin
- **Môn học:** <tên môn>
- **Giảng viên:** <tên GV>
- **Sinh viên:** <tên SV> — <MSSV>
- **Ngày nộp:** <ngày>

## Mục lục
1. Giới thiệu
2. Cơ sở lý thuyết
3. Phương pháp thực hiện
4. Kết quả
5. Phân tích & đánh giá
6. Kết luận
7. Tài liệu tham khảo

## 1. Giới thiệu
### 1.1. Đặt vấn đề
<Bối cảnh và lý do chọn đề tài.>

### 1.2. Mục tiêu
- <Mục tiêu cụ thể, đo lường được.>

### 1.3. Phạm vi
- **Trong phạm vi:** <những gì sẽ thực hiện>
- **Ngoài phạm vi:** <những gì không thực hiện>

## 2. Cơ sở lý thuyết
<Lý thuyết nền tảng, công nghệ sử dụng, và tài liệu liên quan.>

## 3. Phương pháp thực hiện
### 3.1. Kiến trúc hệ thống
<Sơ đồ kiến trúc — Mermaid flowchart hoặc C4.>

### 3.2. Công nghệ sử dụng

| Thành phần | Công nghệ | Lý do chọn |
|---|---|---|
| Frontend | <tech> | <reason> |
| Backend | <tech> | <reason> |
| Database | <tech> | <reason> |

### 3.3. Quy trình phát triển
<Sơ đồ Gantt hoặc timeline.>

## 4. Kết quả
### 4.1. Chức năng đã hoàn thành
<Screenshot hoặc mô tả từng chức năng.>

### 4.2. Kết quả kiểm thử

| Test Case | Input | Expected | Actual | Status |
|---|---|---|---|---|
| <TC> | <input> | <expected> | <actual> | ✅/❌ |

## 5. Phân tích & đánh giá
### 5.1. Ưu điểm
### 5.2. Hạn chế
### 5.3. Hướng phát triển

## 6. Kết luận
<Tóm tắt kết quả đạt được so với mục tiêu ban đầu.>

## 7. Tài liệu tham khảo
1. <Tác giả>, "<Tiêu đề>", <Nguồn>, <Năm>.
```

## Report Quality Checklist

Before delivering any report:

- [ ] Does the first section answer the reader's primary question?
- [ ] Is every claim backed by evidence (data, command output, file reference)?
- [ ] Are tables used for comparisons, not for narratives?
- [ ] Does every diagram have a caption and answer a specific question?
- [ ] Are metrics shown with target vs actual, not just current values?
- [ ] Is there a clear "Next Steps" or "Required Decision" section?
- [ ] Are risks listed with severity AND mitigation, not just the risk name?
- [ ] For Vietnamese reports: are section headings in proper Vietnamese labels?
- [ ] Is the report scannable? (Can someone read only headings and tables to get the gist?)
- [ ] Are all acronyms defined on first use?

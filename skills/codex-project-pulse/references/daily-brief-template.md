# Daily Brief Template

Format rules, generation protocol, and examples for the daily brief — the primary output of `$today` / `$pulse`.

## Generation Protocol

### Data Collection (in order)

```
1. READ .codex/pulse/sprint-state.json
   → Sprint name, goal, dates, story statuses, metrics

2. READ .codex/pulse/priority-queue.json
   → Today's recommended work order

3. READ .codex/pulse/blockers.json
   → Active blockers, stale detection, escalation needs

4. READ .codex/pulse/risk-register.json
   → Active risks, severity changes

5. READ .codex/pulse/milestones.json
   → Upcoming deadlines, readiness status

6. READ latest .codex/sessions/*.json (if exists)
   → Yesterday's progress summary

7. RUN git log --since=yesterday --oneline (if git repo)
   → Recent commits for progress tracking

8. CHECK project quality signals (if test/lint commands exist)
   → Test pass rate, lint errors, known issues
```

### Calculation Rules

```
sprint_progress_pct = stories_done / stories_total × 100
time_elapsed_pct = (today - start_date) / (end_date - start_date) × 100

velocity_status:
  if sprint_progress_pct >= time_elapsed_pct: "On track" 🟢
  if sprint_progress_pct >= time_elapsed_pct - 15: "Slightly behind" 🟡
  else: "Behind schedule" 🔴

blocker_alert:
  any blocker age > 2 days: "Stale — needs escalation" 🔴
  any blocker age > 1 day: "Aging — follow up" 🟡
  
milestone_alert:
  days_remaining <= 3: 🔴 Urgent
  days_remaining <= 7: 🟡 Approaching
  days_remaining > 7: 🟢 Normal
```

## Template

```markdown
# 📊 Daily Brief — [YYYY-MM-DD, Day Name]

## Sprint [N]: [Goal]

| Metric | Value |
|---|---|
| **Progress** | [X]/[Y] stories ([Z]%) |
| **Points** | [delivered]/[total] points |
| **Time** | Day [D]/[T] ([P]% elapsed) |
| **Status** | [🟢 On track / 🟡 Slightly behind / 🔴 Behind] |

### Progress Bar
```
[████████░░░░░░░░░░░░] 40% stories | Day 7/10 (70% time)
     ⚠️ Progress lagging behind time
```

### Story Board

| Status | ID | Title | Owner | Points |
|---|---|---|---|---|
| ✅ Done | AUTH-001 | User login | @dev-a | 3 |
| ✅ Done | AUTH-002 | User register | @dev-a | 2 |
| ✅ Done | AUTH-003 | JWT refresh | @dev-a | 3 |
| 🔄 WIP | CART-005 | Fix rounding | @dev-a | 2 |
| 🔴 Blocked | PAY-001 | Stripe checkout | @dev-b | 5 |
| 📋 Todo | ORDER-002 | Confirm email | — | 3 |
| 📋 Todo | PAY-003 | Payment history | — | 3 |

---

## 🔴 Blockers ([count])

| Story | Blocker | Age | Status |
|---|---|---|---|
| PAY-001 | Waiting Stripe API key | 3 days | ⚠️ STALE — escalate to @team-lead |

**Recommended action:** Message @team-lead directly. If no response by EOD, create test-mode key as workaround.

---

## ⚠️ Active Risks ([count])

| Risk | Severity | Status | Mitigation |
|---|---|---|---|
| Payment may miss demo | 🔴 High | Monitoring | Prepare mock demo fallback |

---

## ⏰ Deadlines

| Milestone | Date | Days Left | Readiness |
|---|---|---|---|
| Sprint 3 Demo | 2026-04-25 | 4 days | 🟡 At risk (PAY-001 blocked) |
| MVP Launch | 2026-05-15 | 24 days | 🟢 On track |

---

## 📈 Quality Pulse

| Signal | Current | Previous | Trend |
|---|---|---|---|
| Test pass rate | 47/47 (100%) | 45/45 (100%) | → Stable |
| Lint errors | 0 | 0 | → Clean |
| Tech debt signals | 19 | 23 | ↓ Improving |
| Security findings | 0 critical | 0 critical | → Clean |

---

## 📋 Today's Priorities

1. 🔴 **Unblock PAY-001** — Contact @team-lead for Stripe API key (15 min)
2. 🟡 **Continue CART-005** — Complete rounding fix + regression test (2h)
3. 🟢 **Start ORDER-002** — Set up email service (4h)

---

## 💡 Yesterday's Progress

- Completed JWT refresh token rotation (AUTH-003)
- PR #42 merged — 5 tests added
- Started investigating cart rounding issue
- Committed: 3 commits, 12 files changed

---

## 🧠 Agent Assessment

**Overall:** Sprint is at risk due to PAY-001 blocker (3 days stale). 
If PAY-001 unblocked today, sprint goal is still achievable.
If not unblocked by tomorrow, recommend scope cut: defer PAY-003 to Sprint 4.

**Confidence:** Medium — depends on external blocker resolution.
```

## Quality Rules for Daily Brief

### Must Include
- [ ] Sprint progress with percentage AND time elapsed comparison
- [ ] ALL active blockers with age and escalation status
- [ ] ALL milestones within 14 days with readiness
- [ ] Prioritized action list for today (max 3-5 items)
- [ ] Yesterday's progress (from session summary or git log)
- [ ] Agent's honest assessment of sprint health

### Must NOT Include
- Vague statements ("things are going well")
- Progress without comparison to time ("40% done" without "70% time elapsed")
- Blockers without age tracking
- Priorities without reasoning
- Quality signals without trend direction

### Tone Rules
- State facts first, then assessment
- Flag bad news prominently (blockers, deadline risks)
- Be specific about recommended actions (who, what, when)
- Include confidence level for forward-looking statements
- Never say "on track" if blockers exist for sprint-goal stories

## Vietnamese Daily Brief

When presenting in Vietnamese:

```markdown
# 📊 Báo cáo hàng ngày — [Ngày]

## Sprint [N]: [Mục tiêu]

| Chỉ số | Giá trị |
|---|---|
| **Tiến độ** | [X]/[Y] stories ([Z]%) |
| **Điểm** | [đã hoàn thành]/[tổng] điểm |
| **Thời gian** | Ngày [D]/[T] ([P]% đã qua) |
| **Trạng thái** | [🟢 Đúng tiến độ / 🟡 Hơi chậm / 🔴 Chậm tiến độ] |

## 🔴 Chặn ([số lượng])
...

## 📋 Ưu tiên hôm nay
1. 🔴 **Gỡ chặn PAY-001** — ...
2. 🟡 **Tiếp tục CART-005** — ...

## 🧠 Đánh giá
**Tổng quan:** Sprint đang gặp rủi ro do PAY-001 bị chặn 3 ngày...
```

## Edge Cases

### No sprint initialized

```markdown
# 📊 Project Status

⚠️ No active sprint found.

**Available actions:**
- `$sprint-init` to start a new sprint
- `$today --no-sprint` to show project health without sprint tracking

**Project health:**
[Show quality signals, recent git activity, open TODOs]
```

### Sprint just started (Day 1)

```markdown
Focus: Sprint planning verification
- [ ] Sprint goal clear and measurable
- [ ] All stories have acceptance criteria
- [ ] No story exceeds 50% of sprint capacity
- [ ] Dependencies identified and communicated
```

### Sprint ending (Last 2 days)

```markdown
⏰ Sprint ending in [N] days

**Completion forecast:**
- [X] stories will complete (currently done or in review)
- [Y] stories at risk (in progress, needs [Z] more days)
- [W] stories likely to carry over

**Recommended action:**
- Focus on completing in-progress stories
- Do NOT start new stories
- Consider scope cut for at-risk items
```

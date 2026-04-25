---
name: retrospective
description: Review how the sprint flowed and define a small set of concrete improvement experiments.
---

# Retrospective

## Lead

`scrum-master`

## Support

Full squad (all active contributors)

## Time-Box

45-60 minutes for a 2-week sprint.

## Steps

1. **Set the stage:** Remind the team this is a safe space for honest feedback.
2. **Gather data:** Each person shares keep/start/stop or uses chosen technique.
3. **Identify patterns:** Group similar items. Look for systemic causes, not symptoms.
4. **Root cause analysis:** For top 2-3 issues, ask "why" until you find the real cause.
5. **Choose experiments:** Select up to 3 concrete experiments for next sprint.
6. **Assign owners:** Each experiment gets one owner and a review date.
7. **Review previous experiments:** Did last sprint's experiments work? Keep, modify, or drop.

## Facilitation Techniques

### Start/Stop/Continue (Simple)

```
🟢 Start doing:
- [New practice to try]

🔴 Stop doing:
- [Practice that hurts productivity]

🔄 Continue doing:
- [Practice that works well]
```

### Mad/Sad/Glad (Emotion-Based)

```
😡 Mad (frustrated by):
- [What caused frustration]

😢 Sad (disappointed by):
- [What fell short of expectations]

😊 Glad (happy about):
- [What went well]
```

### 4Ls (Comprehensive)

```
💖 Loved:     [What the team loved this sprint]
📚 Learned:   [New knowledge or skills gained]
🤷 Lacked:    [What was missing or insufficient]
⏭️ Longed for: [What the team wishes they had]
```

### Sailboat (Visual)

```
⛵ Wind (helping us go faster):
- [Positive forces]

⚓ Anchor (slowing us down):
- [Negative forces]

🪨 Rocks (risks ahead):
- [Potential dangers]

🏝️ Island (our goal):
- [Sprint/product goal]
```

## Experiment Template

```markdown
### Experiment: [Name]

**Problem:** [What's not working — specific, not vague]
**Hypothesis:** If we [change], then [expected improvement] because [reasoning].
**Action:** [Concrete, actionable step]
**Owner:** @[person]
**Measure:** [How we'll know if it worked]
**Review:** Sprint [N+1] retrospective
```

**Example:**
> **Experiment:** Reduce PR review wait time
>
> **Problem:** PRs wait 24-48h for review, blocking story completion.
> **Hypothesis:** If we assign reviewers at PR creation and set 4h SLA, then average review time drops below 8h.
> **Action:** Add reviewer assignment to PR template. Scrum Master tracks review SLA daily.
> **Owner:** @scrum-master
> **Measure:** Average PR review time (currently 36h, target <8h).
> **Review:** Sprint 5 retrospective

## Deliverables

- Retro action list (keep/start/stop or chosen format)
- Top 2-3 experiments with owners and review dates
- Previous experiment review (keep/modify/drop)
- Updated team working agreement (if changed)

## Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| Blame individuals | Focus on process and systems, not people |
| Too many experiments | Max 3 per sprint — focus beats breadth |
| No owners assigned | Every experiment needs one owner |
| Never reviewing experiments | Always check last sprint's experiments first |
| Skipping retro when sprint "went fine" | Good sprints still have improvement opportunities |
| Vague improvements ("communicate better") | Make it specific and measurable |

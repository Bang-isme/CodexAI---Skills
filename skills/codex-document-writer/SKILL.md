---
name: codex-document-writer
description: Draft and revise documents, reports, memos, guides, and formal text with clear structure, reliable tone, and professional formatting.
load_priority: on-demand
---

## TL;DR
Load before writing or revising any document, report, proposal, memo, guide, or long-form explanation. The goal is reader clarity: correct context, full meaning, professional structure, reliable tone, and compact wording without making the reader infer missing intent.

## Activation

1. Activate when the task involves drafting, rewriting, summarizing, formatting, or improving documents, reports, memos, proposals, guides, handoffs, emails, or formal text.
2. Activate on `$doc`, `$report`, `$write`, "soạn tài liệu", "viết báo cáo", "làm văn bản chuyên nghiệp", or "viết rõ ràng hơn".
3. Auto-load with `codex-reasoning-rigor` when the document is decision-heavy, high-stakes, or evidence-based.
4. Auto-load with `codex-doc-renderer` when the deliverable is `.docx`.

## Hard Rules

- Always identify purpose, audience, context, and expected use before choosing wording.
- Start with the document outcome, not background narration.
- Use complete sentences with explicit actor, action, object, and outcome.
- Keep each paragraph focused on one message; do not make the reader infer the point.
- Be detailed where meaning depends on detail, but remove filler, repeated framing, and synonym stacking.
- Use humble, reliable wording: state what is verified, what is inferred, and what remains uncertain.
- Do not overclaim. Avoid "clearly", "obviously", "guaranteed", "always", and "never" unless evidence supports them.
- For Vietnamese, use natural UTF-8 Vietnamese, correct context labels, and professional but readable wording.

## Document Flow

Before drafting:

1. Determine document type and reader.
2. Pick the matching structure from `references/document-types.md`.
3. Apply sentence rules from `references/sentence-quality.md`.
4. Apply reliability rules from `references/tone-reliability.md`.
5. Apply Vietnamese wording rules from `references/vietnamese-style.md` when writing Vietnamese.
6. Apply formatting rules from `references/formatting.md`.

## Reference Files

- `references/document-types.md`: templates for reports, memos, proposals, guides, handoffs, summaries, and executive updates.
- `references/sentence-quality.md`: sentence patterns that keep meaning complete, compact, and easy to read.
- `references/tone-reliability.md`: humility, evidence wording, uncertainty, and confidence calibration.
- `references/vietnamese-style.md`: Vietnamese document labels, wording patterns, and anti-filler rules.
- `references/formatting.md`: professional headings, tables, bullets, spacing, and scan-friendly layout rules.

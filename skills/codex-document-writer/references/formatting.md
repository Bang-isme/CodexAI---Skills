# Formatting Rules

Professional formatting makes the document easier to use. It should reveal structure without adding decoration.

## Heading Order

Use predictable headings:

```markdown
# Document Title

## Purpose
## Summary
## Details
## Evidence
## Risks
## Next Steps
```

For Vietnamese:

```markdown
# Tiêu Đề Tài Liệu

## Mục Đích
## Tóm Tắt
## Nội Dung Chính
## Bằng Chứng
## Rủi Ro
## Bước Tiếp Theo
```

## Bullets

Use bullets for parallel items, not for every sentence.

Good bullets:

- same grammatical shape
- one idea per bullet
- concrete object or action
- no repeated opening phrase

Weak bullets:

- mixed sentence fragments and full paragraphs
- repeated filler
- no owner or action
- too many levels

## Tables

Use tables when the reader must compare items.

```markdown
| Item | Current State | Risk | Next Action |
| --- | --- | --- | --- |
| <system/file/process> | <status> | <risk> | <owner/action> |
```

Do not use a table when the content is a narrative explanation.

## Executive Readability

For reports longer than one page:

- first section: decision or bottom line
- second section: evidence or business impact
- middle sections: details
- final section: action, owner, or unresolved questions

## Markdown Hygiene

- Use one blank line between sections.
- Use code formatting for commands, paths, field names, and exact values.
- Prefer ASCII arrows `->` when output may be read in a terminal.
- Avoid nested bullets unless the document explicitly needs hierarchy.
- Keep list labels stable across related reports.

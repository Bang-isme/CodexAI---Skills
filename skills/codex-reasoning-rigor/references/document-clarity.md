# Document Clarity and Token Economy

Use this reference when the user wants clearer writing, stronger structure, lower token waste, or better Vietnamese output quality.
For full document drafting, reporting, and formal writing workflows, stack `codex-document-writer` and use its document templates first.

## Token Economy

- Remove prompt restatement unless it changes scope or resolves ambiguity.
- Remove repeated framing such as "overall", "in summary", "basically", `nhìn chung`, `về cơ bản`.
- Replace clusters of near-synonyms with one precise term.
- Prefer one explicit claim plus one proof line over three vague support sentences.
- Keep section headers stable so the reader can scan quickly without repeated explanations.

## Sentence Clarity

- One sentence should usually carry one main claim.
- State actor -> action -> object -> outcome in that order when possible.
- If a sentence must be long, keep the dependency chain obvious and avoid nesting multiple caveats.
- Replace abstract verbs like "optimize", "improve", and "enhance" with concrete actions such as "remove", "rename", "run", "compare", or "verify".

## Vietnamese Writing Rules

- Prefer native UTF-8 Vietnamese text, not transliterated or mixed-encoding text.
- Use explicit section labels: `Quyết định`, `Bằng chứng`, `Rủi ro`, `Hiện trạng`, `Bước tiếp theo`.
- Prefer direct verbs: `sửa`, `chạy`, `kiểm tra`, `đối chiếu`, `xác minh`, `chặn`.
- Avoid filler phrases that dilute meaning:
  - `nhìn chung`
  - `về cơ bản`
  - `có thể thấy rằng`
  - `nâng cao chất lượng`
  - `đảm bảo tính ổn định`
  - `giải pháp toàn diện`

## Structure Pattern

Use this default order for decision-heavy outputs:

1. `Quyết định`: what was chosen or what changed.
2. `Bằng chứng`: exact files, commands, counts, or measured results.
3. `Rủi ro`: what remains uncertain or what could regress.
4. `Bước tiếp theo`: what to do next and who or what owns it.

## Rendering Safety

- If a terminal or editor may mangle Unicode punctuation, prefer ASCII separators such as `->`.
- Keep code blocks ASCII unless the content itself must show Vietnamese text.
- If mojibake appears in generated text, treat it as a quality defect, not a cosmetic issue.

# HÃ†Â°Ã¡Â»â€ºng DÃ¡ÂºÂ«n SÃ¡Â»Â­ DÃ¡Â»Â¥ng CodexAI Skill Pack

> **PhiÃƒÂªn bÃ¡ÂºÂ£n**: `12.5.0` | **CÃ¡ÂºÂ­p nhÃ¡ÂºÂ­t**: 2026-03-18

---

## 1. GiÃ¡Â»â€ºi ThiÃ¡Â»â€¡u

CodexAI Skill Pack lÃƒÂ  bÃ¡Â»â„¢ kÃ¡Â»Â¹ nÃ„Æ’ng giÃƒÂºp Codex hoÃ¡ÂºÂ¡t Ã„â€˜Ã¡Â»â„¢ng nhÃ†Â° **Ã„â€˜Ã¡Â»â€˜i tÃƒÂ¡c lÃ¡ÂºÂ­p trÃƒÂ¬nh chuyÃƒÂªn nghiÃ¡Â»â€¡p** thay vÃƒÂ¬ chÃ¡Â»â€° trÃ¡ÂºÂ£ lÃ¡Â»Âi prompt Ã„â€˜Ã†Â¡n lÃ¡ÂºÂ». HÃ¡Â»â€¡ thÃ¡Â»â€˜ng nÃƒÂ y buÃ¡Â»â„¢c Codex phÃ¡ÂºÂ£i tuÃƒÂ¢n theo quy trÃƒÂ¬nh rÃƒÂµ rÃƒÂ ng: phÃƒÂ¢n tÃƒÂ­ch yÃƒÂªu cÃ¡ÂºÂ§u Ã¢â€ â€™ lÃ¡ÂºÂ­p kÃ¡ÂºÂ¿ hoÃ¡ÂºÂ¡ch Ã¢â€ â€™ tra cÃ¡Â»Â©u kiÃ¡ÂºÂ¿n thÃ¡Â»Â©c chuyÃƒÂªn mÃƒÂ´n Ã¢â€ â€™ triÃ¡Â»Æ’n khai Ã¢â€ â€™ kiÃ¡Â»Æ’m tra chÃ¡ÂºÂ¥t lÃ†Â°Ã¡Â»Â£ng Ã¢â€ â€™ lÃ†Â°u trÃ¡Â»Â¯ kiÃ¡ÂºÂ¿n thÃ¡Â»Â©c.

### TÃ¡Â»â€¢ng Quan SÃ¡Â»â€˜ LiÃ¡Â»â€¡u

| HÃ¡ÂºÂ¡ng mÃ¡Â»Â¥c | GiÃƒÂ¡ trÃ¡Â»â€¹ |
| --- | --- |
| KÃ¡Â»Â¹ nÃ„Æ’ng (skills) | 14 |
| Script CLI | 36 |
| TÃƒÂ i liÃ¡Â»â€¡u tham khÃ¡ÂºÂ£o (references) | 146 (66 fullstack + 30 bÃ¡ÂºÂ£o mÃ¡ÂºÂ­t + 50 khÃƒÂ¡c) |
| MÃ¡ÂºÂ«u khÃ¡Â»Å¸i tÃ¡ÂºÂ¡o (starters) | 29 (19 fullstack + 10 bÃ¡ÂºÂ£o mÃ¡ÂºÂ­t) |
| Scrum subagent kit | 10 role briefs + 10 native Codex agents + 7 workflows + 12 aliases + 6 artifact templates |
| Kiá»ƒm thá»­ | 83 unit + 47 smoke = 130 bÃ i test |

---

## 2. KiÃ¡ÂºÂ¿n TrÃƒÂºc HÃ¡Â»â€¡ ThÃ¡Â»â€˜ng

```
Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
Ã¢â€â€š         Master Instructions (P0)              Ã¢â€â€š
Ã¢â€â€š    Quy tÃ¡ÂºÂ¯c hÃƒÂ nh vi chung, chÃƒÂ­nh sÃƒÂ¡ch hoÃƒÂ n thÃƒÂ nhÃ¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                   Ã¢â€â€š
         Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
         Ã¢â€â€š  Intent Analyzer    Ã¢â€â€š  PhÃƒÂ¢n tÃƒÂ­ch yÃƒÂªu cÃ¡ÂºÂ§u
         Ã¢â€â€š  XÃƒÂ¡c nhÃ¡ÂºÂ­n trÃ†Â°Ã¡Â»â€ºc khi Ã¢â€â€š  viÃ¡ÂºÂ¿t code
         Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                   Ã¢â€â€š
         Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
         Ã¢â€â€š  Plan Writer        Ã¢â€â€š  (task vÃ¡Â»Â«a/lÃ¡Â»â€ºn)
         Ã¢â€â€š  Chia nhÃ¡Â»Â cÃƒÂ´ng viÃ¡Â»â€¡c Ã¢â€â€š
         Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                   Ã¢â€â€š
         Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
         Ã¢â€â€š  Workflow Autopilot Ã¢â€â€š  ChÃ¡Â»Ân luÃ¡Â»â€œng xÃ¡Â»Â­ lÃƒÂ½
         Ã¢â€â€š  build/fix/debug/...Ã¢â€â€š
         Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
            Ã¢â€â€š            Ã¢â€â€š
   Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â  Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
   Ã¢â€â€š  Domain    Ã¢â€â€š  Ã¢â€â€š  Security      Ã¢â€â€š
   Ã¢â€â€š  SpecialistÃ¢â€â€š  Ã¢â€â€š  Specialist    Ã¢â€â€š
   Ã¢â€â€š  59 refs   Ã¢â€â€š  Ã¢â€â€š  30 refs       Ã¢â€â€š
   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ  Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
            Ã¢â€â€š            Ã¢â€â€š
         Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
         Ã¢â€â€š  Quality Gate         Ã¢â€â€š  KiÃ¡Â»Æ’m tra trÃ†Â°Ã¡Â»â€ºc khi xong
         Ã¢â€â€š  lint+test+security   Ã¢â€â€š
         Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
                    Ã¢â€â€š
         Ã¢â€Å’Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€“Â¼Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Â
         Ã¢â€â€š  Memory + Git        Ã¢â€â€š  LÃ†Â°u + Commit
         Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€Ëœ
```

---

## 3. CÃƒÂ i Ã„ÂÃ¡ÂºÂ·t

### Windows (PowerShell)

```powershell
Copy-Item -Recurse -Force ".\skills\*" "$env:USERPROFILE\.codex\skills\"
```

### macOS / Linux

```bash
cp -R ./skills/* "$HOME/.codex/skills/"
```

### XÃƒÂ¡c NhÃ¡ÂºÂ­n CÃƒÂ i Ã„ÂÃ¡ÂºÂ·t

```bash
# KiÃ¡Â»Æ’m tra cÃ¡ÂºÂ¥u trÃƒÂºc vÃƒÂ  CLI quan trÃ¡Â»Âng (47 kiÃ¡Â»Æ’m tra)
python skills/tests/smoke_test.py --verbose

# KiÃ¡Â»Æ’m tra logic (82 bÃƒÂ i test)
python -m pytest skills/tests -v
```

---

## 4. BÃ¡ÂºÂ¯t Ã„ÂÃ¡ÂºÂ§u Nhanh Ã¢â‚¬â€ CÃƒÂ¡c LÃ¡Â»â€¡nh Quan TrÃ¡Â»Âng

| LÃ¡Â»â€¡nh | ChÃ¡Â»Â©c nÃ„Æ’ng |
| --- | --- |
| `$codex-genome` | TÃ¡ÂºÂ¡o tÃƒÂ i liÃ¡Â»â€¡u ngÃ¡Â»Â¯ cÃ¡ÂºÂ£nh dÃ¡Â»Â± ÃƒÂ¡n (genome) |
| `$codex-intent-context-analyzer` | PhÃƒÂ¢n tÃƒÂ­ch yÃƒÂªu cÃ¡ÂºÂ§u thÃƒÂ nh JSON cÃƒÂ³ cÃ¡ÂºÂ¥u trÃƒÂºc |
| `$codex-workflow-autopilot` | ChÃ¡Â»Ân luÃ¡Â»â€œng lÃƒÂ m viÃ¡Â»â€¡c phÃƒÂ¹ hÃ¡Â»Â£p |
| `$codex-reasoning-rigor` | Ãƒâ€°p output bÃ¡Â»â€ºt generic, tÃ„Æ’ng reasoning vÃƒÂ  evidence |
| `$codex-execution-quality-gate` | ChÃ¡ÂºÂ¡y kiÃ¡Â»Æ’m tra chÃ¡ÂºÂ¥t lÃ†Â°Ã¡Â»Â£ng toÃƒÂ n diÃ¡Â»â€¡n |
| `$output-guard` | ChÃ¡ÂºÂ¥m Ã„â€˜Ã¡Â»â„¢ generic vÃƒÂ  Ã„â€˜Ã¡Â»â„¢ cÃƒÂ³-evidence cÃ¡Â»Â§a deliverable |
| `$scrum-install` | CÃƒÂ i bÃ¡Â»â„¢ Scrum `.agent` vÃƒÂ  native `.codex/agents` vÃƒÂ o project |
| `$story-ready-check` | KiÃ¡Â»Æ’m tra story Ã„â€˜ÃƒÂ£ Ã„â€˜Ã¡Â»Â§ rÃƒÂµ Ã„â€˜Ã¡Â»Æ’ triÃ¡Â»Æ’n khai chÃ†Â°a |
| `$release-readiness` | ChÃ¡ÂºÂ¡y ceremony quyÃ¡ÂºÂ¿t Ã„â€˜Ã¡Â»â€¹nh ship hay chÃ†Â°a |
| `$codex-doctor` | KiÃ¡Â»Æ’m tra sÃ¡Â»Â©c khÃ¡Â»Âe hÃ¡Â»â€¡ thÃ¡Â»â€˜ng skill |
| `$log-decision` | Ghi lÃ¡ÂºÂ¡i quyÃ¡ÂºÂ¿t Ã„â€˜Ã¡Â»â€¹nh kiÃ¡ÂºÂ¿n trÃƒÂºc |
| `$session-summary` | TÃ¡ÂºÂ¡o bÃƒÂ¡o cÃƒÂ¡o tÃ¡Â»â€¢ng kÃ¡ÂºÂ¿t phiÃƒÂªn lÃƒÂ m viÃ¡Â»â€¡c |
| `$changelog` | TÃ¡ÂºÂ¡o changelog tÃ¡Â»Â« lÃ¡Â»â€¹ch sÃ¡Â»Â­ commit |
| `$teach` | ChÃ¡ÂºÂ¿ Ã„â€˜Ã¡Â»â„¢ giÃ¡ÂºÂ£ng dÃ¡ÂºÂ¡y Ã¢â‚¬â€ giÃ¡ÂºÂ£i thÃƒÂ­ch code |

---

## 5. Quy TrÃƒÂ¬nh LÃƒÂ m ViÃ¡Â»â€¡c KhuyÃ¡ÂºÂ¿n NghÃ¡Â»â€¹

### A. TÃ¡ÂºÂ¡o TÃƒÂ­nh NÃ„Æ’ng MÃ¡Â»â€ºi

```
1. Ã°Å¸Å½Â¯ PHÃƒâ€šN TÃƒÂCH  Ã¢â€ â€™  ChÃ¡ÂºÂ¡y Intent Analyzer
                     XÃƒÂ¡c Ã„â€˜Ã¡Â»â€¹nh mÃ¡Â»Â¥c tiÃƒÂªu, rÃƒÂ ng buÃ¡Â»â„¢c, Ã„â€˜Ã¡Â»â„¢ phÃ¡Â»Â©c tÃ¡ÂºÂ¡p

2. Ã°Å¸â€œâ€¹ LÃ¡ÂºÂ¬P KÃ¡ÂºÂ¾ HOÃ¡ÂºÂ CH  Ã¢â€ â€™  ChÃ¡ÂºÂ¡y Plan Writer (nÃ¡ÂºÂ¿u task vÃ¡Â»Â«a/lÃ¡Â»â€ºn)
                        Chia thÃƒÂ nh bÃ†Â°Ã¡Â»â€ºc nhÃ¡Â»Â 2-5 phÃƒÂºt, mÃ¡Â»â€”i bÃ†Â°Ã¡Â»â€ºc cÃƒÂ³ cÃƒÂ¡ch kiÃ¡Â»Æ’m tra

3. Ã°Å¸â€â‚¬ TRA CÃ¡Â»Â¨U  Ã¢â€ â€™  Domain/Security routing tÃ¡Â»Â± Ã„â€˜Ã¡Â»â„¢ng
                   TÃ¡ÂºÂ£i tÃ¡Â»â€˜i Ã„â€˜a 4 tÃƒÂ i liÃ¡Â»â€¡u tham khÃ¡ÂºÂ£o phÃƒÂ¹ hÃ¡Â»Â£p

4. Ã°Å¸â€™Â» TRIÃ¡Â»â€šN KHAI  Ã¢â€ â€™  Code theo tÃ¡Â»Â«ng bÃ†Â°Ã¡Â»â€ºc trong kÃ¡ÂºÂ¿ hoÃ¡ÂºÂ¡ch

5. Ã¢Å“â€¦ KIÃ¡Â»â€šM TRA  Ã¢â€ â€™  ChÃ¡ÂºÂ¡y Quality Gate
                    Lint + Tests + Security scan + Accessibility

6. Ã°Å¸â€œâ€ž TÃƒâ‚¬I LIÃ¡Â»â€ U  Ã¢â€ â€™  Docs Change Sync tÃ¡Â»Â± phÃƒÂ¡t hiÃ¡Â»â€¡n docs cÃ¡ÂºÂ§n cÃ¡ÂºÂ­p nhÃ¡ÂºÂ­t

7. Ã°Å¸â€™Â¾ LÃ†Â¯U  Ã¢â€ â€™  Ghi decision, tÃ¡ÂºÂ¡o session summary
               GiÃ¡Â»Â¯ kiÃ¡ÂºÂ¿n thÃ¡Â»Â©c cho phiÃƒÂªn tiÃ¡ÂºÂ¿p theo

8. Ã°Å¸Å¡â‚¬ COMMIT  Ã¢â€ â€™  Git Autopilot
                  Conventional commit + kÃƒÂ½ GPG + push
```

### B. SÃ¡Â»Â­a LÃ¡Â»â€”i (Bugfix)

1. **TÃƒÂ¡i tÃ¡ÂºÂ¡o lÃ¡Â»â€”i** Ã¢â‚¬â€ xÃƒÂ¡c nhÃ¡ÂºÂ­n lÃ¡Â»â€”i xÃ¡ÂºÂ£y ra Ã¡Â»â€¢n Ã„â€˜Ã¡Â»â€¹nh
2. **Khoanh vÃƒÂ¹ng** Ã¢â‚¬â€ tÃƒÂ¬m file/function liÃƒÂªn quan
3. **Route** Ã¢â‚¬â€ tÃ¡ÂºÂ£i tham khÃ¡ÂºÂ£o debugging + domain phÃƒÂ¹ hÃ¡Â»Â£p
4. **SÃ¡Â»Â­a tÃ¡Â»â€˜i thiÃ¡Â»Æ’u** Ã¢â‚¬â€ Ã†Â°u tiÃƒÂªn thay Ã„â€˜Ã¡Â»â€¢i nhÃ¡Â»Â Ã„â€˜Ã¡Â»Æ’ giÃ¡ÂºÂ£m regression
5. **Test** Ã¢â‚¬â€ chÃ¡ÂºÂ¡y test liÃƒÂªn quan + quality gate
6. **Ghi gÃ¡Â»â€˜c rÃ¡Â»â€¦** Ã¢â‚¬â€ `$log-decision` ghi nguyÃƒÂªn nhÃƒÂ¢n vÃƒÂ o memory

### C. PhÃƒÂ¡t HÃƒÂ nh (Release)

1. ChÃ¡ÂºÂ¡y `pytest` + `smoke_test`
2. ChÃ¡ÂºÂ¡y quality gate cho project
3. KiÃ¡Â»Æ’m tra VERSION vÃƒÂ  CHANGELOG Ã„â€˜Ã¡Â»â€œng bÃ¡Â»â„¢
4. Commit cÃƒÂ³ kÃƒÂ½ (signed) + push

---

## 6. Chi TiÃ¡ÂºÂ¿t 14 KÃ¡Â»Â¹ NÃ„Æ’ng

### NhÃƒÂ³m Core Ã¢â‚¬â€ LuÃƒÂ´n hoÃ¡ÂºÂ¡t Ã„â€˜Ã¡Â»â„¢ng

| KÃ¡Â»Â¹ nÃ„Æ’ng | NhiÃ¡Â»â€¡m vÃ¡Â»Â¥ |
| --- | --- |
| **master-instructions** | Quy tÃ¡ÂºÂ¯c hÃƒÂ nh vi tÃ¡Â»â€¢ng quan Ã¢â‚¬â€ chÃƒÂ­nh sÃƒÂ¡ch "xong" phÃ¡ÂºÂ£i cÃƒÂ³ bÃ¡ÂºÂ±ng chÃ¡Â»Â©ng, tÃ¡Â»Â± dÃ¡Â»Â«ng sau 3 lÃ¡ÂºÂ§n thÃ¡ÂºÂ¥t bÃ¡ÂºÂ¡i liÃƒÂªn tiÃ¡ÂºÂ¿p |
| **intent-context-analyzer** | PhÃƒÂ¢n tÃƒÂ­ch yÃƒÂªu cÃ¡ÂºÂ§u Ã¢â€ â€™ JSON cÃƒÂ³ cÃ¡ÂºÂ¥u trÃƒÂºc. CÃ¡Â»â€¢ng Socratic: hÃ¡Â»Âi Ã¢â€°Â¥3 cÃƒÂ¢u cho yÃƒÂªu cÃ¡ÂºÂ§u phÃ¡Â»Â©c tÃ¡ÂºÂ¡p |
| **context-engine** | TÃ¡ÂºÂ£i genome dÃ¡Â»Â± ÃƒÂ¡n (nÃ¡ÂºÂ¿u cÃƒÂ³) Ã¢â‚¬â€ giÃƒÂºp Codex hiÃ¡Â»Æ’u cÃ¡ÂºÂ¥u trÃƒÂºc, tech stack, convention |

### NhÃƒÂ³m LÃ¡ÂºÂ­p KÃ¡ÂºÂ¿ HoÃ¡ÂºÂ¡ch

| KÃ¡Â»Â¹ nÃ„Æ’ng | NhiÃ¡Â»â€¡m vÃ¡Â»Â¥ |
| --- | --- |
| **plan-writer** | TÃ¡ÂºÂ¡o kÃ¡ÂºÂ¿ hoÃ¡ÂºÂ¡ch chi tiÃ¡ÂºÂ¿t: mÃ¡Â»â€”i task 2-5 phÃƒÂºt, cÃƒÂ³ file cÃ¡Â»Â¥ thÃ¡Â»Æ’, cÃƒÂ¡ch kiÃ¡Â»Æ’m tra, cÃƒÂ¡ch rollback |
| **workflow-autopilot** | ChÃ¡Â»Ân luÃ¡Â»â€œng (build/fix/debug/review/docs) + chÃ¡ÂºÂ¿ Ã„â€˜Ã¡Â»â„¢ hÃƒÂ nh vi (thinking-partner, devil's-advocate, teach) |
| **reasoning-rigor** | ChÃ¡Â»â€˜ng output generic: ÃƒÂ©p task contract, evidence ladder, monitoring loop, vÃƒÂ  output contract cÃƒÂ³ thÃ¡Â»Æ’ kiÃ¡Â»Æ’m chÃ¡Â»Â©ng |

### NhÃƒÂ³m Scrum & Ã„ÂiÃ¡Â»Âu PhÃ¡Â»â€˜i

| KÃ¡Â»Â¹ nÃ„Æ’ng | NhiÃ¡Â»â€¡m vÃ¡Â»Â¥ |
| --- | --- |
| **scrum-subagents** | CÃƒÂ i bÃ¡Â»â„¢ `.agent` theo SCRUM cho tÃ¡Â»Â«ng dÃ¡Â»Â± ÃƒÂ¡n, Ã„â€˜Ã¡Â»â€œng thÃ¡Â»Âi render native Codex custom agents vÃƒÂ o `.codex/agents`: Product Owner, Scrum Master, architect, dev, QA, security, DevOps, UX + 7 workflow ceremony/release, kÃƒÂ¨m validator, lÃ¡Â»â€¡nh `diff/update`, vÃƒÂ  12 command alias nhÃ†Â° `$scrum-install`, `$story-ready-check`, `$retro`, `$release-readiness` |

### NhÃƒÂ³m KiÃ¡ÂºÂ¿n ThÃ¡Â»Â©c ChuyÃƒÂªn SÃƒÂ¢u

| KÃ¡Â»Â¹ nÃ„Æ’ng | PhÃ¡ÂºÂ¡m vi | Refs | Starters |
| --- | --- | ---: | ---: |
| **domain-specialist** | Full-stack: Frontend, Backend, DB, Auth, Architecture, DevOps, Testing | 66 | 19 |
| **security-specialist** | BÃ¡ÂºÂ£o mÃ¡ÂºÂ­t: Network Ã¢â€ â€™ Infra Ã¢â€ â€™ Offensive/Defensive Ã¢â€ â€™ DevSecOps Ã¢â€ â€™ Compliance Ã¢â€ â€™ Advanced | 30 | 10 |

**Domain Specialist** routing:
- 12 domain chÃƒÂ­nh (React, Next.js, Backend, Database, Mobile, Security, Auth, Data, Testing, Architecture, Integration, DevOps)
- 45+ tÃƒÂ­n hiÃ¡Â»â€¡u routing (vÃƒÂ­ dÃ¡Â»Â¥: "chart, graph" Ã¢â€ â€™ tÃ¡ÂºÂ£i `data-visualization.md`)
- 10 combo (vÃƒÂ­ dÃ¡Â»Â¥: "Build CRUD page" Ã¢â€ â€™ tÃ¡ÂºÂ£i `react-crud-page.jsx` + 3 refs)
- TÃ¡Â»â€˜i Ã„â€˜a 4 tÃƒÂ i liÃ¡Â»â€¡u mÃ¡Â»â€”i lÃ¡ÂºÂ§n tÃ¡ÂºÂ£i

**Security Specialist** phÃ¡ÂºÂ¡m vi:
- v10.0: Network (TCP/IP, firewall, VPN, DNS, SSL, phÃƒÂ¢n Ã„â€˜oÃ¡ÂºÂ¡n mÃ¡ÂºÂ¡ng)
- v10.1: Infrastructure (Linux hardening, secrets, containers, cloud)
- v10.2: Offensive/Defensive (OWASP, pentest, vulnerability scan, incident response)
- v10.3: DevSecOps (CI/CD security, SAST/DAST/SCA, IaC, supply chain)
- v10.4: Compliance (ISO 27001, GDPR, SOC 2, mÃƒÂ£ hÃƒÂ³a, PKI)
- v10.5: Advanced (Zero Trust, DDoS, IDS/IPS, audit framework)

### NhÃƒÂ³m KiÃ¡Â»Æ’m Tra & ChÃ¡ÂºÂ¥t LÃ†Â°Ã¡Â»Â£ng

| KÃ¡Â»Â¹ nÃ„Æ’ng | NhiÃ¡Â»â€¡m vÃ¡Â»Â¥ | Scripts |
| --- | --- | ---: |
| **execution-quality-gate** | KiÃ¡Â»Æ’m tra chÃ¡ÂºÂ¥t lÃ†Â°Ã¡Â»Â£ng: lint, test, security scan, output guard repo-aware, strict-output mÃ¡ÂºÂ·c Ã„â€˜Ã¡Â»â€¹nh cho plan/review/handoff, UX, a11y, Lighthouse, tech debt, quality trend cÃƒÂ³ gate/output signals | 16 |
| **project-memory** | LÃ†Â°u trÃ¡Â»Â¯ xuyÃƒÂªn phiÃƒÂªn: quyÃ¡ÂºÂ¿t Ã„â€˜Ã¡Â»â€¹nh, tÃƒÂ³m tÃ¡ÂºÂ¯t, handoff, genome, changelog, growth report | 11 |
| **docs-change-sync** | PhÃƒÂ¡t hiÃ¡Â»â€¡n tÃƒÂ i liÃ¡Â»â€¡u cÃ¡ÂºÂ§n cÃ¡ÂºÂ­p nhÃ¡ÂºÂ­t khi code thay Ã„â€˜Ã¡Â»â€¢i | 1 |
| **git-autopilot** | Commit tÃ¡Â»Â± Ã„â€˜Ã¡Â»â„¢ng: Conventional Commits + kÃƒÂ½ GPG + gate trÃ†Â°Ã¡Â»â€ºc khi push | 1 |
| **doc-renderer** | ChuyÃ¡Â»Æ’n DOCX Ã¢â€ â€™ PDF Ã¢â€ â€™ PNG Ã„â€˜Ã¡Â»Æ’ kiÃ¡Â»Æ’m tra layout | 1 |

---

## 7. KiÃ¡Â»Æ’m SoÃƒÂ¡t ChÃ¡ÂºÂ¥t LÃ†Â°Ã¡Â»Â£ng

Quality Gate gÃ¡Â»â€œm cÃƒÂ¡c lÃ¡Â»â€ºp kiÃ¡Â»Æ’m tra:

| Ã†Â¯u tiÃƒÂªn | KiÃ¡Â»Æ’m tra | ChÃ¡ÂºÂ·n hoÃƒÂ n thÃƒÂ nh? |
| --- | --- | --- |
| P0 | Lint, phÃƒÂ¡t hiÃ¡Â»â€¡n secret, kiÃ¡Â»Æ’m tra debug code | Ã¢Å“â€¦ CÃƒÂ³ |
| P1 | ChÃ¡ÂºÂ¡y test liÃƒÂªn quan (smart selection) | Ã¢Å“â€¦ CÃƒÂ³ |
| P2 | Security scan | Ã¢Å“â€¦ CÃƒÂ³ |
| P3 | DÃ¡Â»Â± Ã„â€˜oÃƒÂ¡n Ã¡ÂºÂ£nh hÃ†Â°Ã¡Â»Å¸ng (blast radius) | Ã¢Å¡Â Ã¯Â¸Â CÃ¡ÂºÂ£nh bÃƒÂ¡o |
| P4-P6 | Tech debt, Ã„â€˜Ã¡Â»Â xuÃ¡ÂºÂ¥t cÃ¡ÂºÂ£i thiÃ¡Â»â€¡n, xu hÃ†Â°Ã¡Â»â€ºng chÃ¡ÂºÂ¥t lÃ†Â°Ã¡Â»Â£ng | Ã¢â€žÂ¹Ã¯Â¸Â Tham khÃ¡ÂºÂ£o |
| P7-P9 | UX audit, accessibility, Lighthouse | Ã¢Å¡Â Ã¯Â¸Â CÃ¡ÂºÂ£nh bÃƒÂ¡o |

**Quy tÃ¡ÂºÂ¯c vÃƒÂ ng**: KhÃƒÂ´ng Ã„â€˜Ã†Â°Ã¡Â»Â£c kÃ¡ÂºÂ¿t luÃ¡ÂºÂ­n "xong" nÃ¡ÂºÂ¿u kiÃ¡Â»Æ’m tra blocking chÃ†Â°a pass.

---

## 8. XÃ¡Â»Â­ LÃƒÂ½ SÃ¡Â»Â± CÃ¡Â»â€˜

### Skill khÃƒÂ´ng Ã„â€˜Ã†Â°Ã¡Â»Â£c nhÃ¡ÂºÂ­n diÃ¡Â»â€¡n
- KiÃ¡Â»Æ’m tra Ã„â€˜Ã†Â°Ã¡Â»Âng dÃ¡ÂºÂ«n `~/.codex/skills/`
- Ã„ÂÃ¡ÂºÂ£m bÃ¡ÂºÂ£o mÃ¡Â»â€”i skill cÃƒÂ³ file `SKILL.md` vÃ¡Â»â€ºi YAML frontmatter hÃ¡Â»Â£p lÃ¡Â»â€¡
- MÃ¡Â»Å¸ phiÃƒÂªn Codex mÃ¡Â»â€ºi (skill chÃ¡Â»â€° Ã„â€˜Ã†Â°Ã¡Â»Â£c tÃ¡ÂºÂ£i khi khÃ¡Â»Å¸i tÃ¡ÂºÂ¡o phiÃƒÂªn)

### Script lÃ¡Â»â€”i do thiÃ¡ÂºÂ¿u git context
- TruyÃ¡Â»Ân Ã„â€˜ÃƒÂºng `--project-root` trÃ¡Â»Â Ã„â€˜Ã¡ÂºÂ¿n thÃ†Â° mÃ¡Â»Â¥c gÃ¡Â»â€˜c project
- Ã„ÂÃ¡ÂºÂ£m bÃ¡ÂºÂ£o chÃ¡ÂºÂ¡y trong repo cÃƒÂ³ thÃ†Â° mÃ¡Â»Â¥c `.git`
- KiÃ¡Â»Æ’m tra `git status` Ã¢â‚¬â€ mÃ¡Â»â„¢t sÃ¡Â»â€˜ script cÃ¡ÂºÂ§n staged changes

### Badge "Verified" khÃƒÂ´ng hiÃ¡Â»â€¡n trÃƒÂªn GitHub
- KhÃƒÂ³a GPG phÃ¡ÂºÂ£i Ã„â€˜Ã†Â°Ã¡Â»Â£c thÃƒÂªm vÃƒÂ o GitHub: Settings Ã¢â€ â€™ SSH and GPG Keys
- Commit phÃ¡ÂºÂ£i Ã„â€˜Ã†Â°Ã¡Â»Â£c kÃƒÂ½ (`git commit -S`)
- Email trÃƒÂªn commit phÃ¡ÂºÂ£i khÃ¡Â»â€ºp vÃ¡Â»â€ºi identity GitHub

### Quality Gate liÃƒÂªn tÃ¡Â»Â¥c fail
- ChÃ¡ÂºÂ¡y `$codex-doctor` Ã„â€˜Ã¡Â»Æ’ kiÃ¡Â»Æ’m tra cÃƒÂ i Ã„â€˜Ã¡ÂºÂ·t
- KiÃ¡Â»Æ’m tra xem script cÃƒÂ³ thiÃ¡ÂºÂ¿u dependency khÃƒÂ´ng (Node.js, npm packages)
- Circuit breaker: sau 3 lÃ¡ÂºÂ§n thÃ¡ÂºÂ¥t bÃ¡ÂºÂ¡i liÃƒÂªn tiÃ¡ÂºÂ¿p, Codex tÃ¡Â»Â± dÃ¡Â»Â«ng vÃƒÂ  yÃƒÂªu cÃ¡ÂºÂ§u Ã„â€˜ÃƒÂ¡nh giÃƒÂ¡ lÃ¡ÂºÂ¡i

### Genome cÃ…Â© / khÃƒÂ´ng chÃƒÂ­nh xÃƒÂ¡c
- KiÃ¡Â»Æ’m tra timestamp trong `genome.md`
- SÃ¡Â»Â­ dÃ¡Â»Â¥ng `$codex-genome --force` Ã„â€˜Ã¡Â»Æ’ tÃ¡ÂºÂ¡o lÃ¡ÂºÂ¡i
- NÃ¡ÂºÂ¿u sÃ¡Â»â€˜ file thÃ¡Â»Â±c tÃ¡ÂºÂ¿ khÃƒÂ¡c >20% so vÃ¡Â»â€ºi genome, Codex sÃ¡ÂºÂ½ tÃ¡Â»Â± Ã„â€˜Ã¡Â»Â xuÃ¡ÂºÂ¥t refresh

---

## 9. ThÃ¡Â»Â±c HÃƒÂ nh TÃ¡Â»â€˜t

1. **BÃ¡ÂºÂ¯t Ã„â€˜Ã¡ÂºÂ§u bÃ¡ÂºÂ±ng intent, khÃƒÂ´ng code ngay** Ã¢â‚¬â€ Intent Analyzer giÃƒÂºp trÃƒÂ¡nh hiÃ¡Â»Æ’u nhÃ¡ÂºÂ§m tÃ¡Â»Â« Ã„â€˜Ã¡ÂºÂ§u
2. **Task lÃ¡Â»â€ºn bÃ¡ÂºÂ¯t buÃ¡Â»â„¢c cÃƒÂ³ plan** Ã¢â‚¬â€ Plan Writer chia task thÃƒÂ nh bÃ†Â°Ã¡Â»â€ºc cÃƒÂ³ thÃ¡Â»Æ’ kiÃ¡Â»Æ’m tra
3. **ChÃ¡ÂºÂ¡y gate trÃ†Â°Ã¡Â»â€ºc khi commit** Ã¢â‚¬â€ Quality Gate bÃ¡ÂºÂ¯t lÃ¡Â»â€”i trÃ†Â°Ã¡Â»â€ºc khi code lÃƒÂªn production
4. **Ghi decision khi Ã„â€˜Ã¡Â»â€¢i kiÃ¡ÂºÂ¿n trÃƒÂºc** Ã¢â‚¬â€ `$log-decision` giÃƒÂºp team hiÃ¡Â»Æ’u "tÃ¡ÂºÂ¡i sao" khÃƒÂ´ng chÃ¡Â»â€° "cÃƒÂ¡i gÃƒÂ¬"
5. **GiÃ¡Â»Â¯ VERSION, CHANGELOG, genome Ã„â€˜Ã¡Â»â€œng bÃ¡Â»â„¢** Ã¢â‚¬â€ trÃƒÂ¡nh mismatch gÃƒÂ¢y nhÃ¡ÂºÂ§m lÃ¡ÂºÂ«n
6. **DÃƒÂ¹ng genome cho project lÃ¡Â»â€ºn** Ã¢â‚¬â€ giÃ¡ÂºÂ£m hallucination Ã„â€˜ÃƒÂ¡ng kÃ¡Â»Æ’ cho repo 50+ files
7. **Handoff cuÃ¡Â»â€˜i phiÃƒÂªn** Ã¢â‚¬â€ `$session-summary` hoÃ¡ÂºÂ·c `$handoff` Ã„â€˜Ã¡Â»Æ’ phiÃƒÂªn sau tiÃ¡ÂºÂ¿p tÃ¡Â»Â¥c mÃ†Â°Ã¡Â»Â£t

---

## 10. CÃ¡ÂºÂ¥u TrÃƒÂºc Repository

```
CodexAI---Skills/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ README.md                     Ã¢â€ Â TÃ¡Â»â€¢ng quan (English)
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ LICENSE                       Ã¢â€ Â MIT
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ docs/
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ huong-dan-vi.md           Ã¢â€ Â File nÃƒÂ y
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ skills/
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ VERSION                   Ã¢â€ Â 12.5.0
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ CHANGELOG.md              Ã¢â€ Â LÃ¡Â»â€¹ch sÃ¡Â»Â­ phiÃƒÂªn bÃ¡ÂºÂ£n
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ README.md                 Ã¢â€ Â Chi tiÃ¡ÂºÂ¿t kÃ¡Â»Â¹ thuÃ¡ÂºÂ­t
    ├── tests/                    ← 130 bài test
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-reasoning-rigor/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-master-instructions/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-intent-context-analyzer/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-context-engine/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-plan-writer/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-workflow-autopilot/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-domain-specialist/  Ã¢â€ Â 59 refs + 19 starters
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-security-specialist/Ã¢â€ Â 30 refs + 10 starters
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-execution-quality-gate/ Ã¢â€ Â 16 scripts
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-project-memory/     Ã¢â€ Â 11 scripts
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-docs-change-sync/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-git-autopilot/
    Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ codex-doc-renderer/
    Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ codex-scrum-subagents/
```

---

## 11. TÃƒÂ i LiÃ¡Â»â€¡u LiÃƒÂªn Quan

| TÃƒÂ i liÃ¡Â»â€¡u | NÃ¡Â»â„¢i dung |
| --- | --- |
| [README.md](../README.md) | TÃ¡Â»â€¢ng quan cÃƒÂ´ng khai (English) |
| [skills/README.md](../skills/README.md) | Chi tiÃ¡ÂºÂ¿t kÃ¡Â»Â¹ thuÃ¡ÂºÂ­t nÃ¡Â»â„¢i bÃ¡Â»â„¢, tÃ¡ÂºÂ¥t cÃ¡ÂºÂ£ lÃ¡Â»â€¡nh, hÃ†Â°Ã¡Â»â€ºng dÃ¡ÂºÂ«n tuÃ¡Â»Â³ chÃ¡Â»â€°nh |
| [CHANGELOG.md](../skills/CHANGELOG.md) | LÃ¡Â»â€¹ch sÃ¡Â»Â­ phiÃƒÂªn bÃ¡ÂºÂ£n tÃ¡Â»Â« v1.0 Ã„â€˜Ã¡ÂºÂ¿n v12.5.0 |

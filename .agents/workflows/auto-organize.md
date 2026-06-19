---
description: Classify new books from Inbox with an AI Agent (batch processing workflow for Antigravity and Codex)
---

# /auto-organize - Automatic Book Classification (Batch Mode)

> Agent classifies ALL books -> asks the user **once** -> moves files + covers + descriptions + upload. See `SKILL.md` for full details.

## Codex compatibility

- In Codex, the user can invoke `/auto-organize`, `auto-organize`, or ask to classify books in `Inbox/`.
- `view_file` is equivalent to reading the file with a Codex tool or `Get-Content -Raw`.
- `multi_replace_file_content` is equivalent to batch editing with `apply_patch`, then validating JSON.
- `// turbo` lines are Antigravity optimization notes; Codex only needs to run the equivalent command.
- On Windows/PowerShell, use native equivalent commands for `ls`, `mkdir`, and `mv` when needed.

1. Read skill instructions at `.agents/skills/auto-organize/SKILL.md`.

2. Read classification rules at `.agents/skills/auto-organize/prompts/classify_book.md`.

// turbo 3. Scan Inbox and record N new books:

```bash
ls "Inbox/"
```

If empty -> notify the user and stop.

// turbo 4. Normalize file names (dry-run first, `--execute` if needed):

```bash
python scripts/cli.py rename --base-dir .
```

// turbo 5. Generate library structure log:

```bash
python scripts/cli.py structure --base-dir .
```

6. **REQUIRED:** read the full `library_structure.log` (Antigravity: `view_file`; Codex: file-reading tool or `Get-Content -Raw`). Pay attention to the `AVAILABLE CATEGORIES` section.

7. **Batch classify + descriptions** - Process EVERYTHING in memory. Compare against the log and prioritize EXISTING folders. Draft 3-part descriptions. DO NOT ask the user book by book.

8. **Print summary table** -> Ask the user **ONLY ONCE**.

9. Move ALL files in the batch (`mkdir -p` + `mv`). Destination must always start with `Books/`.

// turbo 10. Check dependencies:

```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING"
python -c "from PIL import Image; print('Pillow OK')" 2>&1 || echo "MISSING"
python -c "import docx; print('python-docx OK')" 2>&1 || echo "MISSING"
```

// turbo 11. Generate covers + data.json - **ONLY ONCE**:

```bash
python scripts/cli.py generate --base-dir .
```

// turbo 12. Verify `download_url` (missing = exactly N -> OK, > N -> STOP):

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Missing URL: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

// turbo 12b. **REQUIRED** - Verify `topic` for books in subfolders (for example `Programming_Languages/Java`):

```bash
python -c "import json; d=json.load(open('site/data.json','r',encoding='utf-8')); errors=[(b['title'],b['topic'],b['file_path']) for b in d if b['file_path'].count('/')>=4 and '/'.join(b['file_path'].split('/')[2:-1]).replace('_',' ')!=b['topic']]; print(f'Sub-topic mismatches: {len(errors)}'); [print(f'  - {t} | topic={tp} | path={p}') for t,tp,p in errors]"
```

> If there is a mismatch -> fix `topic` in data.json. Always use the **display name** (spaces), NOT `Snake_Case` (`_`).
> Correct: `"topic": "Programming Languages/Java"` - Wrong: `"topic": "Programming_Languages/Java"`

13. **Insert descriptions** - batch edit all `"description": ""` values at once (Antigravity: `multi_replace_file_content`; Codex: `apply_patch` or suitable CLI).

> **JSON newline:** Use `\n` (single escape) for line breaks, NOT `\\n` (double escape).
> Compare: `"Line 1.\n\nLine 2."` - `"Line 1.\\n\\nLine 2."` is wrong and displays literal `\n`.

// turbo 14. Update the log immediately after classification:

```bash
python scripts/cli.py structure --base-dir .
```

15. **Validate metadata** before upload:

```bash
python scripts/cli.py doctor --base-dir . --strict
```

16. **DRY-RUN upload** (count = N -> OK, > N -> STOP):

```bash
python scripts/cli.py upload --dry-run
```

17. Ask the user for one explicit confirmation before the real upload. Upload new books only after approval:

```bash
python scripts/cli.py upload
```

18. Ask the user for one explicit confirmation before commit/push. Commit + push only after approval:

```bash
git add -A && git commit -m "add: [N] books to library" && git push
```

19. **Report results** to the user (summary table + links).

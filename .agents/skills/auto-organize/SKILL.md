---
name: auto-organize
description: Automatically classify new books in Inbox into the correct category/topic folders with an Antigravity or Codex AI Agent
---

# Auto-Organize Skill - Batch Mode

> **Principle:** Classify EVERYTHING -> ask the user **once** -> move files + covers + descriptions + bulk upload.

## Codex compatibility

This skill is the shared source for Antigravity and Codex.

| Antigravity | Codex |
|-------------|-------|
| `/auto-organize` slash command | The user can invoke `/auto-organize`, `auto-organize`, or describe the request in plain language |
| `view_file` | Use a file-reading tool or `Get-Content -Raw` |
| `multi_replace_file_content` | Use `apply_patch` for batch edits, then validate JSON |
| `mkdir -p` / `mv` | On Windows, use `New-Item -ItemType Directory -Force` / `Move-Item` if aliases are not suitable |

When running with Codex, still follow every guardrail below: ask the user exactly once before bulk move/rename operations, dry-run before upload, and do not run generate a second time until the root cause has been handled.

## Data Protection Rules

| Rule | Details |
|------|---------|
| Run `generate_data.py` ONLY ONCE | If it fails -> fix the root cause; DO NOT rerun blindly |
| Verify PyMuPDF + Pillow | BOTH must be present before generate. Use `python -m pip install` |
| Verify `download_url` | After generate: missing URL count must equal exactly N new books. If > N -> STOP |
| **Verify subfolder `topic`** | After generate: check that books in sub-topics (for example `Java/`) have `topic` containing the full path (`Programming Languages/Java`). If missing -> fix immediately |
| Dry-run upload | REQUIRED before real upload. Count > N -> STOP |
| Lost `download_url` | Restore with: `git checkout site/data.json` |
| **Folder vs Display name** | Folders on disk use `Snake_Case`, but `topic`/`category` fields in `data.json` use display names (spaces). Example: folder `Programming_Languages/Java` -> topic `"Programming Languages/Java"`. NEVER write `_` into `data.json` |

## Execution Workflow

### Steps 1-3: Prepare

1. Read `prompts/classify_book.md` to understand classification rules.
2. Scan `Inbox/`, recording **N = total new books** (.pdf/.epub). If empty -> stop.
3. Normalize names: `python scripts/cli.py rename --base-dir .` -> if needed -> `--execute`.

### Step 4: Context Grounding (REQUIRED)

```bash
python scripts/cli.py structure --base-dir .
```

Then read the full `library_structure.log` (Antigravity: `view_file`; Codex: file-reading tool or `Get-Content -Raw`). Pay attention to the **AVAILABLE CATEGORIES** section at the end - this is the list of existing folders the agent must prioritize.

### Step 5: Batch Classify + Descriptions (in memory)

For each file in Inbox, the agent determines in memory:
- `category_folder` + `topic_folder` (compare against the log, prioritize EXISTING folders)
- `description` written in **O'Reilly style** - 3 natural prose sections, with NO labels:
  1. **Paragraph 1** (context): State the problem/challenge the book addresses
  2. **Paragraph 2** (overview): Introduce the book, author, and approach
  3. **Paragraph 3** (bullets): 4-5 `•` bullets starting with verbs (Master, Build, Learn, Explore, Implement...)

  Separate the 3 sections with `\n\n`. **DO NOT** use labels such as `Context:`, `Overview:`, or `Key Takeaways:`.

**Description language:**
- English filename -> write English
- Vietnamese filename (diacritics or VN patterns: `Ch01_`, `Giao_trinh_`, `PTTKHT`...) -> write Vietnamese

> DO NOT ask the user book by book. Process EVERYTHING, then display the summary.

### Step 6: Show Table + Confirm

Print ONE summary table:

```
| # | File | Category -> Topic | Description (summary) |
```

Ask the user **ONLY ONCE**. If edits are requested -> update in memory -> show the table again.

### Steps 7-8: Move + Dependencies

7. Move the batch: `mkdir -p` + `mv`, using as few commands as practical. Destination must always start with `Books/`.
8. Check dependencies:
```bash
python -c "import fitz; print('PyMuPDF OK')" 2>&1 || echo "MISSING"
python -c "from PIL import Image; print('Pillow OK')" 2>&1 || echo "MISSING"
python -c "import docx; print('python-docx OK')" 2>&1 || echo "MISSING"
```
If missing -> `python -m pip install PyMuPDF Pillow python-docx`. **DO NOT generate while dependencies are missing.**

### Step 9: Generate covers + data.json (ONLY ONCE)

```bash
python scripts/cli.py generate --base-dir .
```

### Step 10: Verify download_url

```bash
python -c "import json; data=json.load(open('site/data.json','r',encoding='utf-8')); missing=[b['title'] for b in data if not b.get('download_url')]; print(f'Missing URL: {len(missing)}'); [print(f'  - {t}') for t in missing]"
```

- Missing == N -> OK. Missing > N -> STOP, `git checkout site/data.json`.

### Step 10b: Verify `topic` for sub-topics (REQUIRED)

```bash
python -c "import json; d=json.load(open('site/data.json','r',encoding='utf-8')); errors=[(b['title'],b['topic'],b['file_path']) for b in d if b['file_path'].count('/')>=4 and '/'.join(b['file_path'].split('/')[2:-1]).replace('_',' ')!=b['topic']]; print(f'Sub-topic mismatches: {len(errors)}'); [print(f'  ERROR {t} | topic={tp} | path={p}') for t,tp,p in errors]"
```

> If there is a mismatch: fix the `topic` field in data.json. Always use the **display name** (spaces), NOT `Snake_Case` (`_`).
> Correct: `"topic": "Programming Languages/Java"`
> Wrong: `"topic": "Programming_Languages/Java"` (creates duplicate topics in the UI)

### Step 11: Insert descriptions in bulk

Use a batch edit to insert ALL `"description": ""` values at once. Antigravity uses `multi_replace_file_content`; Codex uses `apply_patch` or a suitable CLI, then validates JSON. DO NOT manually edit each entry one by one.

> **JSON newline:** Use `\n` (single escape) for line breaks, NOT `\\n` (double escape).
> `"Line 1.\n\nLine 2."` is correct - `"Line 1.\\n\\nLine 2."` is wrong and displays literal `\n`.

### Step 12: Update library_structure.log (REQUIRED)

```bash
python scripts/cli.py structure --base-dir .
```

> The log MUST be updated immediately after classification is complete to avoid duplicate topics next time.

### Step 12b: Validate metadata

```bash
python scripts/cli.py doctor --base-dir . --strict
```

### Steps 13-14: Upload

13. Dry-run: `python scripts/cli.py upload --dry-run` -> count = N -> OK. > N -> STOP.
14. Ask the user for one explicit confirmation, then upload: `python scripts/cli.py upload` (new files only).

### Step 15: Commit + Push

Ask the user for one explicit confirmation before running `git add -A && git commit -m "add: [N] books to library" && git push`.

### Step 16: Report

```
Complete: N books processed

| # | Book | Destination | Cover | Description | Upload |
Upload: N new files (DO NOT re-upload old books)
Links: ?book={id1}, ?book={id2}, ...
```

---
trigger: always_on
glob: "**"
description: Project Rules - guiding principles for the full My Bookshelves development workflow
---

My-Bookshelves is a personal static book library hosted on GitHub Pages.

## 1. CORE PHILOSOPHY

- **Apple-Style UI/UX**: Minimal, glassmorphism (`backdrop-filter: blur(20px)`), generous whitespace, 12-16px border radius, smooth transitions. Light mode by default.
- **Zero-Dependency**: 100% vanilla HTML + CSS + JS (ES6+). NO React/Vue/Tailwind/Bootstrap/jQuery/FontAwesome. System fonts only. Icons = inline SVG or emoji.
- **Storage <= 5MB**: Store PDF/EPUB files on GitHub Releases (tag `storage-v1`), NOT in git. Cover images must be WebP 600px q85 (<80KB). No external resources/CDN.

## 2. PROJECT STRUCTURE

```
Books/{N}_{Category}/{Topic}/book.pdf   # Books (gitignored, stored on Releases)
site/index.html                         # Single-file HTML+CSS, SPA views
site/app.js                             # All JS logic
site/data.json                          # Book metadata (source of truth)
site/assets/covers/*.webp               # Cover images
scripts/*.py                            # Automation scripts
library_structure.log                   # AI context grounding (auto-generated)
```

## 3. NAMING RULES

| Type | Format | Example |
|------|--------|---------|
| Book file | ASCII Snake_Case, no diacritics | `Go_With_Domain.pdf`, `Kien_truc_ung_dung_web.epub` |
| Category | `{N}_Snake_Case` | `1_Computer_Science_Fundamentals` |
| Topic | `Snake_Case` | `Data_Structures_and_Algorithms` |
| Sub-topic | `Topic/SubTopic` (Snake_Case) | `Programming_Languages/Java` |
| Cover image | `Sanitize_Title.webp` | `Head_First_Java_2nd_Edition.webp` |
| Scripts | lowercase_underscore | `generate_data.py` |

Book names: use ONLY `_`; do NOT use spaces/`-`/`+`/`.`. Vietnamese titles must be written without diacritics.

### Warning: Two Naming Forms (Folder vs Display) - Critical

| Context | Format | Example |
|---------|--------|---------|
| **Folder on disk** | `Snake_Case` | `Programming_Languages/Java` |
| **`topic` field in data.json** | Display name (spaces) | `Programming Languages/Java` |
| **`category` field in data.json** | Display name (spaces) | `Computer Science Fundamentals` |

> **NEVER** use `Snake_Case` (underscores `_`) when writing `topic` or `category` values to `data.json`. Always use display names with spaces.
> Wrong: `"topic": "Programming_Languages/Java"`
> Correct: `"topic": "Programming Languages/Java"`

## 4. FRONTEND

- **CSS**: Variables for theming (`--bg`, `--accent`...). Intrinsic responsive layout: `clamp()`, `auto-fill`, `flex-wrap`. Use `@media` only for sidebar/navbar breakpoints.
- **JS**: `querySelector()`, `addEventListener()`, Fetch API. Inline `onclick` only for dynamic HTML.
- **SPA**: View switching (`#home-view`/`#detail-view`), `history.pushState` -> `?book=id`.
- **Pagination**: Dynamic `calculateBooksPerPage()` - a multiple of the column count, recalculated on resize.
- **Cache busting**: `fetch("data.json?v=" + Date.now(), {cache:"no-store"})`.
- **Smoke checks**: Run `python scripts/cli.py smoke --base-dir .` after frontend refactors.

## 5. PYTHON SCRIPTS

- PEP 8, type hints, docstrings, `pathlib.Path`, `argparse`.
- `generate_data.py` requires **PyMuPDF + Pillow** in the same interpreter. Always use `python -m pip install`.
- Covers: PDF page 1 -> zoom 3x -> resize 600px -> WebP q85 method=6 -> convert RGB before saving.

## 6. DATA PIPELINE - Critical

- Run `generate_data.py` ONLY ONCE per batch. MUST verify PyMuPDF+Pillow first.
- MUST verify `download_url` preservation after generate (missing URL count = exactly N new books).
- `upload_releases.py --dry-run` is REQUIRED before a real upload.
- Description format has 3 parts: Context -> Overview -> Key Takeaways (4-5 `•` bullets). Separate with `\n\n`. Write Vietnamese books in Vietnamese.
- Lost `download_url` -> restore with `git checkout site/data.json`.

## 7. GIT

NEVER commit: `*.pdf`, `*.epub`, `*.jpg`, `*.png`, `venv/`, `node_modules/`, IDE config.
Exception: `!library_structure.log` may be committed.

## 8. AI INSTRUCTIONS

1. NO placeholder/TODO code - every function must be complete.
2. DO NOT suggest external libraries - always stay vanilla.
3. DO NOT edit `data.json` in a way that removes existing descriptions/download URLs.
4. MUST read `library_structure.log` before classifying books - prioritize EXISTING folders.
5. MUST run `generate_structure_log.py` after adding new books.
6. MUST read `SKILL.md` before executing `/auto-organize`.
7. Ask the user for confirmation before moving/renaming files.
8. CSS uses variables, JS uses ES6+, images are WebP only.
9. **Sub-topic**: Books in subfolders (for example `Programming_Languages/Java/`) MUST have `topic` = `"Programming Languages/Java"` (display name, NOT `_`). DO NOT write `"Programming Languages"` only (missing sub-topic).
10. **Verify after generate**: After running `generate_data.py`, MUST check that the `topic` field for each new book matches its folder path correctly (especially books in sub-topics).

## 9. CODEX COMPATIBILITY

- Root `AGENTS.md` is the Codex entrypoint and points to rules/skills/workflows in `.agents/`.
- `.agents/` is the shared source for both Antigravity and Codex; do not duplicate logic elsewhere unless necessary.
- When updating `.agents/`, run `python scripts/cli.py codex-sync --base-dir .` to regenerate `.codex/`.
- When encountering Antigravity-specific instructions:
  - `view_file` -> Codex uses a file-reading tool or `Get-Content -Raw`.
  - `multi_replace_file_content` -> Codex uses `apply_patch` for batch edits, then validates JSON.
  - `// turbo` -> optimization note only, not required syntax.
- Codex runs on PowerShell in this repo, so `mkdir -p`/`mv` can be replaced with `New-Item -ItemType Directory -Force`/`Move-Item`.
- For `/auto-organize`, Codex must read `.agents/workflows/auto-organize.md` and `.agents/skills/auto-organize/SKILL.md` before making changes.

## SCRIPTS (CLI & TUI)

**Interactive TUI:**
`python scripts/tui.py`

**Command-line CLI:**

| Command (`python scripts/cli.py <cmd>`) | Function |
|-------|----------|
| `list` | List all books/topics/categories |
| `rename` | Preview renames (dry-run) |
| `rename --execute` | Normalize names to ASCII Snake_Case |
| `generate` | Generate covers + data.json (ONLY ONCE) |
| `structure` | Update library_structure.log |
| `doctor` | Validate repo health, dependencies, metadata, covers |
| `validate` | Alias for `doctor` |
| `smoke` | Smoke check static site contracts |
| `upload --dry-run` | Preview upload (REQUIRED) |
| `upload` | Upload NEW books |
| `upload --force` | Re-upload everything |
| `upload --hard-reset` | Delete + recreate release |
| `codex-sync` | Regenerate the `.codex/` adapter from `.agents/` |
| `delete --book "Title"` | Preview book deletion (dry-run) |
| `delete --book "Title" --execute` | Delete book from data.json + cover |
| `delete --topic "Topic" --category "Cat"` | Preview topic deletion |
| `delete --topic "Topic" --category "Cat" --execute` | Delete an entire topic |
| `delete --category "Cat" --execute` | Delete an entire category |
| `delete --book "Title" --execute --delete-files` | Also delete the physical file |
| `update --book "Title" --set-description "Desc"` | Preview description update |
| `update --book "Title" --set-description "Desc" --execute` | Update description |
| `update --book "Title" --set-category "Cat" --execute` | Move book to another category |
| `update --book "Title" --set-topic "Topic" --execute` | Move book to another topic |
| `update --topic "Old" --category "Cat" --rename "New" --execute` | Rename topic |
| `update --category "Old" --rename "New" --execute` | Rename category |

REPO: `Patruxs/My-Bookshelves` · branch: `main` · deploy: GitHub Pages from `site/`

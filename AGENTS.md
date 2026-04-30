# AGENTS.md

This guide is the entrypoint for Codex when working in the My-Bookshelves repo.
The `.agents/` directory remains the shared source for both Antigravity and Codex.
The `.codex/` directory is the Codex-specific adapter and only points back to `.agents/`.

## Load Order

1. Always read `.agents/rules/my-bookshelves.md` before editing code, metadata, books, covers, uploads, or workflows.
2. When the user invokes `/auto-organize`, `auto-organize`, or asks to classify books in `Inbox/`, read:
   - `.codex/manifest.json`
   - `.codex/rules.md`
   - `.codex/workflows/auto-organize.md`
   - `.agents/workflows/auto-organize.md`
   - `.agents/skills/auto-organize/SKILL.md`
   - `.agents/skills/auto-organize/prompts/classify_book.md`
   - `.agents/skills/auto-organize/config/settings.json`
3. Even when only editing frontend code, keep the zero-dependency boundary from the project rules.

## Codex Compatibility Map

| Antigravity concept | Codex equivalent |
| --- | --- |
| Slash workflow such as `/auto-organize` | The user can invoke it in plain text; read the file in `.agents/workflows/` and execute the steps |
| `view_file` | Use a file-reading tool or `Get-Content -Raw` in PowerShell |
| `multi_replace_file_content` | Use `apply_patch` for batch edits; for large JSON files, prefer existing tools/CLI and validate JSON after editing |
| `// turbo` comment | Optimization note from Antigravity, not required syntax for Codex |
| Bash snippets | Run the equivalent command in PowerShell on Windows (`Get-ChildItem`, `New-Item`, `Move-Item`) |

## Operating Rules For Codex

- The default shell is PowerShell, and the working directory is the repo root.
- Use `rg`/`rg --files` to search for files and content.
- Do not commit book files (`*.pdf`, `*.epub`, `*.docx`) to git.
- Ask the user for one confirmation before bulk renaming/moving books or performing a real upload.
- Before running `generate`, verify PyMuPDF, Pillow, and python-docx with the active interpreter.
- Run `python scripts/cli.py generate --base-dir .` only once per batch; if it fails, fix the root cause before retrying.
- After `generate`, always verify the `download_url` and `topic` for books in subfolders.
- When writing `category`/`topic` to `site/data.json`, use display names with spaces; do not write `Snake_Case`.
- Use `python scripts/cli.py doctor --base-dir . --strict` before upload/deploy-sensitive changes.
- `setup.bat` and `setup.sh` are non-destructive by default; pass `--reset-sample-data` only when a reset is explicitly intended.
- If a test/build/lint/runtime failure occurs during work, append it to `ERRORS.md` according to the workspace error logging rule.

## Auto-Organize Summary

Shared workflow:

1. Scan `Inbox/` and count N new books.
2. Dry-run the rename; execute only after user approval.
3. Generate and read `library_structure.log`.
4. Classify all books in memory, prioritizing existing folders.
5. Show a summary table and ask the user for one confirmation.
6. Move the batch into `Books/`.
7. Verify dependencies, generate covers/data, insert descriptions, and verify metadata.
8. Dry-run the upload, then perform the real upload only if the count matches N.
9. Update `library_structure.log`, then commit/push if the workflow or user requests it.

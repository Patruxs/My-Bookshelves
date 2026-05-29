# Antigravity CLI Instructions for My-Bookshelves

This project is a personal static book library hosted on GitHub Pages. It is shared across Antigravity CLI and Codex. 
The shared source of truth for workflows and rules is located in the `.agents/` folder. Do not delete or modify the `.agents/` or `.codex/` configurations.

## Core Principles
- **Zero-Dependency**: 100% vanilla HTML + CSS + JS (ES6+). NO React/Vue/Tailwind/Bootstrap. System fonts only.
- **File Storage**: Store PDF/EPUB files on GitHub Releases. DO NOT commit them to the git repository.
- **Cover Images**: Must be WebP format, 600px width, <80KB.

## Data & Naming Conventions
- **Folder Names**: Must use ASCII `Snake_Case` (e.g., `Programming_Languages/Java`).
- **Data Names (`site/data.json`)**: When writing `topic` or `category` fields to `site/data.json`, you MUST use display names with spaces, NOT underscores (e.g., `Programming Languages/Java`). 
- **Sub-topics**: Books in subfolders must have a `topic` that includes the full path display name (e.g., `Programming Languages/Java`).

## Workflow: Auto-Organize
If the user asks to classify books, organize the `Inbox/`, or triggers `/auto-organize`:
1. You MUST call `activate_skill` with the name `auto-organize`.
2. Follow the instructions provided by the activated skill exactly, which includes batch classification, confirming with the user, generating data, and uploading.

## Python Automation Scripts
All automation should be performed using the CLI script `python scripts/cli.py`.
- `python scripts/cli.py generate --base-dir .` : Generates covers and metadata. Run ONLY ONCE per batch. Verify dependencies (PyMuPDF, Pillow, python-docx) first.
- `python scripts/cli.py structure --base-dir .` : Generates the `library_structure.log` for AI context grounding. Run this after moving any files.
- `python scripts/cli.py doctor --base-dir . --strict` : Validates repository health and metadata.
- `python scripts/cli.py upload --dry-run` : Always dry-run uploads before performing a real upload.

## Guardrails
- **NEVER** edit `site/data.json` in a way that removes existing `description` or `download_url` fields.
- **ALWAYS** ask the user for confirmation BEFORE executing a batch move/rename, a real upload, or a git commit.
- **NEVER** create duplicate topics by mixing `Snake_Case` and display names in `data.json`.

# 📚 My Bookshelves

A personal digital library — static web, zero dependencies, AI-powered organization.

**[🌐 Live website](https://patruxs.github.io/My-Bookshelves/)**

## ✨ Features

- 📖 **SPA Detail View** — Click to view cover, description, related books, download
- 🔍 **Search & Filter** — By title, category, topic, format
- 📁 **Sidebar Navigation** — Dynamic category tree with topic counts
- 🤖 **AI Auto-Organizer** — Drop books in `Inbox/`, run `/auto-organize`
- 📱 **Responsive** — Desktop, tablet, mobile
- 💾 **< 1MB repo** — Books stored on GitHub Releases, covers as WebP

## 💾 Storage Strategy

```
Git Repo (~1MB)           GitHub Releases (unlimited)
├── site/                 └── storage-v1
│   ├── index.html            ├── Book1.pdf
│   ├── app.js                ├── Book2.epub
│   ├── data.json             └── ...
│   └── assets/covers/*.webp
├── scripts/
└── .agents/
```

Books are **never committed** to git — `.gitignore` blocks `*.pdf *.epub`. Upload via `upload_releases.py`.

## 🚀 Quick Start

```bash
# Install dependencies (use python -m pip to target correct interpreter)
python -m pip install PyMuPDF Pillow

# View locally
python -m http.server 8080    # → http://localhost:8080/site/

# Generate covers + data.json
python scripts/generate_data.py --base-dir .

# Upload books to GitHub Releases
python scripts/upload_releases.py --dry-run   # preview first
python scripts/upload_releases.py             # upload new books only
```

## 📁 Structure

```
Books/                          # Organized by Dynamic Categories
├── 1_Computer_Science_Fundamentals/
├── 2_Software_Engineering_Disciplines/
├── 3_Career_and_Professional_Development/
├── 4_Personal_Development_and_Skills/
├── 5_University_Courses/
└── {N}_New_Category/           # AI can create new categories

Inbox/                          # Drop new books here

site/                           # Static website (GitHub Pages)
├── index.html                  # Single-file HTML+CSS (Apple style)
├── app.js                      # All JS logic, zero dependencies
├── data.json                   # Book metadata (cache-busted fetch)
└── assets/covers/              # WebP covers (250px, q60, <30KB each)

scripts/                        # Python automation
├── generate_data.py            # Scan → covers + data.json
├── rename_books.py             # Normalize filenames → ASCII Snake_Case
├── upload_releases.py          # Smart Incremental Sync → GitHub Releases
├── auto_organize.py            # Library structure helper
└── optimize_covers.py          # Legacy cover re-optimization

.agents/                        # AI Agent configuration
├── rules/my-bookshelves.md     # Project rules
├── skills/auto-organize/       # Classification skill + prompts
└── workflows/auto-organize.md  # /auto-organize workflow
```

## 📋 Scripts Reference

| Command                                                    | Description                             |
| ---------------------------------------------------------- | --------------------------------------- |
| `python scripts/rename_books.py --base-dir .`              | Preview filename normalization          |
| `python scripts/rename_books.py --base-dir . --execute`    | Normalize to ASCII Snake_Case           |
| `python scripts/generate_data.py --base-dir .`             | Extract covers (WebP) + build data.json |
| `python scripts/upload_releases.py --dry-run`              | Preview upload (always run first!)      |
| `python scripts/upload_releases.py`                        | Upload new books to GitHub Releases     |
| `python scripts/auto_organize.py --structure --base-dir .` | Show library folder tree                |

## 🔄 Adding New Books

1. Drop files into `Inbox/`
2. Run `/auto-organize` — AI classifies, moves, generates covers, writes descriptions, uploads
3. Push to `main` → GitHub Pages auto-deploys


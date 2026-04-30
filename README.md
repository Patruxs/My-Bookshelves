# 📚 My Bookshelves

A personal digital library — static web, zero dependencies, AI-powered organization.

**[🌐 Live Demo](https://patruxs.github.io/My-Bookshelves/)**

Built for a lightweight GitHub Pages setup: the website is served from `site/`, books are stored in GitHub Releases, and Python scripts handle local library maintenance.

## ✨ Features

- 📖 **SPA Detail View** — Click to view cover, description, related books, download
- 🔍 **Search & Filter** — By title, category, topic, format
- 📁 **Sidebar Navigation** — Dynamic category tree with topic counts
- 🤖 **AI Auto-Organizer** — Drop books in `Inbox/`, run `/auto-organize` in Antigravity or ask Codex to run `auto-organize`
- 💻 **Interactive TUI** — Manage everything visually in your terminal with `python scripts/tui.py`
- 🩺 **Doctor / Validate** — Check dependencies, metadata, covers, paths, and URLs
- 📱 **Responsive** — Desktop, tablet, mobile
- 💾 **< 1MB repo** — Books stored on GitHub Releases, covers as WebP

## 🚀 Quick Start

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [GitHub CLI](https://cli.github.com/) _(optional, for uploading books to Releases)_

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/Patruxs/My-Bookshelves.git
cd My-Bookshelves

# Windows PowerShell
.\setup.bat

# Windows Command Prompt
setup.bat

# macOS / Linux
chmod +x setup.sh && ./setup.sh
```

This will automatically:
1. ✅ Check Python installation
2. ✅ Create a virtual environment (`venv/`)
3. ✅ Install all Python dependencies (PyMuPDF, Pillow, python-docx)
4. ✅ Create required directories (`Books/`, `Inbox/`, `site/assets/covers/`)
5. ✅ Run a non-destructive repo doctor check

Setup preserves existing library data. To intentionally reset sample data, run:

```bash
setup.bat --reset-sample-data
# or
./setup.sh --reset-sample-data
```

### After Setup

```bash
# Activate the virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows Command Prompt:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate

# View the website locally
python -m http.server 8080
# → http://localhost:8080/site/
```

## 🔄 Adding New Books

1. Drop files into `Inbox/`
2. Run `/auto-organize` in Antigravity, or ask Codex to run `auto-organize` — AI classifies, moves, generates covers, writes descriptions, uploads
3. Run `python scripts/cli.py doctor --base-dir . --strict`
4. Push to `main` → GitHub Pages auto-deploys from `site/`

## 💾 Storage Strategy

```
Git Repo (~1MB)           GitHub Releases (unlimited)
├── site/                 └── storage-v1
│   ├── index.html            ├── Book1.pdf
│   ├── app.js                ├── Book2.epub
│   ├── js/config.js
│   ├── data.json             └── ...
│   └── assets/covers/*.webp
├── scripts/
├── tests/
├── .agents/              # Shared Antigravity/Codex skills, workflows, rules
├── .codex/               # Codex adapter files that point back to .agents/
└── AGENTS.md             # Codex entrypoint
```

Books are **never committed** to git — `.gitignore` blocks `*.pdf *.epub *.docx`. Cover WebP files under `site/assets/covers/` are committed so the GitHub Pages site can display them. Upload books via `upload_releases.py`.

## 📁 Project Structure

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
├── app.js                      # SPA logic, zero dependencies
├── js/config.js                # Small native ES module config
├── data.json                   # Book metadata (cache-busted fetch)
└── assets/covers/              # WebP covers (600px, q85, <80KB each)

scripts/                        # Python automation
├── cli.py                      # Unified Command Line Interface
├── doctor.py                   # Repo health validator
├── lib/                        # Shared script helpers
├── tui.py                      # Interactive Terminal User Interface
├── generate_data.py            # Scan → covers + data.json
├── rename_books.py             # Normalize filenames → ASCII Snake_Case
├── upload_releases.py          # Smart Incremental Sync → GitHub Releases
├── auto_organize.py            # Library structure helper
├── generate_structure_log.py   # Generate AI context log
└── optimize_covers.py          # Legacy cover re-optimization

tests/                          # stdlib unittest coverage for scripts
library_structure.log           # Generated AI context log (local, ignored)
ERRORS.md                       # Local process/error log (ignored)
requirements.txt                # Python dependencies
setup.bat                       # One-command setup (Windows)
setup.sh                        # One-command setup (macOS/Linux)
AGENTS.md                       # Codex compatibility entrypoint
.github/workflows/main.yml      # Simple GitHub Pages deploy workflow
.codex/                         # Codex adapter layer (manifest, rules, workflows)
.agents/                        # Shared AI rules, skills, and workflows
```

## 📋 Scripts Reference

| Command                                                    | Description                             |
| ---------------------------------------------------------- | --------------------------------------- |
| `python scripts/tui.py`                                    | Open Interactive Terminal User Interface|
| `python scripts/cli.py list`                               | List all books, topics, and categories  |
| `python scripts/cli.py generate`                           | Extract covers (WebP) + build data.json |
| `python scripts/cli.py rename`                             | Normalize filenames to ASCII Snake_Case |
| `python scripts/cli.py structure`                          | Update library_structure.log            |
| `python scripts/cli.py doctor --base-dir . --strict`        | Validate dependencies, metadata, covers |
| `python scripts/cli.py validate --base-dir . --json`        | Machine-readable validation report      |
| `python scripts/cli.py upload --dry-run`                   | Preview upload (always run first!)      |
| `python scripts/cli.py upload`                             | Upload new books to GitHub Releases     |
| `python scripts/cli.py codex-sync --base-dir .`            | Regenerate `.codex/` from `.agents/`    |
| `python scripts/cli.py delete --book "Title"`              | Delete a book                           |
| `python scripts/cli.py update --book "Title" ...`          | Update metadata                         |

## ✅ Local Checks

Run these before pushing changes:

```bash
python -m compileall -q scripts
python -m unittest discover -s tests
python scripts/cli.py doctor --base-dir . --strict
python scripts/cli.py codex-sync --base-dir . --check
python -m json.tool site/data.json
```

For upload safety:

```bash
python scripts/cli.py upload --dry-run
python scripts/cli.py upload
```

## 🚀 Deployment

GitHub Pages is deployed from the `site/` directory using `.github/workflows/main.yml`.

Repository settings should use GitHub Actions for Pages deployment. The workflow uploads only `site/`, so the public URL stays:

```text
https://patruxs.github.io/My-Bookshelves/
```

## 🤝 Contributing

1. Fork the repository
2. Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)
3. Add your books to `Inbox/`
4. Submit a Pull Request

## 📄 License

This project is open source. Books are stored separately via GitHub Releases and are not included in the repository.

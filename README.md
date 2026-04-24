# 📚 My Bookshelves

A personal digital library — static web, zero dependencies, AI-powered organization.

**[🌐 Live Demo](https://patruxs.github.io/My-Bookshelves/)**

## ✨ Features

- 📖 **SPA Detail View** — Click to view cover, description, related books, download
- 🔍 **Search & Filter** — By title, category, topic, format
- 📁 **Sidebar Navigation** — Dynamic category tree with topic counts
- 🤖 **AI Auto-Organizer** — Drop books in `Inbox/`, run `/auto-organize`
- 💻 **Interactive TUI** — Manage everything visually in your terminal with `python scripts/tui.py`
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

# Windows
setup.bat

# macOS / Linux
chmod +x setup.sh && ./setup.sh
```

This will automatically:
1. ✅ Check Python installation
2. ✅ Create a virtual environment (`venv/`)
3. ✅ Install all Python dependencies (PyMuPDF, Pillow, python-docx)
4. ✅ Create required directories (`Books/`, `Inbox/`, `site/assets/covers/`)
5. ✅ Verify everything works

### After Setup

```bash
# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# View the website locally
python -m http.server 8080
# → http://localhost:8080/site/
```

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

Books are **never committed** to git — `.gitignore` blocks `*.pdf *.epub *.docx`. Upload via `upload_releases.py`.

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
├── app.js                      # All JS logic, zero dependencies
├── data.json                   # Book metadata (cache-busted fetch)
└── assets/covers/              # WebP covers (600px, q85, <80KB each)

scripts/                        # Python automation
├── cli.py                      # Unified Command Line Interface
├── tui.py                      # Interactive Terminal User Interface
├── generate_data.py            # Scan → covers + data.json
├── rename_books.py             # Normalize filenames → ASCII Snake_Case
├── upload_releases.py          # Smart Incremental Sync → GitHub Releases
├── auto_organize.py            # Library structure helper
├── generate_structure_log.py   # Generate AI context log
└── optimize_covers.py          # Legacy cover re-optimization

requirements.txt                # Python dependencies
setup.bat                       # One-command setup (Windows)
setup.sh                        # One-command setup (macOS/Linux)
```

## 📋 Scripts Reference

| Command                                                    | Description                             |
| ---------------------------------------------------------- | --------------------------------------- |
| `python scripts/tui.py`                                    | Open Interactive Terminal User Interface|
| `python scripts/cli.py list`                               | List all books, topics, and categories  |
| `python scripts/cli.py generate`                           | Extract covers (WebP) + build data.json |
| `python scripts/cli.py rename`                             | Normalize filenames to ASCII Snake_Case |
| `python scripts/cli.py structure`                          | Update library_structure.log            |
| `python scripts/cli.py upload --dry-run`                   | Preview upload (always run first!)      |
| `python scripts/cli.py upload`                             | Upload new books to GitHub Releases     |
| `python scripts/cli.py delete --book "Title"`              | Delete a book                           |
| `python scripts/cli.py update --book "Title" ...`          | Update metadata                         |

## 🔄 Adding New Books

1. Drop files into `Inbox/`
2. Run `/auto-organize` — AI classifies, moves, generates covers, writes descriptions, uploads
3. Push to `main` → GitHub Pages auto-deploys

## 🤝 Contributing

1. Fork the repository
2. Run `setup.bat` (Windows) or `./setup.sh` (macOS/Linux)
3. Add your books to `Inbox/`
4. Submit a Pull Request

## 📄 License

This project is open source. Books are stored separately via GitHub Releases and are not included in the repository.

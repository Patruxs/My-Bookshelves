# 📚 My Bookshelves

A personal digital library with a static web interface and AI-powered book organizer.

**[🌐 Live Demo](https://YOUR_USERNAME.github.io/My-Bookshelves/)**

## Features

- 🔍 **Search & Filter** — Find books by title, category, topic, or format
- 🖼️ **Cover Gallery** — Auto-extracted cover images from PDF/EPUB
- 🤖 **AI Auto-Organizer** — Drop books into `Inbox_Book/`, AI classifies them
- 🚀 **GitHub Pages** — Auto-deploys on push via GitHub Actions

## Project Structure

```
My-Bookshelves/
├── 1_Computer_Science_Fundamentals/    # 📚 Books organized by category
├── 2_Software_Engineering_Disciplines/
├── 3_Career_and_Professional_Development/
├── 4_Miscellaneous/
├── 5_University_Courses/
├── Inbox_Book/                         # 📥 Drop new books here
│
├── site/                               # 🌐 Static website (GitHub Pages)
│   ├── index.html
│   ├── app.js
│   ├── data.json
│   └── assets/covers/
│
├── scripts/                            # 🐍 Python tools
│   ├── generate_data.py                #    Extract covers + build data.json
│   └── auto_organize.py                #    Utility for AI book classification
│
├── .agents/                            # 🤖 AI Agent skills & workflows
├── .github/workflows/main.yml          # ⚙️ CI/CD pipeline
├── requirements.txt
└── DEPLOY_GUIDE.md
```

## Quick Start

### View the library locally

```bash
cd site
python -m http.server 8080
# Open http://localhost:8080
```

### Generate book covers

```bash
pip install -r requirements.txt
cd scripts
python generate_data.py
```

### Organize new books (with AI Agent)

1. Drop PDF/EPUB files into `Inbox_Book/`
2. Run `/auto-organize` in your AI agent

## Deployment

See [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) for GitHub Pages setup.

## Naming Conventions

- Folders: `Snake_Case` with numbered prefixes (`1_`, `2_`, ...)
- Files: Original book titles preserved
- Multiple formats (`.pdf`, `.epub`) kept side-by-side

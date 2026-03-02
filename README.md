# 📚 My Bookshelves

A personal digital library with AI-powered book organization, and extreme storage optimization for GitHub.

**[🌐 Live Demo](https://Patruxs.github.io/My-Bookshelves/)**

---

## ✨ Features

- 🔍 **Live Search & Filter** — Find books by title, category, topic, or format
- 📁 **Sidebar Navigation** — Browse by category and topic tree
- 🖼️ **Cover Gallery** — Auto-extracted cover images (WebP, <30KB each)
- 🌓 **Dark/Light Mode** — System-aware with manual toggle
- 📱 **Fully Responsive** — Optimized for desktop, tablet, and mobile
- 📄 **Pagination** — 15 books/page with smart navigation
- 🔗 **Share Links** — Share individual book details via URL
- 🤖 **AI Auto-Organizer** — Drop books into `Inbox/`, AI classifies and organizes
- 🚀 **GitHub Pages** — Auto-deploys on push with zero build step

## 🏗️ Architecture: 4-Agent System

| Agent       | Role                           | Files                                                    |
| ----------- | ------------------------------ | -------------------------------------------------------- |
| **Agent 1** | Frontend & UI/UX (Apple Style) | `site/index.html`, `site/app.js`                         |
| **Agent 2** | Python Data Engineer           | `scripts/generate_data.py`, `scripts/optimize_covers.py` |
| **Agent 3** | AI Automation Expert           | `scripts/auto_organize.py`, `.agents/`                   |
| **Agent 4** | DevOps & Storage Architect     | `.github/workflows/`, `scripts/upload_releases.py`       |

## 💾 Storage Strategy: "GitHub Releases Hack"

> **Problem**: GitHub repos have a 1GB soft limit. A library of 100+ PDFs could easily exceed this.
>
> **Solution**: Store books in **GitHub Releases** (no repo size impact), not in git history.

```
┌─────────────────────────────────────────────┐
│  Git Repository (~2MB)                      │
│  ├── site/ (HTML, CSS, JS, data.json)       │
│  ├── site/assets/covers/*.webp (<500KB)     │
│  ├── scripts/ (Python tools)                │
│  └── .agents/ (AI config)                   │
├─────────────────────────────────────────────┤
│  GitHub Releases (unlimited*)               │
│  └── books-YYYYMMDD                         │
│      ├── Book1.pdf                          │
│      ├── Book2.epub                         │
│      └── ... (tens of GB possible)          │
└─────────────────────────────────────────────┘
* GitHub Releases limit: 2GB per file, unlimited total
```

### How it works

1. **`.gitignore`** blocks all `*.pdf`, `*.epub` from git tracking
2. **`upload_releases.py`** uploads books to a GitHub Release via `gh` CLI
3. **`data.json`** stores the Release download URL for each book
4. **`app.js`** uses the Release URL for the Download button

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with `pip`
- **GitHub CLI** (`gh`) — [Install](https://cli.github.com/)

### Install dependencies

```bash
pip install pymupdf Pillow ebooklib
```

### 1. View locally

```bash
python -m http.server 8080
# Open http://localhost:8080/site/
```

### 2. Generate covers + data.json

```bash
python scripts/generate_data.py --base-dir .
```

This will:

- Scan all book folders for PDF/EPUB
- Extract covers → **250px WebP** at quality 60 (<30KB each)
- Generate `site/data.json` (preserves existing descriptions)

### 3. Optimize existing covers (optional)

```bash
python scripts/optimize_covers.py
```

Re-optimizes all existing covers to WebP format.

### 4. Upload books to GitHub Releases

```bash
# Preview (no changes)
python scripts/upload_releases.py --dry-run

# Upload all books
python scripts/upload_releases.py

# With custom tag
python scripts/upload_releases.py --tag v2025.03
```

### 5. Organize new books (AI Agent)

1. Drop PDF/EPUB files into `Inbox/`
2. Run `/auto-organize` in your AI agent

The agent will: **classify → move → generate cover (WebP) → write description → update data.json**

## 📁 Project Structure

```
My-Bookshelves/
├── Books/                              # 📚 All books organized by category
│   ├── 1_Computer_Science_Fundamentals/
│   ├── 2_Software_Engineering_Disciplines/
│   ├── 3_Career_and_Professional_Development/
│   ├── 4_Miscellaneous/
│   └── 5_University_Courses/
├── Inbox/                              # 📥 Drop new books here
│
├── site/                               # 🌐 Static website (GitHub Pages)
│   ├── index.html                      #    Single-file UI (Apple style)
│   ├── app.js                          #    All logic (zero dependencies)
│   ├── data.json                       #    Book metadata + descriptions
│   └── assets/covers/                  #    WebP cover images (<500KB total)
│
├── scripts/                            # 🐍 Python tools
│   ├── generate_data.py                #    Extract covers → WebP + build data.json
│   ├── optimize_covers.py              #    Batch resize + convert → WebP
│   ├── auto_organize.py                #    Utility for AI agent
│   └── upload_releases.py             #    Upload books to GitHub Releases
│
├── .agents/                            # 🤖 AI Agent config
│   ├── skills/auto-organize/
│   │   ├── SKILL.md                    #    Agent instructions
│   │   ├── prompts/classify_book.md    #    Classification rules
│   │   └── config/settings.json        #    Config
│   └── workflows/auto-organize.md      #    /auto-organize command
│
├── .github/workflows/main.yml          # ⚙️ CI/CD (GitHub Actions → Pages)
├── .gitignore                          # 🚫 Blocks *.pdf, *.epub from git
└── README.md
```

## 📋 Scripts Reference

| Command                                                | Description                          |
| ------------------------------------------------------ | ------------------------------------ |
| `python scripts/generate_data.py --base-dir .`         | Scan books → WebP covers → data.json |
| `python scripts/generate_data.py --base-dir . --force` | Re-extract ALL covers                |
| `python scripts/optimize_covers.py`                    | Re-optimize existing covers → WebP   |
| `python scripts/upload_releases.py`                    | Upload books to GitHub Releases      |
| `python scripts/upload_releases.py --dry-run`          | Preview upload (no changes)          |
| `python scripts/auto_organize.py --list`               | List books in Inbox                  |
| `python scripts/auto_organize.py --structure`          | Show library folder tree             |

## 🎨 Design Philosophy

- **Zero Dependencies**: No frameworks, no CDN, no external fonts
- **Apple Aesthetic**: System fonts, glassmorphism, generous whitespace
- **Storage First**: Every KB counts — WebP covers, minified assets, smart gitignore
- **AI-Powered**: Classification and organization via AI Agent skill system

## 📊 Storage Budget

| Component             | Size      | Notes              |
| --------------------- | --------- | ------------------ |
| `site/index.html`     | ~50KB     | All CSS inline     |
| `site/app.js`         | ~15KB     | Zero-dependency JS |
| `site/data.json`      | ~25KB     | 50 books metadata  |
| `site/assets/covers/` | ~500KB    | 50 WebP images     |
| **Total repo**        | **~2MB**  | Code + covers only |
| GitHub Releases       | Unlimited | PDFs, EPUBs        |

## 🔄 Workflow: Adding a New Book

```
1. Drop "New Book.pdf" into Inbox/
2. Run /auto-organize (AI classifies → moves to Books/)
3. Run: python scripts/generate_data.py --base-dir .
4. Run: python scripts/upload_releases.py
5. git add . && git commit && git push
6. GitHub Actions deploys to Pages automatically
```

## 📝 Naming Conventions

- Folders: `Snake_Case` with numbered prefixes (`1_`, `2_`, ...)
- Files: Original book titles preserved
- Multiple formats (`.pdf`, `.epub`) kept side-by-side
- Covers: `Book_Title.webp` (auto-generated, sanitized)

## 🚀 Deployment

Push to `main` → GitHub Actions deploys `site/` to GitHub Pages (no build step needed).

The `site/` directory is self-contained — all it needs is `index.html`, `app.js`, `data.json`, and `assets/covers/`.

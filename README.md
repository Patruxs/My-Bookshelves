# 📚 My Bookshelves

A personal digital library — static web, zero dependencies, AI-powered organization.

**[🌐 Download Book Here](https://patruxs.github.io/My-Bookshelves/)**

## 🚀 Quick Start

```bash
git clone https://github.com/Patruxs/My-Bookshelves.git
cd My-Bookshelves

# Setup (installs dependencies & creates folders)
setup.bat               # Windows
chmod +x setup.sh && ./setup.sh  # macOS / Linux

# View locally
python -m http.server 8080
# → http://localhost:8080/site/
```

## 🔄 Adding Books

1. Drop book files into `Inbox/`.
2. Run `/auto-organize` in Antigravity or Codex to classify and generate metadata.
3. Push to `main` (auto-deploys via GitHub Actions).

## 🧰 Management

Manage your library using the interactive terminal UI:
```bash
# Windows cmd.exe, or after adding the repo to PATH
book tui

# Windows PowerShell from the repo root
.\book.bat tui

# macOS / Linux
./book tui
```

Short CLI examples:
```bash
./book doctor
./book unlock-pdfs
./book epub-to-pdf
./book pdf-to-epub
./book generate --base-dir .
```

> **Note:** Book files (`*.pdf`, `*.epub`) are stored in GitHub Releases, not Git. Run `./book doctor` to validate repository health.

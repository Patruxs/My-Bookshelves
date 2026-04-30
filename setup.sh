#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# 📚 My Bookshelves — One-Command Setup (macOS / Linux / Git Bash)
# ══════════════════════════════════════════════════════════
# Usage: chmod +x setup.sh && ./setup.sh
# ══════════════════════════════════════════════════════════

set -e
cd "$(dirname "$0")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  📚 ${BOLD}My Bookshelves — Setup${NC}                         ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check Python ──
echo -e "[1/5] 🐍 Checking Python..."

# Try python3 first, then python
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo -e "   ${RED}❌ Python not found! Please install Python 3.8+${NC}"
    echo "      https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "   ${GREEN}✅ $PYTHON_CMD $PYTHON_VERSION detected${NC}"

find_venv_python() {
    if [ -x "venv/bin/python" ]; then
        echo "venv/bin/python"
        return 0
    fi

    if [ -x "venv/Scripts/python.exe" ]; then
        echo "venv/Scripts/python.exe"
        return 0
    fi

    if [ -x "venv/Scripts/python" ]; then
        echo "venv/Scripts/python"
        return 0
    fi

    return 1
}

# ── Step 2: Create virtual environment + install dependencies ──
echo ""
echo -e "[2/5] 📥 Creating virtual environment and installing Python dependencies..."

if ! VENV_PYTHON="$(find_venv_python)"; then
    VENV_EXISTED="false"
    if [ -d "venv" ]; then
        VENV_EXISTED="true"
    fi

    if ! "$PYTHON_CMD" -m venv venv; then
        echo -e "   ${RED}❌ Failed to create virtual environment${NC}"
        echo "      If you are on Ubuntu/WSL, install python3-venv and rerun setup."
        echo "      If you are on Windows Git Bash, make sure Windows Python is on PATH or run setup.bat."
        if [ "$VENV_EXISTED" = "false" ] && [ -d "venv" ]; then
            rm -rf venv
        fi
        exit 1
    fi

    if ! VENV_PYTHON="$(find_venv_python)"; then
        echo -e "   ${RED}❌ Virtual environment was created, but its Python executable was not found${NC}"
        echo "      Expected one of: venv/bin/python, venv/Scripts/python.exe"
        exit 1
    fi
fi
PYTHON_CMD="$VENV_PYTHON"

echo "   Using $PYTHON_CMD"
echo "   Upgrading pip..."
if ! "$PYTHON_CMD" -m pip install --upgrade pip; then
    echo -e "   ${RED}❌ Failed to upgrade pip${NC}"
    exit 1
fi

echo "   Installing requirements..."
if ! "$PYTHON_CMD" -m pip install -r requirements.txt; then
    echo -e "   ${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo -e "   ${GREEN}✅ All dependencies installed${NC}"

# ── Step 3: Create project directories ──
echo ""
echo -e "[3/5] 📁 Creating project directories..."

mkdir -p Books Inbox site/assets/covers
echo -e "   ${GREEN}✅ Books/  Inbox/  site/assets/covers/${NC}"

# ── Step 4: Verify installation ──
echo ""
echo -e "[4/5] ✅ Verifying setup..."

if PYMUPDF_VERSION=$("$PYTHON_CMD" -c "import fitz; print(fitz.version[0])" 2>/dev/null); then
    echo -e "   ${GREEN}✅ PyMuPDF $PYMUPDF_VERSION${NC}"
else
    echo -e "   ${RED}❌ PyMuPDF not working${NC}"
fi

if PILLOW_VERSION=$("$PYTHON_CMD" -c "from PIL import Image; print(Image.__version__)" 2>/dev/null); then
    echo -e "   ${GREEN}✅ Pillow $PILLOW_VERSION${NC}"
else
    echo -e "   ${RED}❌ Pillow not working${NC}"
fi

if "$PYTHON_CMD" -c "import docx" 2>/dev/null; then
    echo -e "   ${GREEN}✅ python-docx${NC}"
else
    echo -e "   ${RED}❌ python-docx not working${NC}"
fi

# ── Step 5: Optional reset + doctor ──
echo ""
echo -e "[5/5] 🩺 Running repo doctor..."
if [ "${1:-}" = "--reset-sample-data" ]; then
    echo -e "   ${YELLOW}⚠️  Resetting sample data because --reset-sample-data was provided${NC}"
    "$PYTHON_CMD" scripts/reset_library.py --force
else
    echo -e "   ${GREEN}✅ Skipping reset. Existing library data is preserved.${NC}"
fi
"$PYTHON_CMD" scripts/cli.py doctor --base-dir .

# ── Done ──
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  🎉 ${BOLD}Setup complete!${NC}                                ${CYAN}║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}                                                     ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  View locally:                                      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    python -m http.server 8080                       ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    → http://localhost:8080/site/                     ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                     ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Add books:                                         ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    1. Drop files into Inbox/                        ${CYAN}║${NC}"
printf "${CYAN}║${NC}    2. %s scripts/cli.py generate --base-dir .${CYAN}║${NC}\n" "$PYTHON_CMD"
echo -e "${CYAN}║${NC}                                                     ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# 📚 My Bookshelves — One-Command Setup (macOS / Linux)
# ══════════════════════════════════════════════════════════
# Usage: chmod +x setup.sh && ./setup.sh
# ══════════════════════════════════════════════════════════

set -e

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

# ── Step 2: Install dependencies ──
echo ""
echo -e "[2/5] 📥 Installing Python dependencies..."

$PYTHON_CMD -m pip install --upgrade pip >/dev/null 2>&1
$PYTHON_CMD -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
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

$PYTHON_CMD -c "import fitz; print('   ✅ PyMuPDF', fitz.version[0])" 2>/dev/null || echo -e "   ${RED}❌ PyMuPDF not working${NC}"
$PYTHON_CMD -c "from PIL import Image; print('   ✅ Pillow', Image.__version__)" 2>/dev/null || echo -e "   ${RED}❌ Pillow not working${NC}"
$PYTHON_CMD -c "import docx; print('   ✅ python-docx')" 2>/dev/null || echo -e "   ${RED}❌ python-docx not working${NC}"

# ── Step 5: Clean up sample data ──
echo ""
echo -e "[5/5] 🧹 Cleaning up sample data..."
$PYTHON_CMD scripts/reset_library.py --force

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
echo -e "${CYAN}║${NC}    2. python scripts/generate_data.py --base-dir .  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                     ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

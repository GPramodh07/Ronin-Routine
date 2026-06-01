#!/usr/bin/env bash
# ==============================================================================
# Ronin Routine Environment Setup Script
# ==============================================================================
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0;m' # No Color

echo -e "${BLUE}=== Ronin Routine Application Setup ===${NC}"

# Ensure we are in the correct directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. Check Python version
echo -e "${YELLOW}[1/4] Checking Python 3 installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install it with: sudo apt install python3${NC}"
    exit 1
fi
python3_ver=$(python3 --version)
echo -e "${GREEN}Found: $python3_ver${NC}"

# 2. Setup Virtual Environment
echo -e "${YELLOW}[2/4] Setting up Python virtual environment in .venv...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}Created virtual environment successfully.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists in .venv.${NC}"
fi

# 3. Activate and Install dependencies
echo -e "${YELLOW}[3/4] Installing dependencies...${NC}"
source .venv/bin/activate

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt
echo -e "${GREEN}All Python packages installed successfully.${NC}"

# 4. Verify PySide6 Installation
echo -e "${YELLOW}[4/4] Verifying PySide6 import and Qt system dependencies...${NC}"
if python3 -c "import PySide6; from PySide6.QtWidgets import QApplication; from PySide6.QtWebEngineWidgets import QWebEngineView; print('PySide6 and QWebEngineView imported successfully!')" &> /dev/null; then
    echo -e "${GREEN}PySide6 environment verified! All Qt dependencies are present.${NC}"
else
    echo -e "${YELLOW}Warning: PySide6 imported, but some system Qt/WebEngine shared libraries may be missing on this Debian system.${NC}"
    echo -e "${YELLOW}If you run into issues launching the UI, you may need to install standard Debian dependencies using:${NC}"
    echo -e "${BLUE}  sudo apt-get install -y libnss3 libasound2 libegl1 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libxkbcommon0 libdbus-1-3 libxcb-xinerama0${NC}"
fi

echo -e "\n${GREEN}=== Environment Setup Completed Successfully! ===${NC}"
echo -e "To run the application, run:"
echo -e "  ${BLUE}source .venv/bin/activate && python3 src/main.py${NC}"

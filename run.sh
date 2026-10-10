#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "===================================================="
echo "          HuffZip - Desktop File Compressor         "
echo "===================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.9+."
    exit 1
fi

# 2. Check dependencies
echo "[*] Checking Python dependencies..."
python3 -c "import customtkinter, tkinterdnd2" 2>/dev/null || {
    echo "[*] Installing dependencies..."
    python3 -m pip install -r requirements.txt
}

# 3. Check C backend
if [ ! -f "backend/huff" ]; then
    echo "[*] Compiling backend..."
    make -C backend
fi

# 4. Launch GUI
echo "[*] Launching HuffZip..."
python3 main.py

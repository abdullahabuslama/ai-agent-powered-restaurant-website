#!/usr/bin/env bash
# ===========================================================================
#  Restaurant Chatbot - One-Click Launcher (macOS / Linux)
#  Run with:  bash run.sh   (or make it executable: chmod +x run.sh && ./run.sh)
#  ----------------------------------------------------------------
#  المشغّل بنقرة واحدة (ماك / لينكس)
# ===========================================================================
set -e
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  Starting Restaurant Assistant..."
echo "  جارٍ تشغيل مساعد المطعم ..."
echo "============================================================"
echo ""

# --- Pick a python command ---
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "[!] Python is not installed."
    echo "[!] بايثون غير مثبّت على الجهاز."
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

# --- Create the virtual environment on first run ---
if [ ! -d ".venv" ]; then
    echo "[*] First-time setup: creating environment..."
    echo "[*] الإعداد لأول مرة: جارٍ تجهيز البيئة..."
    "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# --- Install / update dependencies ---
echo "[*] Installing required packages... (first run may take a minute)"
echo "[*] جارٍ تثبيت المكتبات المطلوبة... (قد يستغرق دقيقة في أول مرة)"
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt

# --- Launch the app ---
echo ""
echo "[OK] Opening the website in your browser..."
echo "[OK] جارٍ فتح الموقع في المتصفح..."
echo ""
streamlit run app.py

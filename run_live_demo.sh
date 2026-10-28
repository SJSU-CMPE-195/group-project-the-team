#!/bin/bash
# Silent Voice Bridge - Live ASL + Auto-Spell Name Demo Runner

cd "$(dirname "$0")"
export PYTHONPATH=src:$PYTHONPATH

PYTHON_BIN="/Users/aramishf/.gemini/antigravity-ide/scratch/silent-voice-bridge/venv/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo "=========================================================="
echo "🤟 Starting Silent Voice Bridge: Live Words + Fingerspelling"
echo "=========================================================="
echo "Controls:"
echo "  • Sign 'MY' then 'NAME' -> Automatically triggers Spell Mode!"
echo "  • Fingerspell your name (A-R-A-M-I-S-H) in front of camera"
echo "  • Drop hands to commit the spelled word"
echo "  • 's' = Toggle Spelling Mode manually"
echo "  • 'r' = Reset sentence"
echo "  • 'q' = Quit"
echo "=========================================================="

"$PYTHON_BIN" src/live_words.py

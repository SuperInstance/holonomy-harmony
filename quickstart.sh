#!/bin/bash
# holonomy-harmony quickstart — compare Coltrane vs Pachelbel via holonomy
set -e
echo "🎵 Holonomy Harmony — Quick Start"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pip install -e . --quiet 2>/dev/null || true

export PYTHONPATH="$SCRIPT_DIR"
python3 examples/coltrane_vs_pachelbel.py
echo "✅ holonomy-harmony works!"

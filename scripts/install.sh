#!/usr/bin/env bash
# scripts/install.sh - one-command installer for arfix
# Usage: bash scripts/install.sh   (from the repo root, or from anywhere)

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Checking pip..."
if ! command -v pip >/dev/null 2>&1; then
    echo "pip not found. Attempting to install it..."
    pkg install python -y 2>/dev/null || apt install python3-pip -y
fi

echo "==> Installing arfix..."
pip install --break-system-packages -e "$REPO_ROOT" -q

echo "==> Quick test..."
if command -v arfix >/dev/null 2>&1; then
    echo "Success!"
else
    echo "Install finished but arfix was not found in PATH."
    echo "Try: export PATH=\$PATH:~/.local/bin"
    echo "and add it to ~/.bashrc to keep it working."
fi

# Install the auto-wrap hook into .bashrc automatically
HOOK_SRC="$REPO_ROOT/scripts/arfix-shell-hook.sh"
BASHRC="$HOME/.bashrc"

if [ -f "$HOOK_SRC" ]; then
    if grep -q "arfix auto-wrap" "$BASHRC" 2>/dev/null; then
        echo "==> auto-wrap already present in .bashrc, skipping."
    else
        echo "" >> "$BASHRC"
        cat "$HOOK_SRC" >> "$BASHRC"
        echo "==> Auto-wrap added to .bashrc. Run: source ~/.bashrc  (or open a new terminal)"
    fi
fi

echo ""
echo "Try:"
echo '  arfix "hello مرحبا"'
echo '  smartcat cat somefile.txt'

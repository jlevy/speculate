#!/bin/bash
# Automated tbd CLI setup for Claude Code sessions
# This script runs on SessionStart to ensure tbd is available and configured

set -e

# Check if tbd is already installed
if command -v tbd &> /dev/null; then
    echo "[tbd] CLI found at $(which tbd)"
else
    # Check for npm (prerequisite)
    if ! command -v npm &> /dev/null; then
        echo "[tbd] WARNING: npm not found - cannot install tbd"
        echo "[tbd] Install Node.js first: https://nodejs.org/"
        exit 0
    fi

    echo "[tbd] Installing tbd-git..."
    npm install -g tbd-git@latest
    echo "[tbd] Installed successfully"
fi

# Configure Claude Code integration
tbd setup claude

exit 0

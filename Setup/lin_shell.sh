#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# --- Root Check ---
if [ "$EUID" -ne 0 ]; then
    echo "Warning: You are not running this script as root (sudo)."
    echo "Creating symbolic links may fail due to permissions."
    echo "If it fails, please try running again with: sudo ./lin.sh"
    echo "-------------------------------------------------------------"
    echo ""
fi

# --- Resolve Python and Launch ---
if command -v python3 &> /dev/null; then
    sudo python3 deploy.py
else
    sudo python deploy.py
fi
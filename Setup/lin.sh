#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/create_links.py"
MANIFEST_SCRIPT="$SCRIPT_DIR/generate_manifest.py"
ROOT="$SCRIPT_DIR/.."

# --- Script Checks ---
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Could not find 'create_links.py' at: $PYTHON_SCRIPT"
    exit 1
fi
if [ ! -f "$MANIFEST_SCRIPT" ]; then
    echo "ERROR: Could not find 'generate_manifest.py' at: $MANIFEST_SCRIPT"
    exit 1
fi

# --- Root Check ---
if [ "$EUID" -ne 0 ]; then
    echo "Warning: You are not running this script as root (sudo)."
    echo "Creating symbolic links may fail due to permissions."
    echo "If it fails, please try running again with: sudo ./lin.sh"
    echo "-------------------------------------------------------------"
    echo ""
fi

# --- Profile Path ---
PROFILE_NAME="h2-dev"
PROFILE_PATH="$HOME/.config/r2modmanPlus-local/HadesII/profiles/$PROFILE_NAME/ReturnOfModding"

echo ""
echo "=========================================================="
echo "  adamant modpack - full local deployment"
echo "  Profile: $PROFILE_NAME"
echo "=========================================================="
echo ""

# --- Resolve python command ---
if command -v python3 &> /dev/null; then
    PY=python3
else
    PY=python
fi

# --- Set up a single mod ---
setup_mod() {
    local MOD_DIR="$1"
    local TOML_FILE="$MOD_DIR/thunderstore.toml"

    TS_NAMESPACE=$(grep '^namespace =' "$TOML_FILE" | awk -F '"' '{print $2}')
    TS_NAME=$(grep '^name =' "$TOML_FILE" | awk -F '"' '{print $2}')

    if [ -z "$TS_NAMESPACE" ] || [ -z "$TS_NAME" ]; then
        echo "SKIP: Could not parse namespace/name from $TOML_FILE"
        return
    fi

    MOD_NAME="$TS_NAMESPACE-$TS_NAME"
    echo "--- Setting up: $MOD_NAME ---"

    # Copy icon and LICENSE into src
    if [ -f "$SCRIPT_DIR/icon.png" ]; then
        cp -f "$SCRIPT_DIR/icon.png" "$MOD_DIR/src/icon.png"
        echo "  Copied icon.png"
    fi
    if [ -f "$SCRIPT_DIR/LICENSE" ]; then
        cp -f "$SCRIPT_DIR/LICENSE" "$MOD_DIR/src/LICENSE"
        echo "  Copied LICENSE"
    fi

    # Generate manifest.json from thunderstore.toml
    $PY "$MANIFEST_SCRIPT" "$TOML_FILE" "$MOD_DIR/src/manifest.json"

    # Create symlinks
    FOLDER1="$MOD_DIR/src"
    FOLDER2="$MOD_DIR/data"
    LINK1="$PROFILE_PATH/plugins/$MOD_NAME"
    LINK2="$PROFILE_PATH/plugins_data/$MOD_NAME"

    $PY "$PYTHON_SCRIPT" "$FOLDER1" "$FOLDER2" "$LINK1" "$LINK2"

    echo ""
}

# --- Process each mod directory ---
MOD_COUNT=0

# Core and Lib (top-level)
for d in "$ROOT"/adamant-modpack-Core "$ROOT"/adamant-modpack-Lib; do
    if [ -f "$d/thunderstore.toml" ]; then
        setup_mod "$d"
        MOD_COUNT=$((MOD_COUNT + 1))
    fi
done

# All submodules
for d in "$ROOT"/Submodules/adamant-*/; do
    if [ -f "$d/thunderstore.toml" ]; then
        setup_mod "$d"
        MOD_COUNT=$((MOD_COUNT + 1))
    fi
done

echo "=========================================================="
echo "  Done. $MOD_COUNT mods deployed."
echo "=========================================================="
echo ""

#!/bin/bash
#
# Installation script for Code Usage for Linux
# Installs the Python app bundle to ~/.local/share/code-usage and wrappers to ~/.local/bin
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_NAME="Code Usage for Linux"
INSTALL_ROOT="$HOME/.local/share/code-usage"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "$APP_NAME - Installation Script"
echo "=================================="
echo ""

echo -n "Checking Python version... "
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Python $PYTHON_VERSION found, but $REQUIRED_VERSION or later is required."
    exit 1
fi
echo -e "${GREEN}OK${NC} (Python $PYTHON_VERSION)"

echo -n "Checking pip... "
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: pip3 is not installed."
    echo "Please install pip3 and try again."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

echo -n "Installing Python dependencies... "
if pip3 install --user -q requests &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "Failed to install requests automatically."
    echo "Please run: pip3 install --user requests"
fi

mkdir -p "$INSTALL_ROOT" "$INSTALL_ROOT/waybar" "$BIN_DIR"
rm -rf "$INSTALL_ROOT/code_usage"

echo -n "Installing application files... "
cp -R "$SCRIPT_DIR/code_usage" "$INSTALL_ROOT/code_usage"
cp "$SCRIPT_DIR/code-usage.py" "$INSTALL_ROOT/code-usage.py"
cp "$SCRIPT_DIR/claude-usage.py" "$INSTALL_ROOT/claude-usage.py"
cp "$SCRIPT_DIR/waybar/code-usage-waybar.py" "$INSTALL_ROOT/waybar/code-usage-waybar.py"
cp "$SCRIPT_DIR/waybar/claude-usage-waybar.py" "$INSTALL_ROOT/waybar/claude-usage-waybar.py"
chmod +x \
    "$INSTALL_ROOT/code-usage.py" \
    "$INSTALL_ROOT/claude-usage.py" \
    "$INSTALL_ROOT/waybar/code-usage-waybar.py" \
    "$INSTALL_ROOT/waybar/claude-usage-waybar.py"
echo -e "${GREEN}OK${NC}"

echo -n "Installing command wrappers... "
cat > "$BIN_DIR/code-usage" <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_ROOT"
exec python3 "$INSTALL_ROOT/code-usage.py" "\$@"
EOF
cat > "$BIN_DIR/claude-usage" <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_ROOT"
exec python3 "$INSTALL_ROOT/claude-usage.py" "\$@"
EOF
cat > "$BIN_DIR/code-usage-waybar" <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_ROOT"
exec python3 "$INSTALL_ROOT/waybar/code-usage-waybar.py" "\$@"
EOF
cat > "$BIN_DIR/claude-usage-waybar" <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_ROOT"
exec python3 "$INSTALL_ROOT/waybar/claude-usage-waybar.py" "\$@"
EOF
chmod +x \
    "$BIN_DIR/code-usage" \
    "$BIN_DIR/claude-usage" \
    "$BIN_DIR/code-usage-waybar" \
    "$BIN_DIR/claude-usage-waybar"
echo -e "${GREEN}OK${NC}"

echo -n "Checking PATH configuration... "
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}NEEDS UPDATE${NC}"
    echo ""
    echo "$BIN_DIR is not in your PATH."

    if [ -n "$BASH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    else
        SHELL_CONFIG="$HOME/.profile"
    fi

    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
    echo "Added PATH export to $SHELL_CONFIG"
    echo ""
    echo -e "${YELLOW}IMPORTANT:${NC} Run one of the following to update your current session:"
    echo "  source $SHELL_CONFIG"
    echo "  or restart your terminal"
else
    echo -e "${GREEN}OK${NC}"
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Primary commands:"
echo "  code-usage"
echo "  code-usage-waybar"
echo ""
echo "Compatibility aliases:"
echo "  claude-usage"
echo "  claude-usage-waybar"
echo ""

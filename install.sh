#!/bin/bash
#
# Installation script for Code Usage for Linux
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Code Usage for Linux - Installation Script"
echo "========================================="
echo ""

echo -n "Checking Python version... "
if ! command -v python3 >/dev/null 2>&1; then
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
if ! command -v pip3 >/dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: pip3 is not installed."
    echo "Please install pip3 and try again."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

echo -n "Installing Python dependencies... "
if pip3 install --user -q 'requests>=2.25.0' >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "Failed to install requests automatically."
    echo "Please run: pip3 install --user 'requests>=2.25.0'"
fi

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -n "Installing shared package... "
rm -rf "$INSTALL_DIR/code_usage"
cp -r "$SCRIPT_DIR/code_usage" "$INSTALL_DIR/code_usage"
echo -e "${GREEN}OK${NC}"

echo -n "Installing primary CLI... "
cp "$SCRIPT_DIR/code-usage.py" "$INSTALL_DIR/code-usage"
chmod +x "$INSTALL_DIR/code-usage"
echo -e "${GREEN}OK${NC}"

echo -n "Installing Waybar helper... "
cp "$SCRIPT_DIR/waybar/code-usage-waybar.py" "$INSTALL_DIR/code-usage-waybar"
chmod +x "$INSTALL_DIR/code-usage-waybar"
echo -e "${GREEN}OK${NC}"

echo -n "Installing compatibility aliases... "
cp "$SCRIPT_DIR/claude-usage.py" "$INSTALL_DIR/claude-usage"
cp "$SCRIPT_DIR/waybar/claude-usage-waybar.py" "$INSTALL_DIR/claude-usage-waybar"
chmod +x "$INSTALL_DIR/claude-usage" "$INSTALL_DIR/claude-usage-waybar"
echo -e "${GREEN}OK${NC}"

echo -n "Checking PATH configuration... "
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}NEEDS UPDATE${NC}"
    echo ""
    echo "~/.local/bin is not in your PATH."
    echo "Adding it to your shell configuration..."

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
echo "Examples:"
echo "  code-usage --provider auto"
echo "  code-usage --provider codex --json"
echo "  code-usage-waybar --provider auto --programs claude,codex,opencode"
echo ""

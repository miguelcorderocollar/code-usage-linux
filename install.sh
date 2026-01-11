#!/bin/bash
#
# Installation script for Claude Usage for Linux
# Installs the Python script to ~/.local/bin for easy access
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Claude Usage for Linux - Installation Script"
echo "=============================================="
echo ""

# Check Python version
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

# Check if pip is available
echo -n "Checking pip... "
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: pip3 is not installed."
    echo "Please install pip3 and try again."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Install requests library
echo -n "Installing Python dependencies... "
if pip3 install --user -q requests &> /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "Failed to install requests library automatically."
    echo "Please run: pip3 install --user requests"
fi

# Create ~/.local/bin if it doesn't exist
mkdir -p ~/.local/bin

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy the Python script
echo -n "Installing claude-usage to ~/.local/bin... "
cp "$SCRIPT_DIR/claude-usage.py" ~/.local/bin/claude-usage
chmod +x ~/.local/bin/claude-usage
echo -e "${GREEN}OK${NC}"

# Check if ~/.local/bin is in PATH
echo -n "Checking PATH configuration... "
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}NEEDS UPDATE${NC}"
    echo ""
    echo "~/.local/bin is not in your PATH."
    echo "Adding it to your shell configuration..."

    # Detect shell and add to appropriate config file
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
echo "Usage:"
echo "  claude-usage              Show current usage"
echo "  claude-usage --watch      Auto-refresh every 2 minutes"
echo "  claude-usage --json       Output as JSON"
echo "  claude-usage --help       Show all options"
echo ""
echo "Note: Make sure you're logged in to Claude Code first:"
echo "  claude"
echo ""

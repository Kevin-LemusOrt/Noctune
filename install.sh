#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo ""
echo "Installing Noctune..."
echo ""

install_system_dependencies() {
    if command -v apt >/dev/null 2>&1; then
        echo "Detected APT (Debian/Ubuntu)."
        sudo apt update
        sudo apt install -y \
            python3 \
            python3-venv \
            python3-pip \
            playerctl \
            cava

    elif command -v dnf >/dev/null 2>&1; then
        echo "Detected DNF (Fedora)."
        sudo dnf install -y \
            python3 \
            python3-pip \
            playerctl \
            cava

    elif command -v pacman >/dev/null 2>&1; then
        echo "Detected Pacman (Arch Linux)."
        sudo pacman -Sy --needed \
            python \
            python-pip \
            playerctl \
            cava

    else
        echo "Unsupported package manager."
        echo "Install Python 3, playerctl and cava manually."
        exit 1
    fi
}

install_system_dependencies

cd -- "$PROJECT_DIR" || exit 1

for command in python3 playerctl cava; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Error: '$command' was not found after installation."
        exit 1
    fi
done

echo ""
echo "Preparing virtual environment..."
echo ""

if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

echo ""
echo "Installing Python dependencies..."
echo ""

if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    "$PROJECT_DIR/venv/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
else
    "$PROJECT_DIR/venv/bin/python" -m pip install requests rich
fi

echo ""
echo "Creating global command..."
echo ""

mkdir -p "$HOME/.local/bin"

cat > "$HOME/.local/bin/noctune" <<EOF
#!/bin/bash

exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py"
EOF

chmod +x "$HOME/.local/bin/noctune"

echo ""
echo "Configuring PATH..."
echo ""

SHELL_NAME=$(basename "$SHELL")

if [ "$SHELL_NAME" = "zsh" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

if ! grep -q '.local/bin' "$SHELL_RC"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Restart your terminal or run:"
echo ""
echo "source $SHELL_RC"
echo ""
echo "Then launch with:"
echo ""
echo "noctune"
echo ""
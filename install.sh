#!/bin/bash

echo ""
echo "Installing SpotyTerminal..."
echo ""

sudo apt update

sudo apt install -y \
python3 \
python3-venv \
python3-pip \
playerctl \
cava \
tmux

echo ""
echo "Preparing virtual environment..."
echo ""

if [ ! -d "venv" ]; then

    python3 -m venv venv

fi

source venv/bin/activate

echo ""
echo "Installing Python dependencies..."
echo ""

pip install requests rich

echo ""
echo "Creating global command..."
echo ""

mkdir -p ~/.local/bin

PROJECT_DIR=$(pwd)

cat > ~/.local/bin/spotyterminal << EOF
#!/bin/bash

SESSION="spotyterminal"

if tmux has-session -t \$SESSION 2>/dev/null; then

    tmux attach-session -t \$SESSION

else

    tmux new-session -d -s \$SESSION

    tmux send-keys -t \$SESSION \
    "cd $PROJECT_DIR && source venv/bin/activate && python main.py" C-m

    tmux split-window -v -t \$SESSION

    tmux send-keys -t \$SESSION "cava" C-m

    tmux select-pane -t 0

    tmux set-option -t \$SESSION remain-on-exit off

    tmux attach-session -t \$SESSION

fi
EOF

chmod +x ~/.local/bin/spotyterminal

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
echo "spotyterminal"

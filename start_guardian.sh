#!/bin/bash
cd "$(dirname "$0")"

echo "==============================================="
echo "  The Invisible Guardian - starting up..."
echo "==============================================="
echo

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed. Install it from https://python.org and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Installing/checking required packages (quick if already installed)..."
pip3 install --quiet -r requirements.txt

echo
echo "Starting the server..."
python3 run.py &
SERVER_PID=$!

sleep 3

if command -v open &> /dev/null; then
    open http://127.0.0.1:5000       # macOS
elif command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:5000   # Linux
fi

echo
echo "The app should now be open in your browser."
echo "Press Ctrl+C here to stop the server."
wait $SERVER_PID

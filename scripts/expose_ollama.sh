#!/bin/bash
# Check if ngrok is authenticated
if ! ngrok config check > /dev/null 2>&1; then
    echo "Warning: ngrok might not be authenticated. If it fails, run: ngrok config add-authtoken <YOUR_TOKEN>"
fi

echo "Starting ngrok tunnel for Ollama on port 11434..."
echo "Press Ctrl+C to stop."
ngrok http 11434

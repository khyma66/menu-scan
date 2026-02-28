# Ollama Web UI

A simple, modern web interface for interacting with Ollama models locally.

## Features

- 🎨 **Modern UI** - Clean, responsive design with gradient styling
- 💬 **Real-time Chat** - Streaming responses for instant feedback
- 🤖 **Model Selection** - Easy switching between available models
- ⚙️ **Configurable** - Adjust temperature and max tokens
- 🔄 **Health Monitoring** - Real-time connection status
- 📱 **Responsive** - Works on desktop and mobile devices

## Prerequisites

- **Ollama** - Must be installed and running
  ```bash
  # Install Ollama (macOS)
  brew install ollama
  
  # Start Ollama service
  ollama serve
  ```

- **Python 3.8+** - For running the web UI
  ```bash
  python3 --version
  ```

## Quick Start

### Option 1: Using the startup script (Recommended)

```bash
cd ollama-webui
chmod +x start.sh
./start.sh
```

The script will:
1. Check if Ollama is running (start it if not)
2. Create a Python virtual environment
3. Install dependencies
4. Launch the web UI

### Option 2: Manual setup

```bash
# Navigate to the web UI directory
cd ollama-webui

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the web UI
python app.py
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|-----------|----------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `WEBUI_PORT` | `8080` | Web UI port |

### Example with custom configuration

```bash
export OLLAMA_URL=http://localhost:11434
export WEBUI_PORT=3000
python app.py
```

## Usage

1. **Open the Web UI**
   - Navigate to `http://localhost:8080` in your browser

2. **Select a Model**
   - Choose from the dropdown in the sidebar
   - Available models are automatically loaded from Ollama

3. **Start Chatting**
   - Type your message in the input box
   - Press Enter or click Send
   - Responses stream in real-time

4. **Adjust Settings**
   - **Temperature**: Controls randomness (0.0 - 2.0)
   - **Max Tokens**: Limits response length

5. **Clear Chat**
   - Click "Clear Chat" to start fresh

## API Endpoints

The web UI provides a REST API for programmatic access:

### List Models
```bash
GET /api/models
```

### Get Model Info
```bash
GET /api/models/{model_name}
```

### Chat (Streaming)
```bash
POST /api/chat
Content-Type: application/json

{
  "model": "qwen3:32b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true,
  "temperature": 0.7
}
```

### Generate Text
```bash
POST /api/generate
Content-Type: application/json

{
  "model": "qwen3:32b",
  "prompt": "Write a poem",
  "stream": true
}
```

### Health Check
```bash
GET /api/health
```

## Pulling Models

To use the web UI, you need to have at least one model pulled:

```bash
# List available models
ollama list

# Pull a model (example: Qwen3 32B)
ollama pull qwen3:32b

# Pull a smaller model for testing
ollama pull qwen3:4b
```

## Troubleshooting

### Ollama not connecting

1. Check if Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Start Ollama if not running:
   ```bash
   ollama serve
   ```

### Port already in use

Change the port using the `WEBUI_PORT` environment variable:

```bash
export WEBUI_PORT=3000
python app.py
```

### Dependencies not installing

Make sure you're using Python 3.8+:

```bash
python3 --version
```

If using an older Python, install a newer version:

```bash
brew install python@3.11
```

## Development

### Project Structure

```
ollama-webui/
├── app.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── start.sh           # Startup script
├── templates/
│   └── index.html    # Web UI template
└── README.md          # This file
```

### Running in development mode

```bash
# Install with development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Support

For issues or questions:
- Check the [Ollama documentation](https://github.com/ollama/ollama)
- Review the API docs at `http://localhost:8080/docs`

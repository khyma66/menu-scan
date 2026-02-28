# Local Model Web UI - Testing Guide

## Overview

This document provides information about the web UI options available for testing the local Ollama model (qwen3:32b) in the Menu OCR project.

## Available Web UI Options

### 1. FastAPI Swagger UI (Recommended for API Testing)

**URL:** http://localhost:8000/docs

**Features:**
- Interactive API documentation
- Test all API endpoints directly from the browser
- View request/response formats
- Authentication support
- Real-time testing

**Key Endpoints for Local Model Testing:**
- `GET /llm/status` - Check current LLM provider status
- `GET /llm/providers` - List all available LLM providers
- `POST /llm/switch` - Get configuration to switch providers
- `POST /llm/test` - Test the current LLM provider

**How to Use:**
1. Open http://localhost:8000/docs in your browser
2. Navigate to the "LLM Provider" section
3. Expand any endpoint to see details
4. Click "Try it out" to test the endpoint
5. Enter parameters and click "Execute"

### 2. Custom Local Model Web UI

**File:** `local-model-webui.html`

**URL:** Open the file directly in your browser (file://) or serve it via a web server

**Features:**
- User-friendly interface for testing the local model
- Real-time status checking
- Adjustable parameters (temperature, max tokens)
- Response time tracking
- Error handling and display
- Model information display

**How to Use:**
1. Open `local-model-webui.html` in your browser
2. The UI will automatically check the model status
3. Enter your prompt in the text area
4. Adjust temperature and max tokens as needed
5. Click "Test Model" to generate a response
6. View the response and statistics

### 3. Ollama Direct API (Advanced)

**Base URL:** http://localhost:11434

**API Endpoints:**
- `GET /api/tags` - List available models
- `POST /api/generate` - Generate text completion
- `POST /api/chat` - Chat completion
- `POST /api/embeddings` - Generate embeddings

**Example using curl:**
```bash
# List models
curl http://localhost:11434/api/tags

# Generate text
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:32b",
  "prompt": "Say hello",
  "stream": false
}'

# Chat completion
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:32b",
  "messages": [
    {"role": "user", "content": "Say hello"}
  ],
  "stream": false
}'
```

## Current Configuration

### Local Model Status
- **Provider:** Ollama
- **Model:** qwen3:32b
- **Type:** Local LLM
- **Privacy:** 100% - All data stays on your machine
- **Endpoint:** http://localhost:11434

### FastAPI Service Status
- **URL:** http://localhost:8000
- **Environment:** Development
- **Current LLM Provider:** kilocode (needs restart to use ollama)
- **Health Check:** http://localhost:8000/health

## Switching to Local Model

The `.env` file is already configured to use Ollama:
```
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:32b
```

However, the FastAPI service needs to be restarted to pick up the new configuration:

```bash
# Stop the current service (if running)
# Then restart it
cd fastapi-menu-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing the Local Model

### Option 1: Using the Custom Web UI
1. Open `local-model-webui.html` in your browser
2. Enter a prompt
3. Click "Test Model"
4. View the response

### Option 2: Using FastAPI Swagger UI
1. Open http://localhost:8000/docs
2. Navigate to `POST /llm/test`
3. Click "Try it out"
4. Execute the request
5. View the response

### Option 3: Using curl
```bash
curl -X POST http://localhost:8000/llm/test \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

## Troubleshooting

### Issue: "LLM provider test failed"
**Solution:** Ensure Ollama is running:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve
```

### Issue: "API not accessible"
**Solution:** Ensure FastAPI service is running:
```bash
cd fastapi-menu-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue: Model not responding
**Solution:** Check if the model is downloaded:
```bash
# List available models
ollama list

# If qwen3:32b is not available, pull it
ollama pull qwen3:32b
```

## Performance Tips

1. **Temperature:** Lower values (0.1-0.3) for more deterministic responses, higher values (0.7-1.0) for more creative responses
2. **Max Tokens:** Adjust based on your needs. Higher values allow longer responses but take more time
3. **System Resources:** Ensure you have sufficient RAM (at least 16GB recommended for qwen3:32b)
4. **GPU Acceleration:** If available, Ollama can use GPU acceleration for faster inference

## Security Considerations

- The local model runs entirely on your machine
- No data is sent to external servers
- Perfect for sensitive data processing
- Ensure your local network is secure if exposing the API

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qwen Model Documentation](https://huggingface.co/Qwen)

# Ollama Setup for Menu Enrichment

## Overview
The menu enrichment system now uses **Ollama with Qwen3:8b** model running locally instead of Puter.js.

## Prerequisites

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Windows
   # Download from https://ollama.com/download
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Pull Qwen3:8b Model**
   ```bash
   ollama pull qwen3:8b
   ```

## Configuration

The service uses these defaults:
- **Ollama URL**: `http://localhost:11434`
- **Model**: `qwen3:8b`

You can override these via environment variables:
```bash
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=qwen3:8b
```

Or add to `.env`:
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
```

## API Endpoints

### Check Ollama Status
```bash
curl http://localhost:8000/menu-enrichment/check-ollama
```

Response:
```json
{
  "success": true,
  "ollama_available": true,
  "model": "qwen3:8b",
  "base_url": "http://localhost:11434"
}
```

### Enrich Batch
```bash
curl -X POST "http://localhost:8000/menu-enrichment/enrich-batch?limit=10&offset=0"
```

### Enrich All Pending
```bash
curl -X POST "http://localhost:8000/menu-enrichment/enrich-all?batch_size=50"
```

## Performance

With local Ollama:
- **Much faster** than Puter.js (no network latency)
- **No rate limits** (except minimal throttling to avoid overwhelming)
- **0.5 seconds** delay between requests (vs 6 seconds for Puter.js)
- **~120 dishes per minute** (vs ~10 for Puter.js)
- **~7,200 dishes per hour** (vs ~600 for Puter.js)

### Processing Time Estimate

For 197,430 dishes:
- **~27 hours** with local Ollama (vs 329 hours with Puter.js)
- **~12x faster** than Puter.js

## Troubleshooting

### Ollama Not Running
```
Error: Connection refused
```
**Solution**: Start Ollama with `ollama serve`

### Model Not Found
```
Error: model 'qwen3:8b' not found
```
**Solution**: Pull the model with `ollama pull qwen3:8b`

### Check Available Models
```bash
ollama list
```

### Test Ollama Directly
```bash
curl http://localhost:11434/api/tags
```

### Test Model
```bash
ollama run qwen3:8b "What are the ingredients in pizza?"
```

## Advantages of Local Ollama

1. ✅ **No API costs** - completely free
2. ✅ **No rate limits** - process as fast as your hardware allows
3. ✅ **Privacy** - all data stays local
4. ✅ **Faster** - no network latency
5. ✅ **Reliable** - no external service dependencies
6. ✅ **Customizable** - can use any Ollama model

## Model Alternatives

If `qwen3:8b` doesn't work, try:
```bash
ollama pull qwen2.5:8b
ollama pull qwen:8b
ollama pull qwen2:8b
```

Then update the model name in your configuration.




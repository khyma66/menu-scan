# Menu OCR Backend Service

FastAPI backend service for processing menu images with OCR and AI enhancement.

## Features

- 🖼️ **Image Processing**: Upload and process menu images
- 📝 **OCR Extraction**: Extract text from menu images using Tesseract
- 🤖 **AI Enhancement**: Use OpenAI/Anthropic to enhance OCR results
- 💾 **Caching**: Redis-based caching for faster responses
- 🗄️ **Database**: Supabase for storing results
- 📊 **Health Checks**: Monitor service health
- 🔄 **Auto Documentation**: Interactive API docs with Swagger

## Tech Stack

- **FastAPI**: Modern Python web framework
- **Tesseract OCR**: Text extraction from images
- **Redis**: Caching layer
- **Supabase**: Database and storage
- **OpenAI/Anthropic**: LLM fallback for result enhancement
- **Docker**: Containerization

## Setup Instructions

### Prerequisites

- Python 3.11+
- Redis (running locally or Docker)
- Supabase account
- OpenAI or Anthropic API key (optional, for LLM enhancement)

### Local Development

1. **Clone and navigate to the project**
   ```bash
   cd fastapi-menu-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Start Redis (if not running)**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Or install Redis locally
   ```

6. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access API documentation**
   ```
   http://localhost:8000/docs
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t menu-ocr-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env menu-ocr-api
   ```

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status and dependencies.

### Process Image
```
POST /api/v1/ocr/process
```
Process a menu image and extract items.

**Request Body:**
```json
{
  "image_url": "https://example.com/menu.jpg",
  "use_llm_enhancement": true,
  "language": "en"
}
```

**Response:**
```json
{
  "success": true,
  "menu_items": [
    {
      "name": "Pasta Carbonara",
      "price": "$18.99",
      "description": null,
      "category": null
    }
  ],
  "raw_text": "...",
  "processing_time_ms": 1234,
  "enhanced": true,
  "cached": false
}
```

## Project Structure

```
fastapi-menu-service/
├── app/
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration management
│   ├── models.py         # Pydantic models
│   ├── routers/
│   │   └── ocr.py       # OCR processing endpoints
│   ├── services/
│   │   ├── redis_cache.py      # Redis caching
│   │   ├── supabase_client.py  # Database operations
│   │   └── llm_fallback.py     # LLM enhancement
│   └── utils/            # Utility functions
├── tests/                # Unit tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── .env.example         # Environment template
└── README.md            # This file
```

## Configuration

Edit `.env` file with your credentials:

- **Supabase**: Get URL and API key from your project settings
- **Redis**: Connection details (default: localhost:6379)
- **LLM Services**: Add API keys for OpenAI or Anthropic

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
ruff app/
```

## License

MIT


#!/usr/bin/env python3
"""
Ollama Web UI - Simple web interface for Ollama
"""
import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import uvicorn

app = FastAPI(title="Ollama Web UI", description="Simple web interface for Ollama")

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
WEBUI_PORT = int(os.getenv("WEBUI_PORT", "8080"))

# Templates
templates = Jinja2Templates(directory="templates")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = True
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class ModelInfo(BaseModel):
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/models")
async def list_models():
    """List all available Ollama models"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            return {"models": data.get("models", [])}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@app.get("/api/models/{model_name}")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/show", params={"name": model_name})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model info: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send a chat request to Ollama"""
    try:
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": request.stream,
        }
        
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            if "options" not in payload:
                payload["options"] = {}
            payload["options"]["num_predict"] = request.max_tokens
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                # Streaming response
                async def generate():
                    async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "message" in data:
                                        yield f"data: {json.dumps(data)}\n\n"
                                except json.JSONDecodeError:
                                    continue
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/event-stream")
            else:
                # Non-streaming response
                response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@app.post("/api/generate")
async def generate(request: ChatRequest):
    """Generate text using Ollama (simpler API)"""
    try:
        # Get the last message as prompt
        prompt = request.messages[-1].content if request.messages else ""
        
        payload = {
            "model": request.model,
            "prompt": prompt,
            "stream": request.stream,
        }
        
        if request.temperature is not None:
            payload["options"] = {"temperature": request.temperature}
        if request.max_tokens is not None:
            if "options" not in payload:
                payload["options"] = {}
            payload["options"]["num_predict"] = request.max_tokens
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            if request.stream:
                # Streaming response
                async def generate():
                    async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield f"data: {json.dumps(data)}\n\n"
                                except json.JSONDecodeError:
                                    continue
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(generate(), media_type="text/event-stream")
            else:
                # Non-streaming response
                response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                response.raise_for_status()
                return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Generate request failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Check if Ollama is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            return {"status": "healthy", "ollama_url": OLLAMA_URL}
    except httpx.HTTPError:
        return {"status": "unhealthy", "ollama_url": OLLAMA_URL}


def main():
    """Run the web UI"""
    print(f"🚀 Starting Ollama Web UI...")
    print(f"📡 Ollama URL: {OLLAMA_URL}")
    print(f"🌐 Web UI: http://localhost:{WEBUI_PORT}")
    print(f"📚 API Docs: http://localhost:{WEBUI_PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=WEBUI_PORT)


if __name__ == "__main__":
    main()

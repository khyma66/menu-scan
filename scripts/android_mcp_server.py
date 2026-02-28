import json
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx


class HealthProfileRequest(BaseModel):
    health_conditions: list[str] | None = None
    allergies: list[str] | None = None
    dietary_preferences: list[str] | None = None
    medical_notes: str | None = None


class McpCallRequest(BaseModel):
    method: str
    token: str
    payload: Dict[str, Any] | None = None


API_BASE = os.getenv("MENU_OCR_API_BASE", "http://127.0.0.1:8787")

app = FastAPI(title="android-mcp-server")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/mcp/call")
async def mcp_call(req: McpCallRequest):
    headers = {"Authorization": f"Bearer {req.token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        if req.method == "get_health_profile":
            resp = await client.get(f"{API_BASE}/v1/user/health-profile", headers=headers)
        elif req.method == "update_health_profile":
            resp = await client.put(
                f"{API_BASE}/v1/user/health-profile",
                headers=headers,
                json=req.payload or {},
            )
        elif req.method == "list_menus":
            resp = await client.get(f"{API_BASE}/v1/user/menus", headers=headers)
        else:
            raise HTTPException(status_code=400, detail="Unsupported MCP method")

    if resp.status_code >= 300:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

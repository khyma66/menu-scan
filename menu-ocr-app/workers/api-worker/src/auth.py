import os
import jwt
import httpx
from fastapi import Header, HTTPException

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
DEV_BYPASS_AUTH = os.getenv("DEV_BYPASS_AUTH", "false").lower() == "true"
DEV_BYPASS_USER_ID = os.getenv("DEV_BYPASS_USER_ID", "00000000-0000-0000-0000-000000000001")
DEV_BYPASS_EMAIL = os.getenv("DEV_BYPASS_EMAIL", "dev-bypass@example.com")
DEV_BYPASS_COUNTRY = os.getenv("DEV_BYPASS_COUNTRY", "IN")

async def get_user(authorization: str = Header(default="")):
    if DEV_BYPASS_AUTH:
        return {
            "id": DEV_BYPASS_USER_ID,
            "email": DEV_BYPASS_EMAIL,
            "country": DEV_BYPASS_COUNTRY,
            "dev_bypass": True,
        }

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "country": payload.get("user_metadata", {}).get("country"),
            }
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase auth not configured")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        data = resp.json()
        return {
            "id": data.get("id"),
            "email": data.get("email"),
            "country": data.get("user_metadata", {}).get("country"),
        }

import inspect
import json
import os
import uuid
from fastapi import FastAPI, Depends, UploadFile, HTTPException, File, Form
from auth import get_user
from supabase_db import SupabaseDB
from r2_store import R2Store

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.db = SupabaseDB()
    app.state.r2 = R2Store()

def _get_queue_binding():
    try:
        from js import OCR_QUEUE  # type: ignore

        return OCR_QUEUE
    except Exception:
        return globals().get("OCR_QUEUE")


async def send_to_queue(message: dict):
    queue = _get_queue_binding()
    if not queue:
        raise HTTPException(status_code=500, detail="Queue binding not configured")

    try:
        result = queue.send(message)
    except Exception:
        result = queue.send(json.dumps(message))

    if inspect.isawaitable(result):
        await result


def _is_dev_bypass_user(user: dict | None) -> bool:
    return bool(user and user.get("dev_bypass"))


async def _ensure_user_if_needed(user: dict):
    if _is_dev_bypass_user(user):
        return
    await app.state.db.ensure_user(user["id"], email=user.get("email"), country=user.get("country"))

@app.post("/v1/menus:scan")
async def scan_menu(
    pages: list[UploadFile] | None = File(default=None),
    files: list[UploadFile] | None = File(default=None),
    target_lang: str = Form("en"),
    user_country: str | None = Form(default=None),
    restaurant_name: str | None = Form(default=None),
    region: str | None = Form(default=None),
    cuisine_type: str | None = Form(default=None),
    user=Depends(get_user),
):
    uploads = pages or files or []
    if not uploads:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(uploads) > 3:
        raise HTTPException(status_code=400, detail="Max 3 pages allowed")

    await _ensure_user_if_needed(user)

    job_id = str(uuid.uuid4())
    user_id = user["id"]
    user_country = user_country or user.get("country", "IN")

    if restaurant_name and region:
        cached = await app.state.db.find_menu_by_user(user_id, restaurant_name, region)
        if cached:
            cached_keys = cached.get("r2_image_keys") or []
            await app.state.db.create_job(
                job_id=job_id,
                user_id=user_id,
                target_lang=target_lang,
                user_country=user_country,
                r2_keys=cached_keys,
                status="done",
                menu_id=cached.get("id"),
            )
            return {
                "job_id": job_id,
                "status": "done",
                "is_cached": True,
                "cache_hit_from": cached.get("created_at"),
                "menu_id": cached.get("id"),
            }

    r2_keys = []
    for idx, file in enumerate(uploads):
        key = f"menus/{user_id}/{job_id}/page_{idx}.jpg"
        await app.state.r2.upload(key, await file.read())
        r2_keys.append(key)

    await app.state.db.create_job(
        job_id=job_id,
        user_id=user_id,
        target_lang=target_lang,
        user_country=user_country,
        r2_keys=r2_keys,
        status="queued",
    )

    message = {
        "job_id": job_id,
        "user_id": user_id,
        "user_country": user_country,
        "target_lang": target_lang,
        "r2_keys": r2_keys,
        "restaurant_name": restaurant_name,
        "region": region,
        "cuisine_type": cuisine_type,
    }
    await send_to_queue(message)

    return {
        "job_id": job_id,
        "status": "queued",
        "is_cached": False,
        "cache_hit_from": None,
    }

@app.get("/v1/jobs/{job_id}")
async def get_job(job_id: str, user=Depends(get_user)):
    await _ensure_user_if_needed(user)
    job = await app.state.db.get_job(job_id, user["id"])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "done":
        menu = await app.state.db.get_menu(job["menu_id"], user["id"])
        personalized = await app.state.db.get_personalized_menu(menu["id"], user["id"])
        return {
            "job_id": job_id,
            "status": "done",
            "menu": {
                "id": menu["id"],
                "restaurant_name": menu.get("restaurant_name"),
                "region": menu.get("region"),
                "cuisine_type": menu.get("cuisine_type"),
                "ocr_raw": menu.get("ocr_raw"),
                "personalized": personalized,
            },
        }

    return {
        "job_id": job_id,
        "status": job["status"],
        "error": job.get("error"),
    }

@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/test-db")
async def test_db(user=Depends(get_user)):
    is_dev_bypass = _is_dev_bypass_user(user) if isinstance(user, dict) else False
    user_id = user.get("id") if isinstance(user, dict) and not is_dev_bypass else None
    if user_id:
        await _ensure_user_if_needed(user)
    inserted = await app.state.db.insert_test_job(user_id=user_id)
    return {
        "ok": True,
        "inserted": {
            "id": inserted.get("id"),
            "user_id": inserted.get("user_id"),
            "status": inserted.get("status"),
            "error": inserted.get("error"),
        },
    }


@app.get("/v1/user/menus")
async def list_user_menus(user=Depends(get_user)):
    await _ensure_user_if_needed(user)
    menus = await app.state.db.get_user_menus(user["id"])
    return {"menus": menus}


@app.get("/v1/menus/{menu_id}/personalized")
async def get_personalized_menu(menu_id: str, user=Depends(get_user)):
    await _ensure_user_if_needed(user)
    menu = await app.state.db.get_menu(menu_id, user["id"])
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    personalized = await app.state.db.get_personalized_menu(menu_id, user["id"])
    return {"menu_id": menu_id, "personalized": personalized}


@app.get("/v1/user/health-profile")
async def get_health_profile(user=Depends(get_user)):
    await _ensure_user_if_needed(user)
    profile = await app.state.db.get_health_profile(user["id"])
    return {"health_profile": profile}


@app.put("/v1/user/health-profile")
async def upsert_health_profile(payload: dict, user=Depends(get_user)):
    await _ensure_user_if_needed(user)
    await app.state.db.upsert_health_profile(user["id"], payload)
    profile = await app.state.db.get_health_profile(user["id"])
    return {"health_profile": profile}


@app.delete("/v1/user/account")
async def delete_user_account(user=Depends(get_user)):
    await app.state.db.delete_user_account(user["id"])
    return {"ok": True}

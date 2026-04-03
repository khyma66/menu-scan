"""Compatibility endpoints for legacy Android health profile and menus paths."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.routers.auth import get_current_user
from app.services.supabase_client import SupabaseClient

router = APIRouter(prefix="/v1/user", tags=["Health Profile Compat"])


class LegacyHealthProfileRequest(BaseModel):
    health_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    medical_notes: Optional[str] = None


class LegacyHealthProfilePayload(BaseModel):
    health_conditions: List[str]
    allergies: List[str]
    dietary_preferences: List[str]
    medical_notes: Optional[str] = None


class LegacyHealthProfileResponse(BaseModel):
    health_profile: LegacyHealthProfilePayload


def _clean(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    return [v.strip() for v in values if isinstance(v, str) and v.strip()]


@router.get("/health-profile", response_model=LegacyHealthProfileResponse)
async def get_health_profile_compat(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id") if current_user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    supabase = SupabaseClient()
    if not supabase.client:
        raise HTTPException(status_code=500, detail="Supabase unavailable")

    try:
        rows = (
            supabase.client.table("health_conditions")
            .select("condition_type,condition_name,description")
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )

        health_conditions: List[str] = []
        allergies: List[str] = []
        dietary_preferences: List[str] = []
        notes: List[str] = []

        for row in rows:
            condition_type = (row.get("condition_type") or "").lower().strip()
            condition_name = (row.get("condition_name") or "").strip()
            if not condition_name:
                continue
            if condition_type == "allergy":
                allergies.append(condition_name)
            elif condition_type in {"dietary", "preference"}:
                dietary_preferences.append(condition_name)
            else:
                health_conditions.append(condition_name)

            description = (row.get("description") or "").strip()
            if description:
                notes.append(description)

        return LegacyHealthProfileResponse(
            health_profile=LegacyHealthProfilePayload(
                health_conditions=health_conditions,
                allergies=allergies,
                dietary_preferences=dietary_preferences,
                medical_notes=" | ".join(notes[:6]) if notes else None,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load health profile: {str(exc)}")


@router.put("/health-profile", response_model=LegacyHealthProfileResponse)
async def update_health_profile_compat(
    request: LegacyHealthProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") if current_user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    supabase = SupabaseClient()
    if not supabase.client:
        raise HTTPException(status_code=500, detail="Supabase unavailable")

    health_conditions = _clean(request.health_conditions)
    allergies = _clean(request.allergies)
    dietary_preferences = _clean(request.dietary_preferences)
    medical_notes = (request.medical_notes or "").strip() or None

    try:
        supabase.client.table("health_conditions").delete().eq("user_id", user_id).execute()

        rows = []
        rows.extend(
            {
                "user_id": user_id,
                "condition_type": "illness",
                "condition_name": value,
                "description": medical_notes,
            }
            for value in health_conditions
        )
        rows.extend(
            {
                "user_id": user_id,
                "condition_type": "allergy",
                "condition_name": value,
                "description": medical_notes,
            }
            for value in allergies
        )
        rows.extend(
            {
                "user_id": user_id,
                "condition_type": "dietary",
                "condition_name": value,
                "description": medical_notes,
            }
            for value in dietary_preferences
        )

        if rows:
            supabase.client.table("health_conditions").insert(rows).execute()

        return LegacyHealthProfileResponse(
            health_profile=LegacyHealthProfilePayload(
                health_conditions=health_conditions,
                allergies=allergies,
                dietary_preferences=dietary_preferences,
                medical_notes=medical_notes,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save health profile: {str(exc)}")


# ──────────────────────────────────────────────────
# Legacy /v1/user/menus endpoint for Profile → Scans tab
# ──────────────────────────────────────────────────

class UserMenuEntry(BaseModel):
    id: str
    restaurant_name: Optional[str] = None
    region: Optional[str] = None
    cuisine_type: Optional[str] = None
    created_at: Optional[str] = None


class UserMenusListResponse(BaseModel):
    menus: List[UserMenuEntry]


@router.get("/menus", response_model=UserMenusListResponse)
async def get_user_menus(current_user: dict = Depends(get_current_user)):
    """
    Return scan history for the authenticated user.
    Reads from user_recent_scans table and maps to the legacy UserMenu format
    expected by the Android app.
    """
    user_id = current_user.get("id") if current_user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    supabase = SupabaseClient()
    if not supabase.client:
        raise HTTPException(status_code=500, detail="Supabase unavailable")

    try:
        response = (
            supabase.client.table("user_recent_scans")
            .select("id,source,image_name,detected_language,pipeline,scanned_at,dish_count")
            .eq("user_id", user_id)
            .order("scanned_at", desc=True)
            .limit(50)
            .execute()
        )

        scans = response.data or []

        menus = [
            UserMenuEntry(
                id=row.get("id", ""),
                restaurant_name=row.get("source") or row.get("image_name") or "Menu Scan",
                region=row.get("detected_language"),
                cuisine_type=row.get("pipeline"),
                created_at=row.get("scanned_at"),
            )
            for row in scans
        ]

        return UserMenusListResponse(menus=menus)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch menus: {str(exc)}")

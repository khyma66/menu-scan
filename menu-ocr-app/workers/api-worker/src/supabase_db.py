import os
import httpx
import uuid

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


class SupabaseDB:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Supabase service role not configured")

    def _headers(self):
        return {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

    async def create_job(
        self,
        job_id,
        user_id,
        target_lang,
        user_country,
        r2_keys,
        status="queued",
        menu_id=None,
        error=None,
    ):
        payload = {
            "id": job_id,
            "user_id": user_id,
            "target_lang": target_lang,
            "user_country": user_country,
            "r2_keys": r2_keys,
            "status": status,
            "menu_id": menu_id,
            "error": error,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/jobs",
                headers={**self._headers(), "Prefer": "return=representation"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else payload

    async def update_job(self, job_id, **updates):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.patch(
                f"{SUPABASE_URL}/rest/v1/jobs?id=eq.{job_id}",
                headers=self._headers(),
                json=updates,
            )
            resp.raise_for_status()
            return True

    async def get_job(self, job_id, user_id):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/jobs",
                headers=self._headers(),
                params={"id": f"eq.{job_id}", "user_id": f"eq.{user_id}", "select": "*"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None

    async def get_menu(self, menu_id, user_id):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/menus",
                headers=self._headers(),
                params={"id": f"eq.{menu_id}", "user_id": f"eq.{user_id}", "select": "*"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None

    async def find_menu_by_user(self, user_id, restaurant_name, region):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/menus",
                headers=self._headers(),
                params={
                    "user_id": f"eq.{user_id}",
                    "restaurant_name": f"eq.{restaurant_name}",
                    "region": f"eq.{region}",
                    "select": "*",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None

    async def get_personalized_menu(self, menu_id, user_id):
        payload = {"p_menu_id": menu_id, "p_user_id": user_id}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/rpc/get_personalized_menu",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_menus(self, user_id):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/menus",
                headers=self._headers(),
                params={"user_id": f"eq.{user_id}", "select": "*", "order": "created_at.desc"},
            )
            resp.raise_for_status()
            return resp.json()

    async def ensure_user(self, user_id, email=None, country=None):
        payload = {"id": user_id}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers={**self._headers(), "Prefer": "resolution=merge-duplicates"},
                json=payload,
            )
            if resp.status_code == 409:
                return True
            resp.raise_for_status()

            updates = {}
            if email:
                updates["email"] = email
            if country:
                updates["country"] = country
            if updates:
                patch_resp = await client.patch(
                    f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                    headers=self._headers(),
                    json=updates,
                )
                if patch_resp.status_code not in (200, 204, 409):
                    patch_resp.raise_for_status()
            return True

    async def upsert_health_profile(self, user_id, profile):
        payload = {
            "user_id": user_id,
            "health_conditions": profile.get("health_conditions"),
            "allergies": profile.get("allergies"),
            "dietary_preferences": profile.get("dietary_preferences"),
            "medical_notes": profile.get("medical_notes"),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/user_health_profiles",
                headers={**self._headers(), "Prefer": "resolution=merge-duplicates"},
                json=payload,
            )
            resp.raise_for_status()
            return True

    async def get_health_profile(self, user_id):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/user_health_profiles",
                headers=self._headers(),
                params={"user_id": f"eq.{user_id}", "select": "*"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else None

    async def insert_test_job(self, user_id=None):
        job_id = str(uuid.uuid4())
        payload = {
            "id": job_id,
            "user_id": user_id,
            "status": "queued",
            "r2_keys": [],
            "target_lang": "en",
            "user_country": "IN",
            "error": "test-db",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/jobs",
                headers={**self._headers(), "Prefer": "return=representation"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data[0] if data else payload

    async def delete_user_account(self, user_id):
        async with httpx.AsyncClient(timeout=15) as client:
            await client.delete(
                f"{SUPABASE_URL}/rest/v1/dish_health_recommendations?user_id=eq.{user_id}",
                headers=self._headers(),
            )
            await client.delete(
                f"{SUPABASE_URL}/rest/v1/dishes?user_id=eq.{user_id}",
                headers=self._headers(),
            )
            await client.delete(
                f"{SUPABASE_URL}/rest/v1/jobs?user_id=eq.{user_id}",
                headers=self._headers(),
            )
            await client.delete(
                f"{SUPABASE_URL}/rest/v1/menus?user_id=eq.{user_id}",
                headers=self._headers(),
            )
            await client.delete(
                f"{SUPABASE_URL}/rest/v1/user_health_profiles?user_id=eq.{user_id}",
                headers=self._headers(),
            )

            user_resp = await client.delete(
                f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}",
                headers=self._headers(),
            )
            if user_resp.status_code not in (200, 204):
                user_resp.raise_for_status()

            auth_resp = await client.delete(
                f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                },
            )
            if auth_resp.status_code not in (200, 204):
                auth_resp.raise_for_status()

            return True

# Menu OCR App v3 (LLM-Driven Health Recommendations)

This implementation follows the spec in docs/new_implementation/steps.txt and targets:
- Cloudflare Workers (API + queue consumer)
- Google Gemini Flash API (OCR + ingredients + nutrition + health recommendations)
- Supabase (health profiles + dish recommendations)
- Cloudflare R2 (image storage)

High-level flow:
1) Native apps upload menu images to API worker.
2) API worker stores images in R2, creates a job, enqueues it (cache hit returns instantly).
3) Consumer worker calls Gemini Flash, writes menus + dishes + health recommendations.
4) Apps either poll /v1/jobs/{job_id} or subscribe to Supabase Realtime on jobs.

## Credentials you will provide

Cloudflare:
- CF_ACCOUNT_ID
- CF_API_TOKEN (for wrangler deployments)
- R2_BUCKET
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY (or R2_ACCESS_KEY_SECRET)
- Native Queue binding: queue name menu-ocr-jobs (see wrangler.toml)

Supabase:
- SUPABASE_URL
- SUPABASE_ANON_KEY (for apps)
- SUPABASE_SERVICE_ROLE_KEY (server-side)
- SUPABASE_JWT_SECRET (for local JWT verification if needed)

Gemini:
- GEMINI_API_KEY
- GEMINI_MODEL (optional, default gemini-2.0-flash)
- GEMINI_API_BASE (optional, default v1beta endpoint)

## Local dev

1) Apply schema: menu-ocr-app/supabase/schema.sql
2) Add env vars from .env.example in each worker.
3) Run API worker locally (FastAPI). The consumer can be run as a worker or as a local script.

## Realtime option for apps

Recommended: Supabase Realtime on jobs table filtered by job id and user id.
Apps can listen for status changes (queued -> processing -> done/failed) and then fetch menu.

## API endpoints

POST /v1/menus:scan
- Multipart pages[] (or files[]) up to 3
- target_lang (optional, default "en")
- user_country (optional)
- restaurant_name (optional, enables cache hit)
- region (optional, enables cache hit)
- cuisine_type (optional)
Returns: {job_id, status, is_cached, cache_hit_from}

GET /v1/jobs/{job_id}
Returns: status and results when done (menu + personalized recommendations).

GET /v1/menus/{menu_id}/personalized
Returns: personalized menu recommendations for the current user.

GET /v1/user/health-profile
Returns: the current user's health profile.

PUT /v1/user/health-profile
Upserts the current user's health profile.

GET /v1/user/menus
Returns: list of menus.

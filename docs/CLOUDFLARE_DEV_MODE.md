# Cloudflare Dev Mode (while keeping localhost)

This setup keeps local FastAPI testing on `http://localhost:8000` and adds a temporary Cloudflare tunnel for dev-mode external testing.

## What stays unchanged

- Local API testing remains `http://localhost:8000`
- Existing frontend local flow remains `http://localhost:3000`

## One-command E2E test (local + Cloudflare)

From repo root:

```bash
chmod +x scripts/test_pipeline_local_and_cloudflare.sh
./scripts/test_pipeline_local_and_cloudflare.sh
```

What this script validates:

1. `GET /health` on localhost API
2. `GET /` on localhost API
3. `POST /ocr/process-upload` with `tests/assets/test_menu_clear.png`
4. Starts a temporary Cloudflare tunnel (if `cloudflared` exists)
5. Re-runs the same API tests via the tunnel URL

## cloudflared install (macOS)

If tunnel test is skipped due to missing CLI:

```bash
brew install cloudflared
```

Then rerun:

```bash
./scripts/test_pipeline_local_and_cloudflare.sh
```

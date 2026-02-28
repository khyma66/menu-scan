import json
import os
import urllib.request
import urllib.error


def check_gemini() -> dict:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.0-flash:generateContent?key=" + os.getenv("GEMINI_API_KEY", "")
    )
    payload = {
        "contents": [{"parts": [{"text": "Return JSON object with key ok=true"}]}],
        "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"ok": True, "status": resp.status}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:300]
        return {"ok": False, "status": exc.code, "error": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_groq() -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "qwen/qwen3-32b",
        "messages": [{"role": "user", "content": "Return JSON object with key ok=true"}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('GROQ_API_KEY', '')}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"ok": True, "status": resp.status}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")[:300]
        return {"ok": False, "status": exc.code, "error": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


if __name__ == "__main__":
    print(json.dumps({"gemini": check_gemini(), "groq": check_groq()}))

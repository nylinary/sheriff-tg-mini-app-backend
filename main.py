# backend.py (FastAPI) — logs every request + logs auth payload
import os
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl
import time
import hmac
import hashlib

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var (Telegram bot token).")

INITDATA_MAX_AGE_SECONDS = int(os.getenv("INITDATA_MAX_AGE_SECONDS", "300"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("miniapp")


app = FastAPI(title="MiniApp backend logger")

# --------- global request logger ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # basic request info
    ip = request.headers.get("x-forwarded-for") or request.client.host
    ua = request.headers.get("user-agent", "")
    log.info("REQ %s %s ip=%s ua=%s", request.method, request.url.path, ip, ua)

    # body logging for small JSON requests (avoid logging huge bodies in prod)
    body_bytes = await request.body()
    if body_bytes:
        # keep it safe-ish: truncate
        snippet = body_bytes[:2000]
        log.info("REQ_BODY %s", snippet.decode("utf-8", errors="replace"))

    # IMPORTANT: request.body() consumed; re-create request stream for downstream
    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}
    request._receive = receive  # noqa: SLF001 (ok for simple internal tooling)

    response = await call_next(request)
    log.info("RESP %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


# --------- telegram initData verification ----------
def _webapp_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

def _data_check_string(fields: Dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(fields.items(), key=lambda x: x[0]))

def verify_init_data(init_data: str, bot_token: str) -> Dict[str, str]:
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(400, "initData missing hash")

    try:
        auth_date = int(data.get("auth_date", "0"))
    except ValueError:
        raise HTTPException(400, "initData invalid auth_date")

    if auth_date <= 0:
        raise HTTPException(400, "initData missing auth_date")

    age = int(time.time()) - auth_date
    if age < 0:
        raise HTTPException(400, "auth_date in future")
    if age > INITDATA_MAX_AGE_SECONDS:
        raise HTTPException(401, "initData too old")

    dcs = _data_check_string(data)
    secret_key = _webapp_secret_key(bot_token)
    calc_hash = hmac.new(secret_key, dcs.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(401, "bad signature")

    return data


# --------- API ----------
class AuthPayload(BaseModel):
    initData: str
    meta: Optional[Dict[str, Any]] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/telegram-webapp")
async def auth_telegram_webapp(payload: AuthPayload, request: Request):
    # log meta separately (structured-ish)
    log.info("AUTH_META %s", json.dumps(payload.meta or {}, ensure_ascii=False))

    # verify initData
    verified = verify_init_data(payload.initData, BOT_TOKEN)

    # log parsed tg fields
    log.info("AUTH_VERIFIED_FIELDS %s", json.dumps(verified, ensure_ascii=False))

    # parse user json
    if "user" not in verified:
        raise HTTPException(400, "initData missing user")

    try:
        tg_user = json.loads(verified["user"])
    except Exception:
        raise HTTPException(400, "user is not valid JSON")

    log.info("TG_USER %s", json.dumps(tg_user, ensure_ascii=False))

    # demo response (replace with your real login/session)
    return JSONResponse(
        {
            "ok": True,
            "tg_user_id": tg_user.get("id"),
            "username": tg_user.get("username"),
        }
    )
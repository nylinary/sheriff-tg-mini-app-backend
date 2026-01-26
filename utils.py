import hmac
import hashlib
import time
from urllib.parse import parse_qsl
from fastapi import HTTPException

from settings import settings

INITDATA_MAX_AGE_SECONDS = settings.initdata_max_age_seconds

def _webapp_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

def _data_check_string(fields: dict) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(fields.items(), key=lambda x: x[0]))

def verify_init_data(init_data: str, bot_token: str) -> dict:
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

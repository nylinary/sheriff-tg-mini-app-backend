import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth_tokens import decode_token
from db import SessionLocal
from models.lead import Lead
from models.user import User
from schemas.lead import LeadCreate
from settings import settings
import httpx

log = logging.getLogger("miniapp")

leads_router = APIRouter()


async def get_db():
    async with SessionLocal() as session:
        yield session


def _get_access_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if (auth and auth.lower().startswith("bearer ")):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("access_token")


async def _get_current_user(request: Request, db: AsyncSession) -> User:
    token = _get_access_token(request)
    if not token:
        raise HTTPException(401, "Missing access token")

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(401, "Invalid access token")

    if payload.get("type") != "access":
        raise HTTPException(401, "Not an access token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(401, "Missing sub")

    try:
        tg_user_id = int(sub)
    except Exception:
        raise HTTPException(401, "Invalid sub")

    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")

    return user


# Map exchange labels to Webflow CMS field keys
_WEBFLOW_RATE_FIELDS: Dict[str, str] = {
    "USDT/USD": "usdt-to-usd-4",
    "USD/USDT": "usd-to-usdt-2",
    "USDT/EUR": "usdt-to-eur-4",
    "EUR/USDT": "eur-to-usdt-2",
    "USDT/RUB": "usdt-to-rub-5",
    "RUB/USDT": "rub-to-usdt-2",
    "USDT/AED": "usdt-to-aed-3",
    "AED/USDT": "aed-to-usdt-2",
}


async def _get_webflow_exchange_rate(city: str, exchange_type: str) -> Optional[str]:
    """Return the rate string from Webflow CMS for given city+exchange type, else None."""
    items_url = getattr(settings, "webflow_cms_items_url", None)
    api_key = getattr(settings, "webflow_api_key", None)
    if not items_url or not api_key:
        return None

    field_key = _WEBFLOW_RATE_FIELDS.get((exchange_type or "").strip())
    if not field_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    # Webflow v2 uses pagination via limit/offset; we keep it simple with limit=100.
    params = {"limit": 100, "offset": 0}

    try:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.get(items_url, headers=headers, params=params)

        if r.status_code < 200 or r.status_code >= 300:
            log.warning("Webflow CMS rates fetch failed: %s %s", r.status_code, r.text)
            return None

        data = r.json()
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return None

        city_norm = (city or "").strip().casefold()
        for it in items:
            if not isinstance(it, dict):
                continue
            fd = it.get("fieldData")
            if not isinstance(fd, dict):
                continue
            name = (fd.get("name") or "").strip().casefold()
            if name != city_norm:
                continue
            # found city item
            raw_rate = fd.get(field_key)
            if raw_rate is None:
                return None
            s = str(raw_rate).strip()
            return s if s != "" else None

        return None

    except Exception:
        log.exception("Webflow CMS rates fetch error")
        return None


async def _post_webhook_json(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    webhook_url = getattr(settings, "lead_webhook_url", None)
    if not webhook_url:
        log.info("Webhook forward disabled (LEAD_WEBHOOK_URL not set)")
        return None

    log.info("Webhook forward target: %s", webhook_url)

    # Leadteh inner_webhook expects:
    # {"contact_by": "telegram_id"|"telegram_name"|..., "search": "...", "variables": {...}}
    # See docs screenshot.
    contact_by = "telegram_id"
    search = str(payload.get("tg_user_id") or "").strip()

    # include exchange rate from Webflow CMS (may be None)
    exchange_rate = await _get_webflow_exchange_rate(
        str(payload.get("city") or ""),
        str(payload.get("exchange_type") or ""),
    )

    variables: Dict[str, Any] = {
        # core fields
        "lead_id": payload.get("lead_id"),
        "city": payload.get("city"),
        "exchange_type": payload.get("exchange_type"),
        "receive_type": payload.get("receive_type"),
        "sum": payload.get("sum"),
        "wallet_address": payload.get("wallet_address"),
        "exchange_rate": exchange_rate,
        # user fields
        "tg_user_id": payload.get("tg_user_id"),
        "username": payload.get("username"),
    }

    # Flatten meta into variables (Leadteh variables is an object)
    meta = payload.get("meta") or {}
    if isinstance(meta, dict):
        for k, v in meta.items():
            variables[f"meta_{k}"] = v

    webhook_payload: Dict[str, Any] = {
        "contact_by": contact_by,
        "search": search,
        "variables": variables,
    }

    try:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.post(webhook_url, json=webhook_payload)

        try:
            body = r.json()
        except Exception:
            body = r.text

        if 200 <= r.status_code < 300:
            log.info("Webhook delivered: %s", r.status_code)
        else:
            log.warning("Webhook responded with non-2xx: %s %s", r.status_code, r.text)

        return {"status": r.status_code, "body": body}

    except Exception as e:
        log.exception("Webhook call failed: %s", e)
        return {"status": 0, "error": str(e)}


@leads_router.post("/leads")
async def create_lead(body: LeadCreate, request: Request, db: AsyncSession = Depends(get_db)):
    log.info("LEADS_ENDPOINT_HIT %s %s from=%s", request.method, request.url.path, request.client.host if request.client else None)
    user = await _get_current_user(request, db)

    out: Dict[str, Any] = {
        "city": body.city,
        "exchange_type": body.exchange_type,
        "receive_type": body.receive_type,
        "sum": body.sum,
        "wallet_address": body.wallet_address,
        "tg_user_id": user.tg_user_id,
        "username": user.username,
        "meta": body.meta or {},
    }

    # Save to DB
    lead = Lead(
        tg_user_id=user.tg_user_id,
        username=user.username,
        city=body.city,
        exchange_type=body.exchange_type,
        receive_type=body.receive_type,
        sum=body.sum,
        wallet_address=body.wallet_address,
        meta=body.meta or {},
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)

    out["lead_id"] = lead.id

    # forward to webhook if configured
    webhook_url = getattr(settings, "lead_webhook_url", None)
    webhook_result = await _post_webhook_json(out)

    log.info("LEAD %s", out)
    if webhook_url:
        log.info("Webhook forward enabled: %s", webhook_url)

    return {
        "ok": True,
        "lead_id": lead.id,
        "forwarded": bool(webhook_url),
        "webhook_result": webhook_result,
    }

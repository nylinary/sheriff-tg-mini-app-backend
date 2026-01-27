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


async def _post_webhook_json(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    webhook_url = getattr(settings, "lead_webhook_url", None)
    if not webhook_url:
      # Not configured
      return None

    try:
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.post(webhook_url, json=payload)

        # Log non-2xx (common reason "it doesn't work")
        if r.status_code < 200 or r.status_code >= 300:
            log.warning("Webhook responded with non-2xx: %s %s", r.status_code, r.text)

        try:
            body = r.json()
        except Exception:
            body = r.text

        return {"status": r.status_code, "body": body}

    except Exception as e:
        # Make failures visible in logs and API response
        log.exception("Webhook call failed: %s", e)
        return {"status": 0, "error": str(e)}


@leads_router.post("/leads")
async def create_lead(body: LeadCreate, request: Request, db: AsyncSession = Depends(get_db)):
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

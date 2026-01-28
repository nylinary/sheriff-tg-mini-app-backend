import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db import SessionLocal
from schemas.aml import AMLCheckRequest
from settings import settings
from routers.leads import _get_current_user  # reuse existing auth logic

log = logging.getLogger("miniapp")

aml_router = APIRouter()


async def get_db():
    async with SessionLocal() as session:
        yield session


async def _post_aml_webhook_json(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    webhook_url = getattr(settings, "aml_webhook_url", None)
    if not webhook_url:
        log.info("AML webhook forward disabled (AML_WEBHOOK_URL not set)")
        return None

    contact_by = "telegram_name"
    search = str(payload.get("username") or "").strip() or str(payload.get("tg_user_id") or "").strip()

    variables: Dict[str, Any] = {
        "aml_wallet_address": payload.get("wallet_address"),
        "username": payload.get("username"),
    }

    webhook_payload: Dict[str, Any] = {
        "contact_by": contact_by,
        "search": search,
        "variables": variables,
    }

    log.info(
        "AML webhook request: contact_by=%s search=%s variables=%s",
        contact_by,
        search,
        {k: (str(v)[:500] if v is not None else None) for k, v in variables.items()},
    )

    try:
        timeout = httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.post(webhook_url, json=webhook_payload)

        try:
            body = r.json()
        except Exception:
            body = r.text

        if 200 <= r.status_code < 300:
            log.info("AML webhook delivered: %s", r.status_code)
        else:
            log.warning("AML webhook responded non-2xx: %s %s", r.status_code, r.text)

        return {"status": r.status_code, "body": body}

    except Exception as e:
        log.exception("AML webhook call failed: %s", e)
        return {"status": 0, "error": str(e)}


@aml_router.post("/aml/check")
async def aml_check(body: AMLCheckRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await _get_current_user(request, db)

    wallet = str(body.wallet_address or "").strip()
    if not wallet:
        raise HTTPException(400, "wallet_address is required")

    out: Dict[str, Any] = {
        "wallet_address": wallet,
        "tg_user_id": user.tg_user_id,
        "username": user.username,
        "meta": body.meta or {},
    }

    webhook_result = await _post_aml_webhook_json(out)

    return {
        "ok": True,
        "forwarded": bool(getattr(settings, "aml_webhook_url", None)),
        "webhook_result": webhook_result,
    }

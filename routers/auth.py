import json
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schemas.auth import AuthPayload
from utils import verify_init_data
from db import SessionLocal
from models.user import User
from settings import settings
from auth_tokens import create_token

BOT_TOKEN = settings.bot_token
log = logging.getLogger("miniapp")

auth_router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@auth_router.post("/auth/telegram-webapp")
async def auth_telegram_webapp(payload: AuthPayload, request: Request, db: AsyncSession = Depends(get_db)):
    log.info("AUTH_META %s", json.dumps(payload.meta or {}, ensure_ascii=False))
    verified = verify_init_data(payload.initData, BOT_TOKEN)
    log.info("AUTH_VERIFIED_FIELDS %s", json.dumps(verified, ensure_ascii=False))

    if "user" not in verified:
        raise HTTPException(400, "initData missing user")

    try:
        tg_user = json.loads(verified["user"])
    except Exception:
        raise HTTPException(400, "user is not valid JSON")

    log.info("TG_USER %s", json.dumps(tg_user, ensure_ascii=False))

    tg_user_id = tg_user.get("id")
    username = tg_user.get("username")
    if not tg_user_id:
        raise HTTPException(400, "Telegram user id missing")

    # Store or update user in DB
    result = await db.execute(select(User).where(User.tg_user_id == int(tg_user_id)))
    user = result.scalars().first()
    if user:
        user.username = username
    else:
        user = User(tg_user_id=int(tg_user_id), username=username)
        db.add(user)
    await db.commit()

    # Issue tokens
    subject = str(tg_user_id)
    access_token = create_token(token_type="access", subject=subject, ttl_seconds=settings.access_token_ttl_seconds)
    refresh_token = create_token(token_type="refresh", subject=subject, ttl_seconds=settings.refresh_token_ttl_seconds)

    resp = JSONResponse({
        "ok": True,
        "tg_user_id": tg_user_id,
        "username": username,
        # TEMP for testing in TG miniapp (remove later if using HttpOnly cookies only)
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_ttl_seconds,
    })

    # Set HttpOnly cookies
    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_ttl_seconds,
        path="/",
    )
    resp.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_ttl_seconds,
        path="/",
    )

    return resp

@auth_router.post("/auth/refresh")
async def refresh_tokens(request: Request):
    # Refresh using HttpOnly cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "No refresh_token cookie")

    from auth_tokens import decode_token

    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(401, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")

    subject = str(payload.get("sub"))
    access_token = create_token(token_type="access", subject=subject, ttl_seconds=settings.access_token_ttl_seconds)
    new_refresh_token = create_token(token_type="refresh", subject=subject, ttl_seconds=settings.refresh_token_ttl_seconds)

    resp = JSONResponse({
        "ok": True,
        # TEMP for testing
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_ttl_seconds,
    })

    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_ttl_seconds,
        path="/",
    )
    resp.set_cookie(
        "refresh_token",
        new_refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_ttl_seconds,
        path="/",
    )

    return resp

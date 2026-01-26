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
    
    # Store or update user in DB
    tg_user_id = tg_user.get("id")
    username = tg_user.get("username")
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalars().first()
    if user:
        user.username = username
    else:
        user = User(tg_user_id=tg_user_id, username=username)
        db.add(user)
    await db.commit()
    
    return JSONResponse({
        "ok": True,
        "tg_user_id": tg_user_id,
        "username": username,
    })

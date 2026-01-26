from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import SessionLocal
from models.user import User
from auth_tokens import decode_token

users_router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

def _get_access_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("access_token")

@users_router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
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

    return {"id": user.id, "tg_user_id": user.tg_user_id, "username": user.username}

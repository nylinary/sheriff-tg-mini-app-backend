from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db import SessionLocal
from models.user import User

users_router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@users_router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "No access_token cookie")
    # For demo: treat token as tg_user_id
    try:
        tg_user_id = int(token)
    except Exception:
        raise HTTPException(400, "Invalid access_token")
    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "tg_user_id": user.tg_user_id, "username": user.username}

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import SessionLocal
from models.user import User
from models.lead import Lead
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


def _get_tg_user_id_from_request(request: Request) -> str:
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

    tg_user_id = str(sub).strip()
    if not tg_user_id.isdigit():
        raise HTTPException(401, "Invalid sub")

    return tg_user_id


@users_router.get("/me")
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    tg_user_id = _get_tg_user_id_from_request(request)

    result = await db.execute(select(User).where(User.tg_user_id == tg_user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(404, "User not found")

    return {"id": user.id, "tg_user_id": user.tg_user_id, "username": user.username}


@users_router.get("/me/applications")
async def my_applications(request: Request, db: AsyncSession = Depends(get_db)):
    """Return all leads (applications) for the current user."""
    tg_user_id = _get_tg_user_id_from_request(request)

    result = await db.execute(
        select(Lead)
        .where(Lead.tg_user_id == tg_user_id)
        .order_by(Lead.created_at.desc())
    )
    leads = result.scalars().all()

    return {
        "ok": True,
        "items": [
            {
                "id": lead.id,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "city": lead.city,
                "exchange_type": lead.exchange_type,
                "receive_type": lead.receive_type,
                "sum": lead.sum,
                "wallet_address": lead.wallet_address,
                "meta": lead.meta,
            }
            for lead in leads
        ],
    }

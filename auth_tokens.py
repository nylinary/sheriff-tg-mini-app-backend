import time
from typing import Dict, Any, Literal

import jwt
from settings import settings

TokenType = Literal["access", "refresh"]


def _now() -> int:
    return int(time.time())


def create_token(*, token_type: TokenType, subject: str, ttl_seconds: int) -> str:
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": _now(),
        "exp": _now() + int(ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

from pydantic import BaseModel
from typing import Any, Dict, Optional

class AuthPayload(BaseModel):
    initData: str
    meta: Optional[Dict[str, Any]] = None

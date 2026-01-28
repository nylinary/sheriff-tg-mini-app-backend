from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class AMLCheckRequest(BaseModel):
    wallet_address: str = Field(..., min_length=1, max_length=256)
    meta: Optional[Dict[str, Any]] = None

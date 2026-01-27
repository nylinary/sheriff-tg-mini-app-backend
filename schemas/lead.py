from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class LeadCreate(BaseModel):
    city: str = Field(..., min_length=1)
    exchange_type: str = Field(..., min_length=1)
    receive_type: str = Field(..., min_length=1)
    sum: str = Field(..., min_length=1)
    wallet_address: str = Field(..., min_length=1)
    meta: Optional[Dict[str, Any]] = None

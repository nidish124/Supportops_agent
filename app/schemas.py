from fastapi.openapi.models import OpenIdConnect
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class triage_metadata(BaseModel):
    product_version: Optional[str] = None
    timestamp: Optional[datetime] = None
    region: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    product_name: Optional[str] = None

class triageRequest(BaseModel):
    request_id: str = Field(..., description="The request id of the product")
    user_id: str = Field(..., description="The user id of the product")
    channel: str = Field(..., description="The channel of the product")
    message: str = Field(..., description="The message of the product")
    metadata: Optional[triage_metadata] = None



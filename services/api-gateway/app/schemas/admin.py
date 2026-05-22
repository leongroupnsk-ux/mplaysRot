from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    totp_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminUserPatch(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    users_last_30d: int


class AdminTotpSetupOut(BaseModel):
    totp_secret: str
    totp_uri: str
    message: str

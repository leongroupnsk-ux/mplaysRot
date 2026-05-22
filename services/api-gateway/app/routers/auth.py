import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.user import User, RefreshToken
from app.schemas.auth import TokenResponse, LoginRequest, RegisterRequest, UserOut, UpdateProfileRequest
from app.utils.jwt import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, hash_refresh_token,
)
from app.utils.deps import get_current_user
from app.utils.limiter import limiter

router = APIRouter()

_AUTH_LIMIT = "10/minute"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(_AUTH_LIMIT)
async def register(request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="owner",
    )
    db.add(user)
    await db.flush()  # получаем user.id до commit

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    await _store_refresh_token(db, user.id, refresh)
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(_AUTH_LIMIT)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    await _store_refresh_token(db, user.id, refresh)
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(_AUTH_LIMIT)
async def refresh(request: Request, body: dict, db: AsyncSession = Depends(get_db)):
    token = body.get("refresh_token", "")
    exc = HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise exc
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise exc

    token_hash = hash_refresh_token(token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise exc

    # Ротация: старый токен удаляем, выдаём новую пару
    await db.delete(stored)

    access = create_access_token(str(user_id))
    new_refresh = create_refresh_token(str(user_id))
    await _store_refresh_token(db, user_id, new_refresh)
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.new_password:
        if not payload.current_password:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="current_password is required to set a new password")
        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail="Current password is incorrect")
        if len(payload.new_password) < 8:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Password must be at least 8 characters")
        current_user.password_hash = hash_password(payload.new_password)

    await db.commit()
    await db.refresh(current_user)
    return current_user


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _store_refresh_token(db: AsyncSession, user_id: uuid.UUID, token: str) -> None:
    from datetime import timedelta
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(token),
        expires_at=expires,
    ))

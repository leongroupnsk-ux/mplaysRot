"""
Чтение/запись платформенных настроек с Redis-кэшем.
Кэш TTL = 300 сек (5 мин) — настройки меняются редко.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.models.platform_settings import PlatformSetting
from app.utils.crypto import encrypt_token, decrypt_token

_CACHE_TTL = 300  # секунд


async def get_platform_setting(key: str, db: AsyncSession) -> str | None:
    """Возвращает расшифрованное значение настройки; сначала проверяет Redis-кэш.
    Если таблица platform_settings ещё не создана (до применения миграции) —
    молча возвращает None, чтобы логика упала на ключ пользователя.
    """
    redis = get_redis()
    cache_key = f"platform_setting:{key}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return cached if cached != "__NONE__" else None
    except Exception:
        pass

    try:
        # Используем savepoint чтобы при ошибке (таблица не существует)
        # не ломать всю внешнюю транзакцию — достаточно откатить только точку сохранения.
        async with db.begin_nested():
            row = (await db.execute(
                select(PlatformSetting).where(PlatformSetting.key == key)
            )).scalar_one_or_none()
    except Exception:
        # Таблица ещё не создана — деградируем без ошибки.
        # begin_nested() уже откатил savepoint, внешняя транзакция цела.
        return None

    value = decrypt_token(row.value_enc) if (row and row.value_enc) else None

    try:
        await redis.setex(cache_key, _CACHE_TTL, value if value is not None else "__NONE__")
    except Exception:
        pass

    return value


async def set_platform_setting(
    key: str,
    value: str,
    admin_email: str,
    db: AsyncSession,
) -> None:
    """Сохраняет зашифрованное значение; сбрасывает Redis-кэш."""
    from datetime import datetime, timezone

    row = (await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )).scalar_one_or_none()

    if row:
        row.value_enc = encrypt_token(value)
        row.updated_by = admin_email
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(PlatformSetting(
            key=key,
            value_enc=encrypt_token(value),
            updated_by=admin_email,
        ))

    await db.commit()

    try:
        redis = get_redis()
        await redis.delete(f"platform_setting:{key}")
    except Exception:
        pass


async def delete_platform_setting(key: str, admin_email: str, db: AsyncSession) -> None:
    """Удаляет настройку и кэш."""
    row = (await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
    try:
        redis = get_redis()
        await redis.delete(f"platform_setting:{key}")
    except Exception:
        pass

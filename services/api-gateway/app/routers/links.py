"""
/v1/links — CRUD диплинков и публичный резолвер.
Публичные маршруты (без авторизации): /resolve/{code} и /resolve/{code}/click.
"""
import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.catalog import Product, Store
from app.models.connections import MarketplaceConnection
from app.models.links import DeepLink, LinkClick
from app.models.user import User
from app.schemas.links import (
    DeepLinkCreate, DeepLinkOut, DeepLinkPublicOut, DeepLinkUpdate,
    ClickTrackRequest, VerifySkuResponse,
)
from app.utils.crypto import decrypt_token
from app.utils.deps import get_current_user

router = APIRouter()
log = logging.getLogger(__name__)

_SYSTEM_DOMAIN = "attribly.ru"


@dataclass
class _WBProductInfo:
    title: str
    image_url: Optional[str]
    price: Optional[str]


async def _get_wb_api_key(db: AsyncSession, user: User) -> Optional[str]:
    """Возвращает расшифрованный WB API-ключ пользователя, если подключение активно."""
    # Фиксируем user.id ДО любых операций с сессией — иначе после rollback
    # SQLAlchemy пометит объект expired и lazy-load упадёт в сломанной транзакции.
    user_id = user.id

    from app.services.platform_settings import get_platform_setting
    try:
        platform_key = await get_platform_setting("wb_service_key", db)
        if platform_key:
            return platform_key
    except Exception:
        try:
            await db.rollback()
        except Exception:
            pass

    r = await db.execute(
        select(MarketplaceConnection).where(
            MarketplaceConnection.user_id == user_id,
            MarketplaceConnection.marketplace == "wildberries",
            MarketplaceConnection.status == "active",
        ).limit(1)
    )
    conn = r.scalars().first()
    if not conn:
        return None
    return decrypt_token(conn.api_key_enc)


def _extract_nm_id(raw: str) -> Optional[str]:
    """
    Извлекает nmId из строки — либо уже число, либо URL вида
    wildberries.ru/catalog/390366406/detail.aspx.
    """
    raw = raw.strip()
    if raw.isdigit():
        return raw
    # Парсим URL: ищем /catalog/<nmId>/
    import re
    m = re.search(r"/catalog/(\d+)", raw)
    if m:
        return m.group(1)
    return None


async def _fetch_wb_product_info(nm_id: str, api_key: str) -> Optional[_WBProductInfo]:
    """
    Запрашивает карточку товара из WB Content API v2 по nmId.
    Возвращает None если товар не найден или произошла ошибка.
    """
    clean = _extract_nm_id(nm_id)
    if not clean:
        return None
    try:
        nm_id_int = int(clean)
    except ValueError:
        return None

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://content-api.wildberries.ru/content/v2/get/cards/list",
                headers={"Authorization": api_key, "Content-Type": "application/json"},
                json={
                    "settings": {
                        "cursor": {"limit": 1},
                        "filter": {"nmIds": [nm_id_int]},
                    }
                },
            )
        if resp.status_code != 200:
            log.warning("WB Content API returned %s for nmId %s", resp.status_code, nm_id)
            return None

        data = resp.json()
        cards = data.get("cards") or []
        if not cards:
            return None

        card = cards[0]
        title = card.get("title") or card.get("name") or f"Товар WB #{nm_id}"

        # Цена: sizes[0].price или discountedPrice
        price_val: Optional[str] = None
        sizes = card.get("sizes") or []
        if sizes:
            raw_price = sizes[0].get("price") or sizes[0].get("discountedPrice")
            if raw_price:
                try:
                    price_val = str(int(raw_price) // 100)  # kopecks → roubles
                except Exception:
                    price_val = str(raw_price)

        # Фото: photos[0].big или tm
        image_url: Optional[str] = None
        photos = card.get("photos") or []
        if photos:
            image_url = photos[0].get("big") or photos[0].get("tm")

        return _WBProductInfo(title=title, image_url=image_url, price=price_val)

    except Exception as exc:
        log.warning("WB Content API fetch failed for nmId %s: %s", nm_id, exc)


def _short_code() -> str:
    return secrets.token_urlsafe(6)[:8]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"


# ── Private routes (auth required) ───────────────────────────────────────────

@router.get("", response_model=list[DeepLinkOut])
async def list_links(
    marketplace: Optional[str] = None,
    link_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(DeepLink)
        .where(DeepLink.user_id == current_user.id)
        .order_by(DeepLink.created_at.desc())
    )
    if marketplace:
        q = q.where(DeepLink.marketplace == marketplace)
    if link_type:
        q = q.where(DeepLink.link_type == link_type)
    return (await db.execute(q)).scalars().all()


@router.get("/verify-sku", response_model=VerifySkuResponse)
async def verify_sku(
    store_id: str,
    external_product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Проверяет принадлежность SKU к магазину пользователя."""
    try:
        sid = uuid.UUID(store_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid store_id")

    # Нормализуем: если передан полный URL — вытаскиваем nmId
    clean_id = _extract_nm_id(external_product_id) or external_product_id

    # Verify store belongs to user
    store_r = await db.execute(
        select(Store).where(Store.id == sid, Store.user_id == current_user.id)
    )
    store = store_r.scalar_one_or_none()
    if not store:
        return VerifySkuResponse(valid=False, message="Магазин не найден или не принадлежит вам")

    # ── 1. Ищем в локальной БД ────────────────────────────────────────────────
    prod_r = await db.execute(
        select(Product).where(
            Product.store_id == sid,
            Product.external_product_id == clean_id,
            Product.is_active == True,
            Product.is_archived == False,
        )
    )
    product = prod_r.scalar_one_or_none()
    if product:
        return VerifySkuResponse(
            valid=True,
            product_title=product.title,
            product_image=product.image_url,
            product_price=str(product.price) if product.price else None,
        )

    # ── 2. Фолбек: пробуем WB Content API (только свои товары) ───────────────
    if store.provider == "wildberries":
        try:
            api_key = await _get_wb_api_key(db, current_user)
            if api_key:
                wb_info = await _fetch_wb_product_info(clean_id, api_key)
                if wb_info:
                    return VerifySkuResponse(
                        valid=True,
                        product_title=wb_info.title,
                        product_image=wb_info.image_url,
                        product_price=wb_info.price,
                    )
        except Exception:
            pass

        # ── 3. nmId валиден — магазин WB подключён → разрешаем без каталога ──
        if clean_id.isdigit():
            return VerifySkuResponse(
                valid=True,
                product_title=f"Товар WB #{clean_id}",
                product_image=None,
                product_price=None,
            )

    return VerifySkuResponse(
        valid=False,
        message=f"Товар с артикулом {clean_id} не найден. "
                "Проверьте правильность артикула.",
    )


@router.post("", response_model=DeepLinkOut, status_code=201)
async def create_link(
    payload: DeepLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sid = uuid.UUID(payload.store_id)
    except ValueError:
        raise HTTPException(400, detail="Invalid store_id")

    # Verify store ownership
    store_r = await db.execute(
        select(Store).where(Store.id == sid, Store.user_id == current_user.id)
    )
    if not store_r.scalar_one_or_none():
        raise HTTPException(403, detail="Store not found or access denied")

    # Нормализуем артикул (может прийти полный URL)
    clean_ext_id = _extract_nm_id(payload.external_product_id) or payload.external_product_id

    # ── Verify SKU: локальная БД → фолбек WB API ─────────────────────────────
    prod_r = await db.execute(
        select(Product).where(
            Product.store_id == sid,
            Product.external_product_id == clean_ext_id,
            Product.is_active == True,
            Product.is_archived == False,
        )
    )
    product = prod_r.scalar_one_or_none()

    # Данные для ссылки: из локальной БД, потом из payload, потом из WB API
    p_title: Optional[str] = payload.product_title or (product.title if product else None)
    p_image: Optional[str] = payload.product_image or (product.image_url if product else None)
    p_price: Optional[str] = payload.product_price or (str(product.price) if product and product.price else None)

    if not product and payload.marketplace == "wildberries":
        # Пробуем получить данные из WB Content API
        try:
            api_key = await _get_wb_api_key(db, current_user)
            if api_key:
                wb_info = await _fetch_wb_product_info(clean_ext_id, api_key)
                if wb_info:
                    p_title = p_title or wb_info.title
                    p_image = p_image or wb_info.image_url
                    p_price = p_price or wb_info.price
                    product = True  # type: ignore[assignment]
        except Exception:
            pass
        # Если nmId валидный — разрешаем даже без данных из каталога
        if not product and clean_ext_id.isdigit():
            product = True  # type: ignore[assignment]
            p_title = p_title or f"Товар WB #{clean_ext_id}"

    if not product:
        raise HTTPException(
            422,
            detail=f"Товар с артикулом {clean_ext_id} не найден. "
                   "Проверьте правильность артикула.",
        )

    # Generate unique short_code
    for _ in range(10):
        code = _short_code()
        existing = await db.execute(select(DeepLink).where(DeepLink.short_code == code))
        if not existing.scalar_one_or_none():
            break

    link = DeepLink(
        user_id=current_user.id,
        store_id=sid,
        marketplace=payload.marketplace,
        external_product_id=clean_ext_id,
        product_title=p_title,
        product_image=p_image,
        product_price=p_price,
        link_type=payload.link_type,
        short_code=code,
        name=payload.name,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_term=payload.utm_term,
        utm_content=payload.utm_content,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.get("/{link_id}/stats")
async def get_link_stats(
    link_id: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Статистика по ссылке: клики по дням, устройства, источники (referer).
    days — глубина в днях (по умолчанию 30).
    """
    from sqlalchemy import func as sqlfunc, cast, Date as SADate, text
    lid = uuid.UUID(link_id)

    # Проверка владельца
    r = await db.execute(
        select(DeepLink).where(DeepLink.id == lid, DeepLink.user_id == current_user.id)
    )
    link = r.scalar_one_or_none()
    if not link:
        raise HTTPException(404, detail="Link not found")

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Все клики за период
    clicks_r = await db.execute(
        select(LinkClick).where(
            LinkClick.deep_link_id == lid,
            LinkClick.clicked_at >= since,
        ).order_by(LinkClick.clicked_at)
    )
    clicks = clicks_r.scalars().all()

    # Клики по дням
    daily: dict[str, int] = {}
    device_counts: dict[str, int] = {"mobile": 0, "desktop": 0, "tablet": 0, "unknown": 0}
    source_counts: dict[str, int] = {}

    for c in clicks:
        day = c.clicked_at.strftime("%Y-%m-%d")
        daily[day] = daily.get(day, 0) + 1
        dev = c.device_type or "unknown"
        device_counts[dev] = device_counts.get(dev, 0) + 1
        # Источник: берём domain из referer или "direct"
        src = "direct"
        if c.referer:
            try:
                from urllib.parse import urlparse
                h = urlparse(c.referer).hostname or "direct"
                src = h.replace("www.", "")
            except Exception:
                src = "other"
        source_counts[src] = source_counts.get(src, 0) + 1

    # Заполняем пропущенные дни нулями
    from datetime import date, timedelta as td
    today = datetime.now(timezone.utc).date()
    start = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date()
    daily_full = []
    d = start
    while d <= today:
        ds = d.strftime("%Y-%m-%d")
        daily_full.append({"date": ds, "clicks": daily.get(ds, 0)})
        d += td(days=1)

    total_clicks = len(clicks)

    # Воронка: уникальные IP (охват) → клики → (заказы — пока нет данных, будет 0)
    unique_visitors = len({c.ip_hash for c in clicks})

    # Топ источников для воронки многоканальности
    top_sources = sorted(source_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "link": {
            "id": str(link.id),
            "name": link.name,
            "short_code": link.short_code,
            "external_product_id": link.external_product_id,
            "product_title": link.product_title,
            "product_image": link.product_image,
            "marketplace": link.marketplace,
            "utm_source": link.utm_source,
            "utm_medium": link.utm_medium,
            "utm_campaign": link.utm_campaign,
            "status": link.status,
            "created_at": link.created_at.isoformat(),
        },
        "summary": {
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "orders": 0,          # будет заполняться из attribution
            "conversion_rate": 0,
            "days": days,
        },
        "daily": daily_full,
        "devices": device_counts,
        "sources": [{"source": s, "clicks": c} for s, c in top_sources],
        "funnel": [
            {"stage": "Показы",         "value": None,           "note": "нет данных"},
            {"stage": "Уникальные",      "value": unique_visitors, "note": f"за {days} дн."},
            {"stage": "Клики",           "value": total_clicks,    "note": f"за {days} дн."},
            {"stage": "Заказы",          "value": 0,               "note": "требует attribution"},
            {"stage": "Выкупы",          "value": 0,               "note": "требует attribution"},
        ],
    }


@router.get("/{link_id}", response_model=DeepLinkOut)
async def get_link(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(DeepLink).where(
            DeepLink.id == uuid.UUID(link_id),
            DeepLink.user_id == current_user.id,
        )
    )
    link = r.scalar_one_or_none()
    if not link:
        raise HTTPException(404, detail="Link not found")
    return link


@router.patch("/{link_id}", response_model=DeepLinkOut)
async def update_link(
    link_id: str,
    payload: DeepLinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(DeepLink).where(
            DeepLink.id == uuid.UUID(link_id),
            DeepLink.user_id == current_user.id,
        )
    )
    link = r.scalar_one_or_none()
    if not link:
        raise HTTPException(404, detail="Link not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(link, k, v)
    link.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(link)
    return link


@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(DeepLink).where(
            DeepLink.id == uuid.UUID(link_id),
            DeepLink.user_id == current_user.id,
        )
    )
    link = r.scalar_one_or_none()
    if not link:
        raise HTTPException(404, detail="Link not found")
    await db.delete(link)
    await db.commit()


# ── Public routes (no auth) ───────────────────────────────────────────────────

@router.get("/resolve/{short_code}", response_model=DeepLinkPublicOut)
async def resolve_link(short_code: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(DeepLink).where(DeepLink.short_code == short_code))
    link = r.scalar_one_or_none()
    if not link:
        raise HTTPException(404, detail="Link not found")
    return link


# ── Server-side redirect: /l/{short_code} ─────────────────────────────────────
# Nginx routes attribly.ru/l/* → api-gateway → this handler.
# Builds the marketplace URL and sends 302 immediately (no JS required).

from fastapi.responses import RedirectResponse as _RedirectResponse
from urllib.parse import urlencode as _urlencode

@router.get("/redirect/{short_code}", include_in_schema=False)
async def redirect_short_link(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Публичный редирект /l/{short_code} → marketplace URL.
    Логирует клик и делает 302 на web-URL маркетплейса.
    """
    r = await db.execute(select(DeepLink).where(DeepLink.short_code == short_code))
    link = r.scalar_one_or_none()

    if not link or link.status not in ("active",):
        # Ссылка не найдена или на паузе — показываем страницу 404 на фронте
        return _RedirectResponse(url=f"/not-found?code={short_code}", status_code=302)

    # Логируем клик асинхронно (не блокируем редирект)
    try:
        ip = _safe_ip(request)
        ua = request.headers.get("user-agent", "")
        referer = request.headers.get("referer")
        device = _detect_device(ua)
        db.add(LinkClick(
            deep_link_id=link.id,
            ip_hash=_hash(ip),
            user_agent=ua,
            device_type=device,
            referer=referer,
        ))
        link.click_count += 1
        link.updated_at = datetime.now(timezone.utc)
        await db.commit()
    except Exception:
        pass  # не мешаем редиректу даже при ошибке логирования

    # Строим marketplace web URL с UTM
    utm: dict[str, str] = {}
    if link.utm_source:   utm["utm_source"]   = link.utm_source
    if link.utm_medium:   utm["utm_medium"]   = link.utm_medium
    if link.utm_campaign: utm["utm_campaign"] = link.utm_campaign
    if link.utm_term:     utm["utm_term"]     = link.utm_term
    if link.utm_content:  utm["utm_content"]  = link.utm_content

    qs = f"?{_urlencode(utm)}" if utm else ""

    if link.marketplace == "wildberries":
        url = f"https://www.wildberries.ru/catalog/{link.external_product_id}/detail.aspx{qs}"
    elif link.marketplace == "ozon":
        url = f"https://www.ozon.ru/product/{link.external_product_id}/{qs}"
    else:
        url = f"https://www.wildberries.ru/catalog/{link.external_product_id}/detail.aspx{qs}"

    return _RedirectResponse(url=url, status_code=302)


def _safe_ip(request: Request) -> str:
    """Безопасно получает IP клиента, не падает если request.client is None."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/resolve/{short_code}/click", status_code=204)
async def track_click(
    short_code: str,
    payload: ClickTrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(DeepLink).where(DeepLink.short_code == short_code))
    link = r.scalar_one_or_none()
    if not link:
        return

    ip_hash = _hash(_get_ip(request))
    device_type = payload.device_type or _detect_device(payload.user_agent or "")

    db.add(LinkClick(
        deep_link_id=link.id,
        ip_hash=ip_hash,
        user_agent=payload.user_agent,
        device_type=device_type,
        referer=payload.referer,
    ))
    link.click_count += 1
    link.updated_at = datetime.now(timezone.utc)
    await db.commit()


def _detect_device(ua: str) -> str:
    ua_lower = ua.lower()
    if any(x in ua_lower for x in ("ipad", "tablet", "kindle")):
        return "tablet"
    if any(x in ua_lower for x in ("mobile", "android", "iphone", "ipod")):
        return "mobile"
    return "desktop"

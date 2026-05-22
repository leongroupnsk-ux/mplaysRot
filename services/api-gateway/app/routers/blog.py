"""
/v1/blog — публичное API блога.
Просмотры: один IP в сутки = 1 просмотр.
Лайки: один IP = один лайк (toggle).
"""
import hashlib
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.blog import BlogArticle, BlogView, BlogLike
from app.schemas.blog import (
    ArticleCardOut, ArticleDetailOut, ArticleListResponse,
    ViewResponse, LikeResponse,
)

router = APIRouter()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _get_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = 1,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    limit = 9
    offset = (page - 1) * limit

    base_filter = [BlogArticle.status == "published"]
    if category and category != "all":
        base_filter.append(BlogArticle.category == category)

    total_q = select(func.count()).select_from(BlogArticle).where(*base_filter)
    total = (await db.execute(total_q)).scalar_one()

    items_q = (
        select(BlogArticle)
        .where(*base_filter)
        .order_by(BlogArticle.published_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    items = (await db.execute(items_q)).scalars().all()

    return ArticleListResponse(
        items=list(items),
        total=total,
        page=page,
        pages=max(1, (total + limit - 1) // limit),
    )


@router.get("/articles/{slug}", response_model=ArticleDetailOut)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(BlogArticle).where(
            BlogArticle.slug == slug,
            BlogArticle.status == "published",
        )
    )
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404, detail="Article not found")
    return article


@router.post("/articles/{article_id}/view", response_model=ViewResponse)
async def register_view(article_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(BlogArticle).where(
            BlogArticle.id == article_id,
            BlogArticle.status == "published",
        )
    )
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404)

    ip_hash = _hash(_get_ip(request))
    ua_hash = _hash(request.headers.get("User-Agent", ""))
    today = date.today()

    existing = await db.execute(
        select(BlogView).where(
            BlogView.article_id == article_id,
            BlogView.ip_hash == ip_hash,
            func.date(BlogView.viewed_at) == today,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(BlogView(article_id=article_id, ip_hash=ip_hash, user_agent_hash=ua_hash))
        article.view_count += 1
        await db.commit()
        await db.refresh(article)

    return ViewResponse(view_count=article.view_count)


@router.post("/articles/{article_id}/like", response_model=LikeResponse)
async def toggle_like(
    article_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(BlogArticle).where(
            BlogArticle.id == article_id,
            BlogArticle.status == "published",
        )
    )
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404)

    ip_hash = _hash(_get_ip(request))
    cookie_key = f"liked_{article_id}"

    existing = await db.execute(
        select(BlogLike).where(
            BlogLike.article_id == article_id,
            BlogLike.ip_hash == ip_hash,
        )
    )
    like_row = existing.scalar_one_or_none()

    if like_row:
        await db.delete(like_row)
        article.like_count = max(0, article.like_count - 1)
        await db.commit()
        await db.refresh(article)
        response.delete_cookie(cookie_key)
        return LikeResponse(like_count=article.like_count, liked=False)
    else:
        db.add(BlogLike(
            article_id=article_id,
            ip_hash=ip_hash,
            cookie_id=request.cookies.get(cookie_key),
        ))
        article.like_count += 1
        await db.commit()
        await db.refresh(article)
        response.set_cookie(cookie_key, "1", max_age=60 * 60 * 24 * 365 * 2, samesite="lax")
        return LikeResponse(like_count=article.like_count, liked=True)

"""
/admin/blog — CRUD статей блога + загрузка медиа.
Требует роль admin (require_admin dependency).
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.blog import BlogArticle
from app.models.user import User
from app.schemas.blog import (
    ArticleDetailOut, ArticleCreateRequest, ArticleUpdateRequest, MediaUploadResponse,
)
from app.utils.deps import require_admin

router = APIRouter()

UPLOAD_DIR = Path("/tmp/blog_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.get("/articles", response_model=list[ArticleDetailOut])
async def admin_list_articles(
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = select(BlogArticle).order_by(BlogArticle.created_at.desc())
    if status:
        q = q.where(BlogArticle.status == status)
    if category:
        q = q.where(BlogArticle.category == category)
    r = await db.execute(q)
    return r.scalars().all()


@router.get("/articles/{article_id}", response_model=ArticleDetailOut)
async def admin_get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    r = await db.execute(select(BlogArticle).where(BlogArticle.id == article_id))
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404, detail="Article not found")
    return article


@router.post("/articles", response_model=ArticleDetailOut, status_code=201)
async def admin_create_article(
    payload: ArticleCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = payload.model_dump()
    if data["status"] == "published" and not data.get("published_at"):
        data["published_at"] = datetime.now(timezone.utc)
    article = BlogArticle(**data)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


@router.put("/articles/{article_id}", response_model=ArticleDetailOut)
async def admin_update_article(
    article_id: int,
    payload: ArticleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    r = await db.execute(select(BlogArticle).where(BlogArticle.id == article_id))
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404, detail="Article not found")

    update_data = payload.model_dump(exclude_none=True)
    if update_data.get("status") == "published" and not article.published_at:
        update_data["published_at"] = datetime.now(timezone.utc)
    for key, value in update_data.items():
        setattr(article, key, value)
    article.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(article)
    return article


@router.delete("/articles/{article_id}", status_code=204)
async def admin_delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    r = await db.execute(select(BlogArticle).where(BlogArticle.id == article_id))
    article = r.scalar_one_or_none()
    if not article:
        raise HTTPException(404, detail="Article not found")
    await db.delete(article)
    await db.commit()


@router.post("/media/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="File too large (max 5 MB)")
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, detail="Only JPEG, PNG, WebP, GIF allowed")

    ext = (file.filename or "image.jpg").rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    (UPLOAD_DIR / filename).write_bytes(content)
    return MediaUploadResponse(url=f"/uploads/blog/{filename}")

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class ArticleCardOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    category: str
    tags: list[str] = []
    author: str
    published_at: Optional[datetime] = None
    view_count: int = 0
    like_count: int = 0


class ArticleDetailOut(ArticleCardOut):
    content: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: str = "draft"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ArticleListResponse(BaseModel):
    items: list[ArticleCardOut]
    total: int
    page: int
    pages: int


class ArticleCreateRequest(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    category: str = "general"
    tags: list[str] = []
    author: str = "Команда Attribly"
    published_at: Optional[datetime] = None
    status: str = "draft"
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    status: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ViewResponse(BaseModel):
    view_count: int


class LikeResponse(BaseModel):
    like_count: int
    liked: bool


class MediaUploadResponse(BaseModel):
    url: str

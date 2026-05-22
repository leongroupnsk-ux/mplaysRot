import math
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "Paginated[T]":
        pages = math.ceil(total / page_size) if page_size else 1
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)

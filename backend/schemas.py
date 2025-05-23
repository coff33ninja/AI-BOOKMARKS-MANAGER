from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True


class BookmarkBase(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    position: Optional[float] = 0.0


class BookmarkCreate(BookmarkBase):
    tags: Optional[List[str]] = None


class BookmarkUpdate(BookmarkBase):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    position: Optional[float] = None


class BookmarkResponse(BookmarkBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class BookmarkReorder(BaseModel):
    bookmark_id: int
    new_position: float
    category: Optional[str] = None


class AISuggestionRequest(BaseModel):
    url: HttpUrl


class TitleSuggestionResponse(BaseModel):
    suggested_title: Optional[str] = None
    error: Optional[str] = None


class TagsSuggestionResponse(BaseModel):
    suggested_tags: List[str] = []
    suggested_category: Optional[str] = None
    error: Optional[str] = None


class AnalyticsResponse(BaseModel):
    category_counts: dict
    tag_counts: dict
    recent_actions: List[dict]

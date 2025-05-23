from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Table,
    Computed,
    Float,
)
from sqlalchemy.sql import func
from .database import Base

# Junction table for bookmarks and tags
bookmark_tags = Table(
    "bookmark_tags",
    Base.metadata,
    Column("bookmark_id", Integer, ForeignKey("bookmarks.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    schema="public",
)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False, unique=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    position = Column(Float, nullable=False, default=0.0)  # For drag-and-drop ordering
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    search_vector = Column(
        Text,
        Computed(
            "to_tsvector('english', title || ' ' || url || ' ' || description || ' ' || coalesce(category, ''))",
            persisted=True,
        ),
    )
    tags = relationship("Tag", secondary=bookmark_tags, back_populates="bookmarks")
    interactions = relationship("BookmarkInteraction", back_populates="bookmark")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    bookmarks = relationship("Bookmark", secondary=bookmark_tags, back_populates="tags")


class BookmarkInteraction(Base):
    __tablename__ = "bookmark_interactions"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, index=True)
    bookmark_id = Column(Integer, ForeignKey("bookmarks.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "view", "edit"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    bookmark = relationship("Bookmark", back_populates="interactions")

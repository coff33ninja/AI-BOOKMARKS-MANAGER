from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from . import models, schemas


def get_bookmark(db: Session, bookmark_id: int):
    """Retrieve a bookmark by ID."""
    return db.query(models.Bookmark).filter(models.Bookmark.id == bookmark_id).first()


def get_bookmarks(db: Session, skip: int = 0, limit: int = 100, category: str = None):
    """Retrieve a list of bookmarks, optionally filtered by category, ordered by position."""
    query = db.query(models.Bookmark)
    if category:
        query = query.filter(models.Bookmark.category == category)
    return (
        query.order_by(
            models.Bookmark.position.asc(), models.Bookmark.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_tag_by_name(db: Session, tag_name: str):
    """Retrieve or create a tag by name."""
    tag_name = tag_name.lower().strip()
    tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
    if not tag:
        tag = models.Tag(name=tag_name)
        db.add(tag)
        db.commit()
        db.refresh(tag)
    return tag


def create_bookmark(db: Session, bookmark: schemas.BookmarkCreate):
    """Create a new bookmark with tags and category."""
    try:
        # Set position as max(position) + 1 within category
        max_position = (
            db.query(func.max(models.Bookmark.position))
            .filter(models.Bookmark.category == bookmark.category)
            .scalar()
            or 0
        )
        db_bookmark = models.Bookmark(
            url=str(bookmark.url),
            title=bookmark.title or "Untitled Bookmark",
            description=bookmark.description,
            category=bookmark.category,
            position=max_position + 1,
        )
        if bookmark.tags:
            db_bookmark.tags = [get_tag_by_name(db, tag) for tag in bookmark.tags]
        db.add(db_bookmark)
        db.commit()
        db.refresh(db_bookmark)
        return db_bookmark
    except IntegrityError:
        db.rollback()
        return None


def update_bookmark(
    db: Session, bookmark_id: int, bookmark_update: schemas.BookmarkUpdate
):
    """Update a bookmark, including tags, category, and position."""
    db_bookmark = get_bookmark(db, bookmark_id)
    if not db_bookmark:
        return None
    try:
        update_data = bookmark_update.dict(exclude_unset=True)
        if "tags" in update_data:
            db_bookmark.tags = [
                get_tag_by_name(db, tag) for tag in update_data.pop("tags") or []
            ]
        for key, value in update_data.items():
            setattr(db_bookmark, key, value)
        db.commit()
        db.refresh(db_bookmark)
        return db_bookmark
    except IntegrityError:
        db.rollback()
        return None


def delete_bookmark(db: Session, bookmark_id: int):
    """Delete a bookmark by ID."""
    db_bookmark = get_bookmark(db, bookmark_id)
    if db_bookmark:
        db.delete(db_bookmark)
        db.commit()
        return True
    return False


def reorder_bookmark(db: Session, reorder: schemas.BookmarkReorder):
    """Update bookmark position and category."""
    db_bookmark = get_bookmark(db, reorder.bookmark_id)
    if not db_bookmark:
        return None
    try:
        db_bookmark.position = reorder.new_position
        if reorder.category:
            db_bookmark.category = reorder.category
        db.commit()
        db.refresh(db_bookmark)
        return db_bookmark
    except IntegrityError:
        db.rollback()
        return None


def search_bookmarks(db: Session, query: str, limit: int = 100):
    """Search bookmarks using PostgreSQL full-text search."""
    if not query:
        return get_bookmarks(db, limit=limit)
    tag_subquery = (
        db.query(models.Tag.name).filter(models.Tag.name.ilike(f"%{query}%")).subquery()
    )
    return (
        db.query(models.Bookmark)
        .filter(
            (models.Bookmark.search_vector.op("@@")(func.to_tsquery("english", query)))
            | (
                models.Bookmark.id.in_(
                    db.query(models.bookmark_tags.c.bookmark_id).join(
                        tag_subquery,
                        models.bookmark_tags.c.tag_id
                        == db.query(models.Tag.id).filter(
                            models.Tag.name == tag_subquery.c.name
                        ),
                    )
                )
            )
        )
        .order_by(
            func.ts_rank(
                models.Bookmark.search_vector, func.to_tsquery("english", query)
            ).desc()
        )
        .limit(limit)
        .all()
    )


def get_categories(db: Session):
    """Retrieve distinct categories."""
    return [
        row[0]
        for row in db.query(models.Bookmark.category)
        .distinct()
        .filter(models.Bookmark.category != None)
        .all()
    ]


def log_interaction(db: Session, bookmark_id: int, action: str):
    """Log a user interaction with a bookmark."""
    interaction = models.BookmarkInteraction(bookmark_id=bookmark_id, action=action)
    db.add(interaction)
    db.commit()


def get_analytics(db: Session):
    """Retrieve analytics data."""
    # Category counts
    category_counts = (
        db.query(models.Bookmark.category, func.count(models.Bookmark.id))
        .group_by(models.Bookmark.category)
        .all()
    )
    category_counts = {cat or "Uncategorized": count for cat, count in category_counts}

    # Tag counts
    tag_counts = (
        db.query(models.Tag.name, func.count(models.bookmark_tags.c.bookmark_id))
        .join(models.bookmark_tags)
        .group_by(models.Tag.name)
        .all()
    )
    tag_counts = {name: count for name, count in tag_counts}

    # Recent actions
    recent_actions = (
        db.query(models.BookmarkInteraction)
        .join(models.Bookmark)
        .order_by(models.BookmarkInteraction.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_actions = [
        {
            "bookmark_id": action.bookmark_id,
            "title": action.bookmark.title,
            "action": action.action,
            "timestamp": action.timestamp.isoformat(),
        }
        for action in recent_actions
    ]

    return schemas.AnalyticsResponse(
        category_counts=category_counts,
        tag_counts=tag_counts,
        recent_actions=recent_actions,
    )

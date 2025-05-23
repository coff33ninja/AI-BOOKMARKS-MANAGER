from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from . import crud, schemas, ai_utils, ws_manager
from .database import SessionLocal, engine, get_db

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Bookmark Manager")

# Serve React frontend
app.mount("/static", StaticFiles(directory="../frontend/dist"), name="static")

# WebSocket manager
ws_manager = ws_manager.ConnectionManager()


# --- WebSocket Route ---
@app.websocket("/ws/bookmarks")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time bookmark updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        ws_manager.disconnect(websocket)


# --- API Routes ---
@app.post("/bookmarks/", response_model=schemas.BookmarkResponse)
async def create_bookmark(
    bookmark: schemas.BookmarkCreate, db: Session = Depends(get_db)
):
    """Create a new bookmark and broadcast update."""
    if not bookmark.title:
        bookmark.title = (
            ai_utils.extract_title_from_url(str(bookmark.url)) or "Untitled Bookmark"
        )
    if not bookmark.category:
        _, bookmark.category = ai_utils.suggest_tags_from_url(str(bookmark.url))
    created_bookmark = crud.create_bookmark(db, bookmark)
    if not created_bookmark:
        raise HTTPException(
            status_code=400, detail="Bookmark with this URL already exists"
        )
    crud.log_interaction(db, created_bookmark.id, "create")
    await ws_manager.broadcast(
        {
            "action": "create",
            "bookmark": schemas.BookmarkResponse.from_orm(created_bookmark).dict(),
        }
    )
    return created_bookmark


@app.get("/bookmarks/", response_model=List[schemas.BookmarkResponse])
async def read_bookmarks(
    skip: int = 0, limit: int = 100, category: str = None, db: Session = Depends(get_db)
):
    """Retrieve a list of bookmarks, optionally filtered by category."""
    bookmarks = crud.get_bookmarks(db, skip=skip, limit=limit, category=category)
    for bookmark in bookmarks:
        crud.log_interaction(db, bookmark.id, "view")
    return bookmarks


@app.get("/bookmarks/{bookmark_id}", response_model=schemas.BookmarkResponse)
async def read_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    """Retrieve a single bookmark by ID."""
    bookmark = crud.get_bookmark(db, bookmark_id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    crud.log_interaction(db, bookmark_id, "view")
    return bookmark


@app.put("/bookmarks/{bookmark_id}", response_model=schemas.BookmarkResponse)
async def update_bookmark(
    bookmark_id: int, bookmark: schemas.BookmarkUpdate, db: Session = Depends(get_db)
):
    """Update a bookmark and broadcast update."""
    updated_bookmark = crud.update_bookmark(db, bookmark_id, bookmark)
    if not updated_bookmark:
        raise HTTPException(
            status_code=404, detail="Bookmark not found or update failed"
        )
    crud.log_interaction(db, bookmark_id, "edit")
    await ws_manager.broadcast(
        {
            "action": "update",
            "bookmark": schemas.BookmarkResponse.from_orm(updated_bookmark).dict(),
        }
    )
    return updated_bookmark


@app.post("/bookmarks/reorder/", response_model=schemas.BookmarkResponse)
async def reorder_bookmark(
    reorder: schemas.BookmarkReorder, db: Session = Depends(get_db)
):
    """Reorder a bookmark and broadcast update."""
    updated_bookmark = crud.reorder_bookmark(db, reorder)
    if not updated_bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    crud.log_interaction(db, reorder.bookmark_id, "reorder")
    await ws_manager.broadcast(
        {
            "action": "update",
            "bookmark": schemas.BookmarkResponse.from_orm(updated_bookmark).dict(),
        }
    )
    return updated_bookmark


@app.delete("/bookmarks/{bookmark_id}", status_code=204)
async def delete_bookmark(bookmark_id: int, db: Session = Depends(get_db)):
    """Delete a bookmark and broadcast update."""
    if not crud.delete_bookmark(db, bookmark_id):
        raise HTTPException(status_code=404, detail="Bookmark not found")
    crud.log_interaction(db, bookmark_id, "delete")
    await ws_manager.broadcast({"action": "delete", "bookmark_id": bookmark_id})
    return {"message": "Bookmark deleted successfully"}


@app.get("/bookmarks/search/", response_model=List[schemas.BookmarkResponse])
async def search_bookmarks(query: str, limit: int = 100, db: Session = Depends(get_db)):
    """Search bookmarks using full-text search."""
    bookmarks = crud.search_bookmarks(db, query, limit)
    for bookmark in bookmarks:
        crud.log_interaction(db, bookmark.id, "view")
    return bookmarks


@app.get("/categories/", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    """Retrieve distinct categories."""
    return crud.get_categories(db)


@app.get("/analytics/", response_model=schemas.AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Retrieve analytics data."""
    return crud.get_analytics(db)


@app.post("/ai/suggest-title", response_model=schemas.TitleSuggestionResponse)
async def suggest_title(payload: schemas.AISuggestionRequest):
    """Suggest a title based on the URL."""
    title = ai_utils.extract_title_from_url(str(payload.url))
    return schemas.TitleSuggestionResponse(
        suggested_title=title, error="Could not fetch title" if not title else None
    )


@app.post("/ai/suggest-tags", response_model=schemas.TagsSuggestionResponse)
async def suggest_tags(
    payload: schemas.AISuggestionRequest, db: Session = Depends(get_db)
):
    """Suggest tags and category using RoBERTa."""
    tags, category = ai_utils.suggest_tags_from_url(str(payload.url))
    return schemas.TagsSuggestionResponse(
        suggested_tags=tags,
        suggested_category=category,
        error="Could not fetch tags" if not tags else None,
    )

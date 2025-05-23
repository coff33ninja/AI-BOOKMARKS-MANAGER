from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite database (use PostgreSQL/MySQL for production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookmarks.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite-specific
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yields a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
Database Connection Management

SQLAlchemy engine and session management for J-GOD Taiwan stock database.
"""

import logging
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Default database path - use jgod_tw_stock.db for consistency with other backfill scripts
DEFAULT_DB_PATH = "data/jgod_tw_stock.db"
BASE_DIR = Path(__file__).parent.parent.parent

# Allow override via environment variable
DB_PATH = os.getenv("JGOD_DB_PATH", DEFAULT_DB_PATH)

# SQLite database URL
_db_path = BASE_DIR / DB_PATH
_db_url = f"sqlite:///{_db_path}"

# Create data directory if not exists
if not _db_path.parent.exists():
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created data directory: {_db_path.parent}")

_engine = None
_SessionLocal = None


def get_engine():
    """
    Get SQLAlchemy engine (singleton).
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        _engine = create_engine(
            _db_url,
            connect_args={"check_same_thread": False},  # SQLite specific
            echo=False,  # Set to True for SQL logging
        )
        logger.info(f"Database engine created: {_db_url}")
    return _engine


def get_session() -> Generator[Session, None, None]:
    """
    Get database session (context manager).
    
    Yields:
        Session: SQLAlchemy session
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """
    Initialize database schema (create all tables).
    
    This should be called once before using the database.
    """
    from jgod.storage.models import Base  # Avoid circular import
    
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {_db_path}")
    logger.info(f"Tables created: {list(Base.metadata.tables.keys())}")


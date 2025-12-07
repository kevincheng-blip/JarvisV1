"""
Storage layer for J-GOD.

This package exposes high-level helpers for:
- creating the simulation database
- getting an engine / session factory

NOTE:
- We intentionally DO NOT re-export `Base` here to avoid circular import issues.
- ORM models should import `Base` directly from `jgod.storage.db`.
"""

from jgod.storage.db import get_engine, get_session, init_db

__all__ = [
    "get_engine",
    "get_session",
    "init_db",
]

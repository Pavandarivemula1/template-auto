"""
database.py – SQLAlchemy engine, session, and base setup.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# PostgreSQL database URL (can be overridden by environment variable)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.ghpvicmyfsmvttgjfzac:R4hVCPlUBJ7RjDLL@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres")

engine = create_engine(
    DATABASE_URL,
    # Postgres doesn't need check_same_thread
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency – yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

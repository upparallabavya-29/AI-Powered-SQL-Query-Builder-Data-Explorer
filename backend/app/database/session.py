import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Retrieve the database URL, defaulting to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_builder.db")

# Connection parameters for different database systems
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific arguments to handle multiple threads in FastAPI
    connect_args = {"check_same_thread": False}
    
    # If using in-memory or static pool SQLite for test configurations
    if ":memory:" in DATABASE_URL:
        connect_args["poolclass"] = StaticPool

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # Automatically test connections on checkout
)

# Enforce foreign key constraints in SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Dependency generator for database sessions in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator:
    """Context manager for standalone database session operations outside of routes."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.app.config import settings

# Engine setup
connect_args = {}
db_url = settings.sync_database_url

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )
else:
    # Serverless-friendly connection pool configuration for PostgreSQL.
    # Small pool size prevents exhausting connection limits on external managed DBs (Neon, Supabase, RDS).
    # pool_pre_ping validates connection health before handing it to a query.
    engine = create_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,
        pool_timeout=30,
        connect_args=connect_args,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a thread-local transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("complianceos.database")

Base = declarative_base()


def create_db_engine():
    # Try primary database url (PostgreSQL)
    try:
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to primary database: %s", settings.DATABASE_URL.split("@")[-1])
        return engine
    except Exception as exc:
        logger.warning(
            "Could not connect to primary database (%s). Falling back to SQLite (%s). Error: %s",
            settings.DATABASE_URL,
            settings.SQLITE_FALLBACK_URL,
            exc,
        )
        return create_engine(
            settings.SQLITE_FALLBACK_URL,
            echo=False,
            connect_args={"check_same_thread": False},
        )


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import entities  # ensure models are registered
    Base.metadata.create_all(bind=engine)

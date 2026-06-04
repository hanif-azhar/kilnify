"""SQLAlchemy engine and session setup for Kilnify."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv optional in some environments
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kilnify.db")

# SQLite needs check_same_thread disabled for FastAPI's threaded request handling.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

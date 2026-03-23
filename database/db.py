from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

# ================================
# DATABASE ENGINE
# ================================

# SQLite needs special argument
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL, echo=False, connect_args=connect_args  # Set True for SQL debugging
)


# ================================
# SESSION CONFIGURATION
# ================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ================================
# BASE MODEL
# ================================

Base = declarative_base()


# ================================
# DATABASE DEPENDENCY (FastAPI)
# ================================


def get_db():
    """
    Dependency to get DB session
    Automatically closes after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

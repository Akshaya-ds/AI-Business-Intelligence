import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Determine DB URL: prefer PostgreSQL if env var DATABASE_URL is set, otherwise fallback to SQLite file in project root.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # SQLite fallback stored in <project_root>/backend/data/app.db
    project_root = Path(__file__).resolve().parents[3]
    sqlite_path = project_root / "data" / "app.db"
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite+pysqlite:///{sqlite_path}?check_same_thread=False"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

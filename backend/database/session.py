import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.settings import settings
from backend.database.schema import Base

# Support Vercel serverless environment (writable only in /tmp)
if os.environ.get("VERCEL"):
    db_url = "sqlite:////tmp/incident_platform.db"
else:
    db_url = settings.DATABASE_URL

if db_url.startswith("sqlite"):
    db_path = db_url.replace("sqlite:////", "/").replace("sqlite:///", "")
    try:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_db_initialized = False

def init_db():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    Base.metadata.create_all(bind=engine)
    if os.environ.get("VERCEL"):
        try:
            db = SessionLocal()
            from backend.database.repositories.incident_repo import IncidentRepository
            repo = IncidentRepository(db)
            if not repo.get_incident("INC-2026-PAY-882"):
                from scripts.seed_database import seed_demo_incident
                seed_demo_incident(skip_init=True)
            db.close()
        except Exception:
            pass

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

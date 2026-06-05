import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLite fallback path
if not DATABASE_URL or DATABASE_URL.strip() == "":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_path = os.path.join(BASE_DIR, "kalyx.db")
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    print(f"[Database] DATABASE_URL not set. Falling back to SQLite: {DATABASE_URL}")
else:
    print(f"[Database] Connecting to database: {DATABASE_URL.split('@')[-1]}")

# Configuration arguments for engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific multi-threading safety argument
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class
Base = declarative_base()

# Context manager for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

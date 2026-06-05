import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, courses, studio, export

# Create database tables automatically if they don't exist
try:
    print("[Startup] Initializing relational database schemas...")
    Base.metadata.create_all(bind=engine)
    
    # Safety DB migration: add username column if it doesn't exist on users table
    from app.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
        db.commit()
        print("[Startup] SQLite migration: Added username column to users table.")
    except Exception as err:
        # Ignore if column already exists
        print(f"[Startup] SQLite migration check: {err}")
        pass
    finally:
        db.close()
        
    print("[Startup] Database schemas synchronized successfully.")
    
    # Seed default developer course for instant hackathon evaluations
    from app.models import Course, User
    from app.routers.auth import hash_password
    
    db = SessionLocal()
    if db.query(User).count() == 0:
        print("[Startup] Seeding default demo educator profile...")
        default_user = User(
            email="professor.jones@stanford.edu",
            username="professor.jones",
            hashed_password=hash_password("hackathon_demo_pass"),
            full_name="Dr. Devashish Jones"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        print("[Startup] Seeding default Advanced Machine Learning course node...")
        default_course = Course(
            user_id=default_user.id,
            title="Advanced Machine Learning",
            description="An advanced machine learning class focusing on model architectures, regression models, classification boundaries, and support vector machines."
        )
        db.add(default_course)
        db.commit()
    db.close()
except Exception as e:
    print(f"[Startup] Database sync warning: {e}. Ensure server credentials are valid.")

app = FastAPI(
    title="KALYX — Agentic Curriculum Intelligence Platform API",
    description="Multi-agent educational sequencing, slide generation, Bloom's taxonomy auditing, and PPTX exporting.",
    version="1.0.0"
)

# Configure CORS Middleware
# Next.js defaults to localhost:3000. We allow full local cross-origin capabilities.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(studio.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "platform": "KALYX",
        "description": "Agentic Curriculum Intelligence Platform Backend",
        "status": "Online"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

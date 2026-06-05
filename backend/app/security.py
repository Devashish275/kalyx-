import os
import time
import jwt
from collections import defaultdict
from fastapi import Request, HTTPException, status

JWT_SECRET = os.getenv("JWT_SECRET", "hackathon_super_secret_key_kalyx_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class RateLimiter:
    def __init__(self):
        # Maps limit_key -> list of timestamps
        self.history = defaultdict(list)

    def check_rate_limit(self, key: str, limit: int, window: int = 60):
        now = time.time()
        # Clean up timestamps older than the window
        self.history[key] = [t for t in self.history[key] if now - t < window]
        if len(self.history[key]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too many requests. Please try again later.",
                    "detail": "Too many requests. Please try again later."
                }
            )
        self.history[key].append(now)

limiter = RateLimiter()

def get_user_identifier(request: Request) -> str:
    # 1. Try Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # 2. Try query parameter
    if not token:
        token = request.query_params.get("token")
        
    if not token:
        # Fallback to IP address if no token is provided
        return f"ip_{request.client.host if request.client else 'unknown'}"
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email:
            return f"user_{email}"
    except Exception:
        pass
        
    return f"ip_{request.client.host if request.client else 'unknown'}"

# Dependencies for rate limiting
def limit_login(request: Request):
    ip = request.client.host if request.client else "unknown"
    limiter.check_rate_limit(f"login_{ip}", 10, 60)

def limit_signup(request: Request):
    ip = request.client.host if request.client else "unknown"
    limiter.check_rate_limit(f"signup_{ip}", 5, 60)

def limit_course_creation(request: Request):
    key = get_user_identifier(request)
    limiter.check_rate_limit(f"course_create_{key}", 20, 60)

def limit_syllabus_upload(request: Request):
    key = get_user_identifier(request)
    limiter.check_rate_limit(f"syllabus_upload_{key}", 5, 60)

def limit_analysis_generation(request: Request):
    key = get_user_identifier(request)
    limiter.check_rate_limit(f"analysis_gen_{key}", 5, 60)

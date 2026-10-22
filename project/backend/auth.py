"""
Authentication & Authorization helpers for SmartMart AI.
Supports API key authentication, session bearer tokens, and canonical Gmail normalization.
Strictly guarantees one account per Gmail ID and isolates data between users.
"""

import os
import sys
import time
from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import User, get_db

API_KEY = os.environ.get("SMARTMART_API_KEY", "dev-key")


def normalize_email(email: Optional[str]) -> str:
    """
    Canonicalize email addresses to strictly enforce one account per Gmail ID.
    - Trims and lowercases.
    - For Gmail / Googlemail, removes dots and trailing aliases (e.g. 'john.doe+test@gmail.com' -> 'johndoe@gmail.com').
    """
    if not email:
        return ""
    clean = email.strip().lower()
    if "@" not in clean:
        return clean
    user_part, domain_part = clean.split("@", 1)
    if domain_part in ("gmail.com", "googlemail.com"):
        user_part = user_part.split("+")[0]  # Strip +extension
        user_part = user_part.replace(".", "")  # Gmail treats dotted and undotted as identical
        domain_part = "gmail.com"
    return f"{user_part}@{domain_part}"


async def require_api_key(x_api_key: str = Header(default=None, alias="X-API-Key")):
    """FastAPI dependency: require a valid API key header for protected routes."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Set X-API-Key header."
        )
    return x_api_key


class GuestUser:
    """Represents a temporary unauthenticated guest session isolated from registered users."""
    def __init__(self, guest_id: str):
        import re, json
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', str(guest_id))[:64]
        self.id = clean_id if clean_id.startswith("guest_") else f"guest_{clean_id}"
        self.email = f"{self.id}@guest.local"
        self.name = "Guest User"
        self.auth_provider = "guest"
        self.avatar_url = None
        self.is_guest = True
        self.state_data = json.dumps({"has_data": False})


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-ID"),
    db_dep: Optional[Session] = Depends(get_db),
):
    """
    Retrieve currently authenticated user from Bearer session token or Guest session.
    Returns GuestUser if guest token/header provided, or None if completely unauthenticated.
    """
    from database import SessionLocal, User, UserSession

    close_db = False
    db = db_dep
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        token = authorization
        clean_token = token.replace("Bearer ", "").strip() if token else None

        # 1. Handle explicit guest tokens (e.g. Bearer guest_...)
        if clean_token and clean_token.startswith("guest_"):
            return GuestUser(clean_token)

        # 2. Check authenticated registered user session
        if clean_token:
            now = time.time()
            session = db.query(UserSession).filter(
                UserSession.token == clean_token,
                UserSession.expires_at > now
            ).first()

            if session:
                user = db.query(User).filter(User.id == session.user_id).first()
                if user:
                    return user

        # 3. Check X-Guest-ID header for guest sessions
        if x_guest_id and str(x_guest_id).strip():
            return GuestUser(str(x_guest_id).strip())

        return None
    finally:
        if close_db:
            db.close()


def require_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db_dep: Optional[Session] = Depends(get_db),
):
    """
    FastAPI dependency: requires valid authenticated session.
    Raises HTTP 401 if not authenticated.
    """
    user = get_current_user(authorization=authorization, x_api_key=x_api_key, db_dep=db_dep)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to access your isolated store data."
        )
    return user

"""
Authentication API routes — Email/Password & Google Sign-In with User Session & State Persistence
"""

import hashlib
import json
import re
import uuid
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, SessionLocal, User, UserSession
from upload_store import (
    get_feature_flags as store_get_flags,
    set_feature_flags as store_set_flags,
)
from routes.upload import perform_load_demo, perform_reset_data

router = APIRouter(prefix="/api/auth", tags=["auth"])

SALT = "SMARTMART_AUTH_SALT_v3"
SESSION_DURATION_SECONDS = 30 * 24 * 60 * 60  # 30 days


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with custom salt."""
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


def derive_name_from_email(email: str) -> str:
    """Derive clean human-readable username from email address.
    e.g., 'riteesh800@gmail.com' -> 'Riteesh', 'john.doe@gmail.com' -> 'John Doe'
    """
    if not email or "@" not in email:
        return "User"
    prefix = email.split("@")[0].strip()
    # Replace dots, underscores, dashes with spaces
    cleaned = re.sub(r"[._-]+", " ", prefix).strip()
    # Remove trailing digits if attached to word, or keep if separate
    cleaned = re.sub(r"(?<=[a-zA-Z])\d+", "", cleaned).strip()
    if not cleaned:
        cleaned = prefix
    return cleaned.title()


def create_user_session(db: Session, user_id: str) -> str:
    token = uuid.uuid4().hex + uuid.uuid4().hex
    now = time.time()
    session = UserSession(
        token=token,
        user_id=user_id,
        created_at=now,
        expires_at=now + SESSION_DURATION_SECONDS,
    )
    db.add(session)
    db.commit()
    return token


def get_user_from_token(token: Optional[str], db: Session) -> Optional[User]:
    if not token:
        return None
    clean_token = token.replace("Bearer ", "").strip()
    session = db.query(UserSession).filter(
        UserSession.token == clean_token,
        UserSession.expires_at > time.time()
    ).first()
    if not session:
        return None
    return db.query(User).filter(User.id == session.user_id).first()


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class SaveStateRequest(BaseModel):
    state_data: dict


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in.")

    name = req.name.strip() if req.name and req.name.strip() else derive_name_from_email(email)
    user_id = str(uuid.uuid4())
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Initial state for new user: start fresh with no data until demo data is loaded
    initial_state = {
        "has_data": False,
        "active_panel": "home",
        "registered_at": now_str,
    }

    user = User(
        id=user_id,
        email=email,
        name=name,
        auth_provider="email",
        password_hash=hash_password(req.password),
        avatar_url=None,
        created_at=now_str,
        last_login_at=now_str,
        state_data=json.dumps(initial_state),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_session(db, user.id)

    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "auth_provider": user.auth_provider,
            "avatar_url": user.avatar_url,
            "state_data": initial_state,
        }
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if user.auth_provider == "google" and not user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account was registered using Google Sign-In. Please sign in with Google."
        )

    if user.password_hash != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user.last_login_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    db.commit()

    token = create_user_session(db, user.id)

    # Restore user's previous data state
    user_state = {}
    try:
        user_state = json.loads(user.state_data or "{}")
    except Exception:
        user_state = {}

    # If the user previously had data loaded, restore it
    if user_state.get("has_data"):
        try:
            # Check if database has rows; if not, restore demo data
            count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
            if not count or count == 0:
                perform_load_demo()
            else:
                store_set_flags({
                    "has_data": True, "has_sales": True, "has_products": True,
                    "has_customers": True, "has_cost": True, "has_categories": True,
                    "has_timestamps": True, "has_payment": True, "has_basket": True,
                    "enable_dashboard": True, "enable_inventory": True, "enable_sales": True,
                    "enable_customers": True, "enable_suppliers": True, "enable_forecast": True,
                    "enable_recommendations": True, "enable_pricing": True, "enable_heatmap": True,
                    "enable_anomalies": True, "enable_profit": True, "enable_demographics": True,
                    "enable_retention": True,
                })
        except Exception:
            pass
    else:
        # User left account with empty data
        try:
            perform_reset_data()
        except Exception:
            store_set_flags({"has_data": False})

    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "auth_provider": user.auth_provider,
            "avatar_url": user.avatar_url,
            "state_data": user_state,
        }
    }


@router.post("/google")
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid Google email address.")

    derived_name = req.name.strip() if req.name and req.name.strip() else derive_name_from_email(email)
    user = db.query(User).filter(User.email == email).first()

    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if not user:
        # Create new Google user
        user_id = str(uuid.uuid4())
        initial_state = {
            "has_data": False,
            "active_panel": "home",
            "registered_at": now_str,
        }
        user = User(
            id=user_id,
            email=email,
            name=derived_name,
            auth_provider="google",
            password_hash=None,
            avatar_url=req.avatar_url,
            created_at=now_str,
            last_login_at=now_str,
            state_data=json.dumps(initial_state),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_state = initial_state
    else:
        # Existing Google user: update last login and avatar
        user.last_login_at = now_str
        if req.avatar_url:
            user.avatar_url = req.avatar_url
        if req.name and req.name.strip():
            user.name = req.name.strip()
        db.commit()
        try:
            user_state = json.loads(user.state_data or "{}")
        except Exception:
            user_state = {}

    token = create_user_session(db, user.id)

    # Restore data state according to how user left it
    if user_state.get("has_data"):
        try:
            count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
            if not count or count == 0:
                perform_load_demo()
            else:
                store_set_flags({
                    "has_data": True, "has_sales": True, "has_products": True,
                    "has_customers": True, "has_cost": True, "has_categories": True,
                    "has_timestamps": True, "has_payment": True, "has_basket": True,
                    "enable_dashboard": True, "enable_inventory": True, "enable_sales": True,
                    "enable_customers": True, "enable_suppliers": True, "enable_forecast": True,
                    "enable_recommendations": True, "enable_pricing": True, "enable_heatmap": True,
                    "enable_anomalies": True, "enable_profit": True, "enable_demographics": True,
                    "enable_retention": True,
                })
        except Exception:
            pass
    else:
        try:
            perform_reset_data()
        except Exception:
            store_set_flags({"has_data": False})

    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "auth_provider": user.auth_provider,
            "avatar_url": user.avatar_url,
            "state_data": user_state,
        }
    }


@router.get("/me")
def get_me(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in.")

    user_state = {}
    try:
        user_state = json.loads(user.state_data or "{}")
    except Exception:
        user_state = {}

    return {
        "status": "success",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "auth_provider": user.auth_provider,
            "avatar_url": user.avatar_url,
            "state_data": user_state,
        }
    }


@router.post("/save-state")
def save_user_state(
    req: SaveStateRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    try:
        current_state = json.loads(user.state_data or "{}")
    except Exception:
        current_state = {}

    current_state.update(req.state_data)
    current_state["last_saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    user.state_data = json.dumps(current_state)
    db.commit()

    return {"status": "success", "state_data": current_state}


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization:
        clean_token = authorization.replace("Bearer ", "").strip()
        db.query(UserSession).filter(UserSession.token == clean_token).delete()
        db.commit()

    # Reset data to empty guest state
    try:
        perform_reset_data()
    except Exception:
        store_set_flags({"has_data": False})
    return {"status": "success", "message": "Logged out successfully"}

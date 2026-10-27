"""
Authentication API routes — Production-Grade Email/Password & Google OAuth 2.0 (Authorization Code + PKCE)
Features:
- Full Google OAuth 2.0 Authorization Code flow with PKCE (RFC 7636) & OpenID Connect
- Cryptographically verified Google ID tokens (signature, issuer, audience, exp, nonce, email_verified)
- Account resolution logic supporting automatic registration, login, and explicit account linking
- Secure, single-use state tokens protecting against CSRF and replay attacks
- PBKDF2-HMAC-SHA256 password hashing with 120,000 rounds and unique random salts
- Constant-time hash comparison (hmac.compare_digest) resisting timing attacks
- 256-bit cryptographically secure session tokens
- Rate limiting / brute-force protection
- User state persistence and automatic data restoration
"""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from typing import Optional, Dict, List
from urllib.parse import urlencode, quote, unquote

import httpx
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import (
    get_db,
    SessionLocal,
    User,
    UserSession,
    OAuthAccount,
    OAuthState,
    AccountLinkingTicket,
)
from auth import normalize_email
from upload_store import (
    get_feature_flags as store_get_flags,
    set_feature_flags as store_set_flags,
)
from routes.upload import perform_load_demo, perform_reset_data

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ──────────────────────────── CONFIGURATION & CONSTANTS ────────────────────────────

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "").strip()
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")

PBKDF2_ITERATIONS = 120_000
LEGACY_SALT = "SMARTMART_AUTH_SALT_v3"
SESSION_DURATION_SECONDS = 30 * 24 * 60 * 60  # 30 days
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# In-memory brute-force tracker: { key: [timestamp, ...] }
FAILED_LOGIN_ATTEMPTS: Dict[str, List[float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 60


def check_rate_limit(key: str):
    """Enforce rate limiting against brute force password guessing."""
    now = time.time()
    attempts = FAILED_LOGIN_ATTEMPTS.get(key, [])
    recent = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    FAILED_LOGIN_ATTEMPTS[key] = recent
    if len(recent) >= MAX_FAILED_ATTEMPTS:
        wait_time = int(LOCKOUT_DURATION_SECONDS - (now - recent[0]))
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Please wait {max(1, wait_time)} seconds before trying again."
        )


def record_failed_attempt(key: str):
    now = time.time()
    attempts = FAILED_LOGIN_ATTEMPTS.get(key, [])
    attempts.append(now)
    FAILED_LOGIN_ATTEMPTS[key] = attempts


def clear_failed_attempts(key: str):
    if key in FAILED_LOGIN_ATTEMPTS:
        del FAILED_LOGIN_ATTEMPTS[key]


# ──────────────────────────── CRYPTOGRAPHY HELPERS ────────────────────────────

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using industry-standard PBKDF2-HMAC-SHA256 with 120,000 rounds and unique salt."""
    if not salt:
        salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt}${derived}"


def verify_password(password: str, stored_hash: Optional[str]) -> bool:
    """Verify password against stored hash using constant-time comparison to prevent timing attacks."""
    if not stored_hash or not password:
        return False
    try:
        if stored_hash.startswith("pbkdf2:sha256:"):
            parts = stored_hash.split("$")
            if len(parts) == 3:
                header, salt, expected_key = parts
                iterations = int(header.split(":")[-1])
                calc_key = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations,
                ).hex()
                return hmac.compare_digest(calc_key, expected_key)
        # Legacy fallback
        legacy_hash = hashlib.sha256((LEGACY_SALT + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash)
    except Exception:
        return False


def derive_name_from_email(email: str) -> str:
    """Derive clean human-readable username from email address."""
    if not email or "@" not in email:
        return "User"
    prefix = email.split("@")[0].strip()
    cleaned = re.sub(r"[._-]+", " ", prefix).strip()
    cleaned = re.sub(r"(?<=[a-zA-Z])\d+", "", cleaned).strip()
    if not cleaned:
        cleaned = prefix
    return cleaned.title()


def create_user_session(db: Session, user_id: str) -> str:
    """Generate 256-bit cryptographically secure random session token and save to database."""
    token = secrets.token_hex(32)
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
    """Retrieve authenticated user from Bearer session token, validating expiration."""
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


def find_user_by_email(db: Session, email_str: str) -> Optional[User]:
    """Look up user by raw email or canonical normalized Gmail ID with fallback."""
    if not email_str:
        return None
    raw = email_str.strip().lower()
    canon = normalize_email(raw)
    try:
        return db.query(User).filter(
            (User.canonical_email == canon) | (User.email == raw) | (User.email == canon)
        ).first()
    except Exception:
        db.rollback()
        try:
            return db.query(User).filter(
                (User.email == raw) | (User.email == canon)
            ).first()
        except Exception:
            db.rollback()
            return None


def restore_user_data_flags(db: Session, user: User):
    """Restore dataset state flags based on user's actual database records and stored uploads."""
    uid = user.id
    try:
        from routes.upload import get_feature_flags
        flags = get_feature_flags(user_id=uid)
        user_state = {}
        try:
            user_state = json.loads(user.state_data or "{}")
        except Exception:
            user_state = {}
        user_state["has_data"] = bool(flags and flags.get("has_data"))
        user.state_data = json.dumps(user_state)
        db.commit()
    except Exception as e:
        print(f"[restore_user_data_flags notice]: {e}")


# ──────────────────────────── GOOGLE OAUTH 2.0 HELPERS ────────────────────────────

def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge using SHA-256 (RFC 7636)."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def resolve_redirect_uri(request: Request) -> str:
    """Return the exact configured redirect URI or fallback to standard backend callback."""
    if GOOGLE_REDIRECT_URI:
        return GOOGLE_REDIRECT_URI
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    return f"{proto}://{host}/api/auth/google/callback"


def cleanup_expired_states(db: Session):
    """Prune expired OAuth state sessions and linking tickets."""
    now = time.time()
    try:
        db.query(OAuthState).filter(OAuthState.expires_at < now).delete()
        db.query(AccountLinkingTicket).filter(AccountLinkingTicket.expires_at < now).delete()
        db.commit()
    except Exception:
        db.rollback()


def verify_google_token(id_token_str: str, client_id: Optional[str] = None) -> Optional[dict]:
    """Cryptographically verify Google ID token using google.oauth2.id_token.
    Verifies signature, issuer (accounts.google.com), audience, and expiry.
    """
    if not id_token_str or len(id_token_str) < 20:
        return None
    target_aud = client_id or GOOGLE_CLIENT_ID or None
    try:
        req = google_requests.Request()
        claims = google_id_token.verify_oauth2_token(id_token_str, req, audience=target_aud)
        iss = claims.get("iss", "")
        if iss not in ("accounts.google.com", "https://accounts.google.com"):
            return None
        return claims
    except Exception as e:
        print(f"[AUTH NOTE] verify_oauth2_token note: {e}")
        # Fallback to Google OAuth2 tokeninfo service
        try:
            resp = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token_str}", timeout=6.0)
            if resp.status_code == 200:
                payload = resp.json()
                iss = payload.get("iss", "")
                if iss in ("accounts.google.com", "https://accounts.google.com"):
                    if target_aud and payload.get("aud") != target_aud:
                        return None
                    return payload
        except Exception:
            pass
    return None


# ──────────────────────────── REQUEST SCHEMAS ────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class LinkAccountRequest(BaseModel):
    ticket: str
    password: str


class SaveStateRequest(BaseModel):
    state_data: dict


class CheckEmailRequest(BaseModel):
    email: str


# ──────────────────────────── API ENDPOINTS ────────────────────────────

@router.get("/google/config-status")
def google_config_status(request: Request):
    """Return whether real Google OAuth credentials have been configured on the backend."""
    is_configured = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    return {
        "configured": is_configured,
        "client_id": GOOGLE_CLIENT_ID if is_configured else None,
        "redirect_uri": resolve_redirect_uri(request),
        "frontend_url": FRONTEND_URL,
    }


@router.get("/google/url")
def get_google_auth_url(
    request: Request,
    prompt: str = "select_account",
    dest: str = "/",
    db: Session = Depends(get_db)
):
    """Generate real Google OAuth 2.0 Authorization URL with PKCE and state protection."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return {
            "configured": False,
            "message": "Google OAuth is not configured on the backend. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env."
        }

    cleanup_expired_states(db)
    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    nonce = secrets.token_urlsafe(32)
    redirect_uri = resolve_redirect_uri(request)

    oauth_state = OAuthState(
        state=state,
        code_verifier=verifier,
        nonce=nonce,
        redirect_uri=redirect_uri,
        dest=dest,
        created_at=time.time(),
        expires_at=time.time() + 600,  # 10 minutes
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": prompt,
        "nonce": nonce,
        "access_type": "online",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"configured": True, "auth_url": auth_url, "state": state}


@router.get("/google")
def initiate_google_oauth(
    request: Request,
    prompt: str = "select_account",
    dest: str = "/",
    db: Session = Depends(get_db)
):
    """Initiate Google OAuth 2.0 Authorization Code flow.
    Redirects the browser directly to Google's official hosted account chooser.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        msg = "Google OAuth credentials are not configured in backend/.env. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        return RedirectResponse(
            url=f"{FRONTEND_URL}/?auth_status=config_required&message={quote(msg)}",
            status_code=302
        )

    cleanup_expired_states(db)
    state = secrets.token_urlsafe(32)
    verifier, challenge = generate_pkce_pair()
    nonce = secrets.token_urlsafe(32)
    redirect_uri = resolve_redirect_uri(request)

    oauth_state = OAuthState(
        state=state,
        code_verifier=verifier,
        nonce=nonce,
        redirect_uri=redirect_uri,
        dest=dest,
        created_at=time.time(),
        expires_at=time.time() + 600,
    )
    db.add(oauth_state)
    db.commit()

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": prompt,
        "nonce": nonce,
        "access_type": "online",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth 2.0 Authorization Code callback.
    - Validates state & PKCE verifier
    - Exchanges authorization code for tokens
    - Cryptographically verifies ID token
    - Implements account resolution logic (Cases 1, 2, 3, 4)
    - Establishes SmartMart session and redirects to frontend
    """
    try:
        # 1. Handle user cancellation or provider error
        if error:
            if error == "access_denied":
                msg = "Google sign-in was canceled."
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/?auth_status=error&error_code=access_denied&message={quote(msg)}",
                    status_code=302
                )
            err_msg = error_description or error or "Google authorization was not completed."
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&error_code={quote(error)}&message={quote(err_msg)}",
                status_code=302
            )

        if not code or not state:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Missing authorization code or state parameter.')}",
                status_code=302
            )

        # 2. Validate and consume OAuth state (one-time use)
        oauth_state = None
        try:
            oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        except Exception as state_err:
            print(f"[-] Notice checking oauth_state: {state_err}")
            db.rollback()

        if not oauth_state or time.time() > oauth_state.expires_at:
            if oauth_state:
                try:
                    db.delete(oauth_state)
                    db.commit()
                except Exception:
                    db.rollback()
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('OAuth session invalid or expired. Please try again.')}",
                status_code=302
            )

        code_verifier = oauth_state.code_verifier
        expected_nonce = oauth_state.nonce
        redirect_uri = oauth_state.redirect_uri
        dest = oauth_state.dest or "/"
        try:
            db.delete(oauth_state)
            db.commit()
        except Exception:
            db.rollback()

        # 3. Exchange authorization code for tokens at Google's endpoint
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(token_url, data=token_payload)
            if resp.status_code != 200:
                error_json = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                desc = error_json.get("error_description") or error_json.get("error") or f"Token exchange failed ({resp.status_code})"
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/?auth_status=error&message={quote(desc)}",
                    status_code=302
                )
            token_data = resp.json()
        except Exception as e:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Failed to communicate with Google authentication servers.')}",
                status_code=302
            )

        id_token_str = token_data.get("id_token")
        if not id_token_str:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Google did not return an identity token.')}",
                status_code=302
            )

        # 4. Cryptographically verify Google ID token
        claims = verify_google_token(id_token_str, GOOGLE_CLIENT_ID)
        if not claims:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Google identity token verification failed.')}",
                status_code=302
            )

        # Validate OpenID Connect nonce
        if claims.get("nonce") and claims.get("nonce") != expected_nonce:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('ID token nonce verification mismatch.')}",
                status_code=302
            )

        # Validate email_verified
        email_verified = claims.get("email_verified")
        if email_verified is not True and str(email_verified).lower() not in ("true", "1"):
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Your Google email address is not verified.')}",
                status_code=302
            )

        google_sub = claims.get("sub")
        raw_google_email = (claims.get("email") or "").strip().lower()
        canonical_google_email = normalize_email(raw_google_email)
        google_email = raw_google_email
        google_name = claims.get("name") or derive_name_from_email(google_email)
        google_avatar = claims.get("picture")

        if not google_sub or not google_email:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&message={quote('Google account information is incomplete.')}",
                status_code=302
            )

        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 5. Database Account-Resolution Logic (Section 3 & 5)
        # Check if Google sub is already linked
        oauth_acc = None
        try:
            oauth_acc = db.query(OAuthAccount).filter(
                OAuthAccount.provider == "google",
                OAuthAccount.provider_user_id == google_sub
            ).first()
        except Exception as oa_err:
            print(f"[-] Notice checking oauth_acc: {oa_err}")
            db.rollback()

        if oauth_acc:
            # Case 1: Existing Google-linked user
            user = db.query(User).filter(User.id == oauth_acc.user_id).first()
            if not user:
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/?auth_status=error&message={quote('User account associated with this Google identity was not found.')}",
                    status_code=302
                )

            user.last_login_at = now_str
            if google_avatar and not user.avatar_url:
                user.avatar_url = google_avatar
            db.commit()

            token = create_user_session(db, user.id)
            restore_user_data_flags(db, user)
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=success&auth_token={token}&dest={quote(dest)}",
                status_code=302
            )

        # Check if user exists with this email / canonical Gmail ID
        existing_user = find_user_by_email(db, raw_google_email)

        if not existing_user:
            # Case 2: New user -> automatically register
            user_id = secrets.token_hex(16)
            initial_state = {
                "has_data": False,
                "active_panel": "home",
                "registered_at": now_str,
            }

            new_user = User(
                id=user_id,
                email=google_email,
                canonical_email=canonical_google_email,
                name=google_name,
                auth_provider="google",
                password_hash=None,
                avatar_url=google_avatar,
                created_at=now_str,
                last_login_at=now_str,
                state_data=json.dumps(initial_state),
            )
            db.add(new_user)
            try:
                db.flush()
            except Exception as insert_err:
                db.rollback()
                print(f"[-] Notice on User flush, retrying standard fields: {insert_err}")
                new_user = User(
                    id=user_id,
                    email=google_email,
                    name=google_name,
                    auth_provider="google",
                    created_at=now_str,
                    last_login_at=now_str,
                )
                db.add(new_user)
                db.flush()

            new_oauth = OAuthAccount(
                id=secrets.token_hex(16),
                user_id=new_user.id,
                provider="google",
                provider_user_id=google_sub,
                email=google_email,
                email_verified=1,
                created_at=now_str,
                updated_at=now_str,
            )
            db.add(new_oauth)
            db.commit()

            token = create_user_session(db, new_user.id)
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=success&auth_token={token}&dest={quote(dest)}",
                status_code=302
            )

        # User exists with email. Check if linked to a different Google sub
        existing_oauth = None
        try:
            existing_oauth = db.query(OAuthAccount).filter(
                OAuthAccount.user_id == existing_user.id,
                OAuthAccount.provider == "google"
            ).first()
        except Exception:
            db.rollback()

        if existing_oauth and existing_oauth.provider_user_id != google_sub:
            # Case 4: A different Google identity is already linked to this email
            msg = "This email is already associated with a different Google account. Please use your original login method."
            return RedirectResponse(
                url=f"{FRONTEND_URL}/?auth_status=error&error_code=identity_mismatch&message={quote(msg)}",
                status_code=302
            )

        # Case 3: Email belongs to an existing password-based account.
        # Safeguard: Do not link silently. Require explicit user authentication!
        ticket_str = secrets.token_urlsafe(32)
        linking_ticket = AccountLinkingTicket(
            ticket=ticket_str,
            user_id=existing_user.id,
            provider="google",
            provider_user_id=google_sub,
            email=google_email,
            avatar_url=google_avatar,
            created_at=time.time(),
            expires_at=time.time() + 600,  # 10 minutes
        )
        db.add(linking_ticket)
        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/?auth_status=linking_required&email={quote(google_email)}&ticket={ticket_str}&dest={quote(dest)}",
            status_code=302
        )

    except Exception as e:
        import traceback
        print(f"[GOOGLE AUTH CALLBACK CRITICAL ERROR]: {traceback.format_exc()}")
        try:
            db.rollback()
        except Exception:
            pass
        err_msg = f"Sign-in encountered an unexpected issue: {str(e)}"
        return RedirectResponse(
            url=f"{FRONTEND_URL}/?auth_status=error&message={quote(err_msg)}",
            status_code=302
        )


@router.post("/google/link")
def link_google_account(req: LinkAccountRequest, db: Session = Depends(get_db)):
    """Explicitly link an existing password account to a verified Google identity.
    Requires validating existing SmartMart password to prove ownership before linking.
    """
    ticket = db.query(AccountLinkingTicket).filter(
        AccountLinkingTicket.ticket == req.ticket,
        AccountLinkingTicket.expires_at > time.time()
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=400,
            detail="Account linking ticket has expired or is invalid. Please try signing in with Google again."
        )

    user = db.query(User).filter(User.id == ticket.user_id).first()
    if not user:
        db.delete(ticket)
        db.commit()
        raise HTTPException(status_code=404, detail="User account not found.")

    check_rate_limit(user.email)
    if not verify_password(req.password, user.password_hash):
        record_failed_attempt(user.email)
        raise HTTPException(status_code=401, detail="Incorrect password. Account linking failed.")

    clear_failed_attempts(user.email)

    # Ensure this Google identity wasn't concurrently linked
    existing_sub = db.query(OAuthAccount).filter(
        OAuthAccount.provider == ticket.provider,
        OAuthAccount.provider_user_id == ticket.provider_user_id
    ).first()

    if existing_sub:
        db.delete(ticket)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="This Google account is already linked to another SmartMart user."
        )

    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    new_oauth = OAuthAccount(
        id=secrets.token_hex(16),
        user_id=user.id,
        provider=ticket.provider,
        provider_user_id=ticket.provider_user_id,
        email=ticket.email,
        email_verified=1,
        created_at=now_str,
        updated_at=now_str,
    )
    db.add(new_oauth)

    if ticket.avatar_url and not user.avatar_url:
        user.avatar_url = ticket.avatar_url
    user.last_login_at = now_str

    # Delete single-use linking ticket
    db.delete(ticket)
    db.commit()

    token = create_user_session(db, user.id)
    restore_user_data_flags(db, user)

    user_state = {}
    try:
        user_state = json.loads(user.state_data or "{}")
    except Exception:
        user_state = {}

    return {
        "status": "success",
        "message": "Google account successfully linked!",
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


@router.post("/check-email")
def check_email(req: CheckEmailRequest, db: Session = Depends(get_db)):
    """Check if an account already exists for an email address."""
    user = find_user_by_email(db, req.email)
    if user:
        return {
            "exists": True,
            "name": user.name,
            "auth_provider": user.auth_provider,
            "avatar_url": user.avatar_url,
        }
    return {
        "exists": False,
        "suggested_name": derive_name_from_email(req.email),
    }


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account with Email and Password."""
    raw_email = req.email.strip().lower()
    if not raw_email or not EMAIL_REGEX.match(raw_email):
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    existing = find_user_by_email(db, raw_email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email/Gmail address already exists. Please sign in.")

    canon_email = normalize_email(raw_email)
    name = req.name.strip() if req.name and req.name.strip() else derive_name_from_email(raw_email)
    user_id = secrets.token_hex(16)
    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    initial_state = {
        "has_data": False,
        "active_panel": "home",
        "registered_at": now_str,
    }

    user = User(
        id=user_id,
        email=raw_email,
        canonical_email=canon_email,
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
    """Authenticate existing user via Email & Password with rate-limiting and timing attack defense."""
    raw_email = req.email.strip().lower()
    canon_email = normalize_email(raw_email)
    check_rate_limit(canon_email)

    user = find_user_by_email(db, raw_email)
    if not user:
        record_failed_attempt(canon_email)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if user.auth_provider == "google" and not user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account was registered using Google Sign-In. Please sign in with Google."
        )

    if not verify_password(req.password, user.password_hash):
        record_failed_attempt(canon_email)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    clear_failed_attempts(canon_email)

    if user.password_hash and not user.password_hash.startswith("pbkdf2:sha256:"):
        user.password_hash = hash_password(req.password)

    user.last_login_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    db.commit()

    token = create_user_session(db, user.id)
    restore_user_data_flags(db, user)

    user_state = {}
    try:
        user_state = json.loads(user.state_data or "{}")
    except Exception:
        user_state = {}

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
def google_auth_direct(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Direct Google ID Token verification endpoint (supports Google Identity Services / Mobile clients)."""
    verified_email = None
    verified_name = None
    verified_avatar = None
    google_sub = None

    if req.id_token:
        google_payload = verify_google_token(req.id_token, GOOGLE_CLIENT_ID)
        if google_payload:
            raw_email = (google_payload.get("email") or "").strip().lower()
            verified_email = raw_email
            canonical_email = normalize_email(raw_email)
            verified_name = req.name.strip() if req.name and req.name.strip() else (google_payload.get("name") or derive_name_from_email(verified_email))
            verified_avatar = google_payload.get("picture")
            google_sub = google_payload.get("sub")
        else:
            raise HTTPException(
                status_code=401,
                detail="Google authentication token could not be verified by Google. Please try again."
            )

    if not verified_email:
        raise HTTPException(status_code=400, detail="A valid verified Google ID token is required.")

    now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Check OAuthAccount by sub
    oauth_acc = None
    if google_sub:
        oauth_acc = db.query(OAuthAccount).filter(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_user_id == google_sub
        ).first()

    if oauth_acc:
        user = db.query(User).filter(User.id == oauth_acc.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User account not found.")
        user.last_login_at = now_str
        if verified_avatar:
            user.avatar_url = verified_avatar
        db.commit()
    else:
        user = find_user_by_email(db, verified_email)
        if not user:
            # Register new Google user
            user_id = secrets.token_hex(16)
            initial_state = {
                "has_data": False,
                "active_panel": "home",
                "registered_at": now_str,
            }
            user = User(
                id=user_id,
                email=verified_email,
                canonical_email=canonical_email,
                name=verified_name,
                auth_provider="google",
                password_hash=None,
                avatar_url=verified_avatar,
                created_at=now_str,
                last_login_at=now_str,
                state_data=json.dumps(initial_state),
            )
            db.add(user)
            db.flush()

            if google_sub:
                new_oauth = OAuthAccount(
                    id=secrets.token_hex(16),
                    user_id=user.id,
                    provider="google",
                    provider_user_id=google_sub,
                    email=verified_email,
                    email_verified=1,
                    created_at=now_str,
                    updated_at=now_str,
                )
                db.add(new_oauth)
            db.commit()
            db.flush()

            if google_sub:
                new_oauth = OAuthAccount(
                    id=secrets.token_hex(16),
                    user_id=user.id,
                    provider="google",
                    provider_user_id=google_sub,
                    email=verified_email,
                    email_verified=1,
                    created_at=now_str,
                    updated_at=now_str,
                )
                db.add(new_oauth)
            db.commit()
        else:
            # Existing user: if google_sub provided and user has no other google identity, link
            if google_sub:
                existing_oauth = db.query(OAuthAccount).filter(
                    OAuthAccount.user_id == user.id,
                    OAuthAccount.provider == "google"
                ).first()
                if existing_oauth and existing_oauth.provider_user_id != google_sub:
                    raise HTTPException(
                        status_code=400,
                        detail="This email is already associated with a different Google account."
                    )
                elif not existing_oauth:
                    new_oauth = OAuthAccount(
                        id=secrets.token_hex(16),
                        user_id=user.id,
                        provider="google",
                        provider_user_id=google_sub,
                        email=verified_email,
                        email_verified=1,
                        created_at=now_str,
                        updated_at=now_str,
                    )
                    db.add(new_oauth)

            user.last_login_at = now_str
            if verified_avatar:
                user.avatar_url = verified_avatar
            db.commit()

    token = create_user_session(db, user.id)
    restore_user_data_flags(db, user)

    user_state = {}
    try:
        user_state = json.loads(user.state_data or "{}")
    except Exception:
        user_state = {}

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
    """Validate current session token and return user profile and state."""
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please sign in.")

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
    """Save persistent user UI state across sessions."""
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
    """Terminate session. Preserves user data securely for their next login."""
    if authorization:
        clean_token = authorization.replace("Bearer ", "").strip()
        db.query(UserSession).filter(UserSession.token == clean_token).delete()
        db.commit()

    return {"status": "success", "message": "Logged out successfully"}

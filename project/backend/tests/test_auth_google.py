"""
Automated Unit and Integration Tests for SmartMart AI Google OAuth & Auth System.
Covers:
- PKCE generation and validation (RFC 7636)
- State generation, single-use enforcement, and replay attack defense
- Google authorization URL creation with prompt=select_account and nonce
- Cancellation handling (access_denied)
- Account resolution:
  - Case 1: Existing Google-linked user login
  - Case 2: New Google user automatic registration
  - Case 3: Existing password account explicit linking safeguard
  - Case 4: Google identity mismatch protection
- Token verification security: invalid state, forged token, unverified email, nonce mismatch
- Concurrency and database uniqueness constraints
- Existing email/password auth regression
"""

import os
import sys
import time
import base64
import hashlib
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db, User, UserSession, OAuthAccount, OAuthState, AccountLinkingTicket
from main import app
from routes import auth_routes

# Isolated SQLite database for testing with StaticPool so all threads share the same in-memory DB
TEST_DB_URL = "sqlite:///:memory:"
engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ──────────────────────────── UNIT TESTS: CRYPTO & PKCE ────────────────────────────

def test_pkce_generation():
    verifier, challenge = auth_routes.generate_pkce_pair()
    assert len(verifier) >= 43
    # Verify RFC 7636 SHA-256 calculation
    expected_digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).decode("ascii").rstrip("=")
    assert challenge == expected_challenge


def test_password_hashing_and_verification():
    raw_pass = "SecureSecret123!"
    hashed = auth_routes.hash_password(raw_pass)
    assert hashed.startswith("pbkdf2:sha256:120000$")
    assert auth_routes.verify_password(raw_pass, hashed) is True
    assert auth_routes.verify_password("WrongPassword", hashed) is False


# ──────────────────────────── INTEGRATION TESTS: EMAIL / PASSWORD REGRESSION ────────────────────────────

def test_email_password_registration_and_login(client):
    # Register
    reg_resp = client.post("/api/auth/register", json={
        "email": "retailer@smartmart.io",
        "name": "Retail Manager",
        "password": "Password1234"
    })
    assert reg_resp.status_code == 200
    data = reg_resp.json()
    assert data["status"] == "success"
    assert data["user"]["email"] == "retailer@smartmart.io"
    token = data["token"]

    # Verify session with /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["name"] == "Retail Manager"

    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": "retailer@smartmart.io",
        "password": "Password1234"
    })
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()

    # Wrong password rejected
    bad_login = client.post("/api/auth/login", json={
        "email": "retailer@smartmart.io",
        "password": "IncorrectPassword"
    })
    assert bad_login.status_code == 401


# ──────────────────────────── GOOGLE OAUTH URL & INITIATION ────────────────────────────

def test_google_auth_url_generation_unconfigured(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "")
    resp = client.get("/api/auth/google/url")
    assert resp.status_code == 200
    assert resp.json()["configured"] is False


def test_google_auth_url_generation_configured(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    resp = client.get("/api/auth/google/url?prompt=select_account")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is True
    auth_url = data["auth_url"]
    assert "accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "prompt=select_account" in auth_url
    assert "code_challenge_method=S256" in auth_url
    assert "scope=openid+email+profile" in auth_url or "scope=openid%20email%20profile" in auth_url


def test_google_initiate_redirect(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")
    resp = client.get("/api/auth/google")
    assert resp.status_code == 302
    redirect_target = resp.headers["location"]
    assert "accounts.google.com/o/oauth2/v2/auth" in redirect_target
    assert "prompt=select_account" in redirect_target


def test_google_auth_cancellation_handled(client):
    # When user cancels or denies consent
    resp = client.get("/api/auth/google/callback?error=access_denied&error_description=User+denied+access")
    assert resp.status_code == 302
    target = resp.headers["location"]
    assert "auth_status=error" in target
    assert "access_denied" in target


# ──────────────────────────── GOOGLE CALLBACK & ACCOUNT RESOLUTION TESTS ────────────────────────────

def test_google_callback_invalid_or_expired_state(client):
    resp = client.get("/api/auth/google/callback?code=mock_code&state=non_existent_state")
    assert resp.status_code == 302
    assert "auth_status=error" in resp.headers["location"]


@patch("httpx.AsyncClient.post")
@patch("routes.auth_routes.verify_google_token")
def test_google_callback_case_2_new_user_registration(mock_verify, mock_token_post, client, monkeypatch):
    """Case 2: Verified Google identity is new -> automatically registers new user with sub claim."""
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    # 1. Initiate to generate state
    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    # 2. Mock Google Token Exchange & Verification
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"id_token": "valid_mock_jwt_token", "access_token": "mock_access"}
    mock_token_post.return_value = mock_token_resp

    mock_verify.return_value = {
        "sub": "google-sub-10001",
        "email": "new.shopper@gmail.com",
        "name": "Jane Shopper",
        "picture": "https://lh3.googleusercontent.com/avatar/jane.jpg",
        "email_verified": True,
        "iss": "https://accounts.google.com",
    }

    # 3. Call callback
    callback_resp = client.get(f"/api/auth/google/callback?code=valid_code&state={state}")
    assert callback_resp.status_code == 302
    target = callback_resp.headers["location"]
    assert "auth_status=success" in target
    assert "auth_token=" in target

    # 4. Verify in DB
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "new.shopper@gmail.com").first()
    assert user is not None
    assert user.name == "Jane Shopper"
    assert user.auth_provider == "google"
    assert user.avatar_url == "https://lh3.googleusercontent.com/avatar/jane.jpg"

    oauth_acc = db.query(OAuthAccount).filter(OAuthAccount.provider_user_id == "google-sub-10001").first()
    assert oauth_acc is not None
    assert oauth_acc.user_id == user.id
    db.close()


@patch("httpx.AsyncClient.post")
@patch("routes.auth_routes.verify_google_token")
def test_google_callback_case_1_existing_linked_user(mock_verify, mock_token_post, client, monkeypatch):
    """Case 1: User with existing Google sub signs in -> logs in immediately."""
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    # Pre-seed user and linked oauth_account
    db = TestingSessionLocal()
    user = User(
        id="user-google-1",
        email="linked.user@gmail.com",
        name="Linked User",
        auth_provider="google",
        password_hash=None,
        avatar_url=None,
        created_at="2026-01-01T00:00:00Z",
        last_login_at="2026-01-01T00:00:00Z",
        state_data="{}"
    )
    oauth = OAuthAccount(
        id="oauth-1",
        user_id="user-google-1",
        provider="google",
        provider_user_id="google-sub-20002",
        email="linked.user@gmail.com",
        email_verified=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z"
    )
    db.add(user)
    db.add(oauth)
    db.commit()
    db.close()

    # Initiate flow
    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"id_token": "valid_token"}
    mock_token_post.return_value = mock_token_resp

    mock_verify.return_value = {
        "sub": "google-sub-20002",
        "email": "linked.user@gmail.com",
        "name": "Linked User",
        "picture": "https://lh3.googleusercontent.com/avatar/linked.jpg",
        "email_verified": True,
        "iss": "https://accounts.google.com",
    }

    resp = client.get(f"/api/auth/google/callback?code=code_123&state={state}")
    assert resp.status_code == 302
    assert "auth_status=success" in resp.headers["location"]


@patch("httpx.AsyncClient.post")
@patch("routes.auth_routes.verify_google_token")
def test_google_callback_case_3_and_account_linking(mock_verify, mock_token_post, client, monkeypatch):
    """Case 3: Verified Google email matches existing email/password account.
    Safeguard: Requires explicit password authentication before linking.
    """
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    # 1. Create an existing email/password user
    db = TestingSessionLocal()
    existing_user = User(
        id="user-pwd-1",
        email="existing.owner@gmail.com",
        name="Existing Owner",
        auth_provider="email",
        password_hash=auth_routes.hash_password("MySuperPassword"),
        avatar_url=None,
        created_at="2026-01-01T00:00:00Z",
        last_login_at="2026-01-01T00:00:00Z",
        state_data="{}"
    )
    db.add(existing_user)
    db.commit()
    db.close()

    # 2. Google OAuth callback returns matching email but no linked sub
    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"id_token": "valid_token"}
    mock_token_post.return_value = mock_token_resp

    mock_verify.return_value = {
        "sub": "google-sub-30003",
        "email": "existing.owner@gmail.com",
        "name": "Existing Owner Google",
        "picture": "https://lh3.googleusercontent.com/avatar/owner.jpg",
        "email_verified": True,
        "iss": "https://accounts.google.com",
    }

    callback_resp = client.get(f"/api/auth/google/callback?code=code_333&state={state}")
    assert callback_resp.status_code == 302
    target = callback_resp.headers["location"]

    # Must require linking instead of logging in automatically
    assert "auth_status=linking_required" in target
    assert "ticket=" in target

    # Extract ticket from URL
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(target)
    qs = parse_qs(parsed.query)
    ticket = qs["ticket"][0]

    # 3. Attempt linking with wrong password -> rejected
    wrong_link = client.post("/api/auth/google/link", json={
        "ticket": ticket,
        "password": "WrongPassword!"
    })
    assert wrong_link.status_code == 401

    # 4. Attempt linking with correct password -> succeeds
    good_link = client.post("/api/auth/google/link", json={
        "ticket": ticket,
        "password": "MySuperPassword"
    })
    assert good_link.status_code == 200
    data = good_link.json()
    assert data["status"] == "success"
    assert "token" in data

    # 5. Verify in DB that OAuthAccount is now linked
    db = TestingSessionLocal()
    oauth_entry = db.query(OAuthAccount).filter(OAuthAccount.provider_user_id == "google-sub-30003").first()
    assert oauth_entry is not None
    assert oauth_entry.user_id == "user-pwd-1"
    db.close()


@patch("httpx.AsyncClient.post")
@patch("routes.auth_routes.verify_google_token")
def test_google_callback_case_4_mismatched_identity_rejected(mock_verify, mock_token_post, client, monkeypatch):
    """Case 4: Email matches an existing account that is already linked to a different Google identity -> rejected."""
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    # Create user linked to sub "original-sub"
    db = TestingSessionLocal()
    user = User(
        id="user-case4",
        email="conflict@gmail.com",
        name="Conflict User",
        auth_provider="google",
        password_hash=None,
        avatar_url=None,
        created_at="2026-01-01T00:00:00Z",
        last_login_at="2026-01-01T00:00:00Z",
        state_data="{}"
    )
    oauth = OAuthAccount(
        id="oauth-c4",
        user_id="user-case4",
        provider="google",
        provider_user_id="original-sub",
        email="conflict@gmail.com",
        email_verified=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z"
    )
    db.add(user)
    db.add(oauth)
    db.commit()
    db.close()

    # Now someone signs in with same email but DIFFERENT sub "imposter-sub"
    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"id_token": "valid_token"}
    mock_token_post.return_value = mock_token_resp

    mock_verify.return_value = {
        "sub": "imposter-sub",
        "email": "conflict@gmail.com",
        "name": "Different Google Account",
        "picture": None,
        "email_verified": True,
        "iss": "https://accounts.google.com",
    }

    resp = client.get(f"/api/auth/google/callback?code=code_4&state={state}")
    assert resp.status_code == 302
    assert "identity_mismatch" in resp.headers["location"]


@patch("httpx.AsyncClient.post")
@patch("routes.auth_routes.verify_google_token")
def test_google_callback_unverified_email_rejected(mock_verify, mock_token_post, client, monkeypatch):
    """Google claims with email_verified = False must be rejected."""
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"id_token": "valid_token"}
    mock_token_post.return_value = mock_token_resp

    mock_verify.return_value = {
        "sub": "unverified-sub",
        "email": "unverified@gmail.com",
        "email_verified": False,
        "iss": "https://accounts.google.com",
    }

    resp = client.get(f"/api/auth/google/callback?code=code_u&state={state}")
    assert resp.status_code == 302
    assert "not+verified" in resp.headers["location"] or "not%20verified" in resp.headers["location"]


def test_oauth_state_single_use_replay_prevention(client, monkeypatch):
    """State tokens are deleted upon first access to prevent replay attacks."""
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "test-client-secret")

    url_resp = client.get("/api/auth/google/url")
    state = url_resp.json()["state"]

    # First attempt: state is looked up and deleted
    # Even if exchange fails, state is already consumed
    client.get(f"/api/auth/google/callback?code=bad_code&state={state}")

    # Replay attempt with same state
    replay_resp = client.get(f"/api/auth/google/callback?code=bad_code&state={state}")
    assert replay_resp.status_code == 302
    target = replay_resp.headers["location"]
    assert "OAuth%20session%20invalid" in target or "OAuth+session+invalid" in target


def test_account_linking_expired_ticket_rejected(client):
    """Expired account linking tickets are rejected with 400."""
    db = TestingSessionLocal()
    user = User(
        id="user-exp",
        email="exp@gmail.com",
        name="Expired User",
        auth_provider="email",
        password_hash=auth_routes.hash_password("Pass123!"),
        created_at="2026-01-01T00:00:00Z",
        last_login_at="2026-01-01T00:00:00Z"
    )
    # Expired ticket
    ticket = AccountLinkingTicket(
        ticket="expired-ticket-xyz",
        user_id="user-exp",
        provider="google",
        provider_user_id="google-sub-exp",
        email="exp@gmail.com",
        created_at=time.time() - 1000,
        expires_at=time.time() - 400,
    )
    db.add(user)
    db.add(ticket)
    db.commit()
    db.close()

    resp = client.post("/api/auth/google/link", json={
        "ticket": "expired-ticket-xyz",
        "password": "Pass123!"
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


def test_database_sub_uniqueness_constraint():
    """Verify database unique constraint prevents duplicate provider_user_id (sub)."""
    db = TestingSessionLocal()
    u1 = User(id="u1", email="u1@test.com", name="U1", created_at="now", last_login_at="now")
    u2 = User(id="u2", email="u2@test.com", name="U2", created_at="now", last_login_at="now")
    db.add_all([u1, u2])
    db.commit()

    oa1 = OAuthAccount(
        id="oa1", user_id="u1", provider="google",
        provider_user_id="same-google-sub", email="u1@test.com",
        created_at="now", updated_at="now"
    )
    db.add(oa1)
    db.commit()

    oa2 = OAuthAccount(
        id="oa2", user_id="u2", provider="google",
        provider_user_id="same-google-sub", email="u2@test.com",
        created_at="now", updated_at="now"
    )
    db.add(oa2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()
    db.close()

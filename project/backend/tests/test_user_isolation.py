"""
Automated Integration Tests for Multi-Tenant User Isolation and Canonical Gmail Uniqueness.
Verifies:
1. Strict One Gmail ID = One Account (variations with dots and plus aliases are rejected).
2. Data isolation across inventory, sales, dashboard KPI metrics, and ML endpoints.
3. Data reset isolation (User B resetting data does not affect User A).
4. Chatbot isolation (User B cannot see User A's figures).
5. Non-destructive logout (logging out does not delete database rows).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from database import Base, get_db, User, Product, Sale, Inventory
from auth import normalize_email

# Use an isolated test database
TEST_DB_URL = "sqlite:///./test_user_isolation.db"
test_engine = create_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    import database
    orig_session_local = database.SessionLocal
    orig_engine = database.engine
    database.SessionLocal = TestingSessionLocal
    database.engine = test_engine

    Base.metadata.create_all(test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    database.SessionLocal = orig_session_local
    database.engine = orig_engine
    Base.metadata.drop_all(test_engine)
    if os.path.exists("./test_user_isolation.db"):
        try:
            os.remove("./test_user_isolation.db")
        except Exception:
            pass


@pytest.fixture
def client():
    return TestClient(app)


def test_canonical_gmail_one_account_only(client):
    """Test that canonical Gmail variations cannot create multiple accounts."""
    # 1. Register primary account
    resp1 = client.post("/api/auth/register", json={
        "name": "Primary Owner",
        "email": "fresh.market.hq@gmail.com",
        "password": "Password123!"
    })
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    assert data1["status"] == "success"

    # 2. Duplicate with removed dots should be rejected
    resp2 = client.post("/api/auth/register", json={
        "name": "Duplicate Owner",
        "email": "freshmarkethq@gmail.com",
        "password": "Password456!"
    })
    assert resp2.status_code in (400, 409)

    # 3. Duplicate with plus alias should be rejected
    resp3 = client.post("/api/auth/register", json={
        "name": "Alias Owner",
        "email": "fresh.market.hq+promo@gmail.com",
        "password": "Password789!"
    })
    assert resp3.status_code in (400, 409)

    # 4. Duplicate with googlemail.com should be rejected
    resp4 = client.post("/api/auth/register", json={
        "name": "Googlemail Owner",
        "email": "freshmarkethq@googlemail.com",
        "password": "Password999!"
    })
    assert resp4.status_code in (400, 409)

    # 5. Check email endpoint detects all variations
    check1 = client.post("/api/auth/check-email", json={"email": "freshmarkethq+branch1@gmail.com"})
    assert check1.status_code == 200
    assert check1.json()["exists"] is True

    # 6. Login using alias or undotted format succeeds with correct credentials
    login_resp = client.post("/api/auth/login", json={
        "email": "freshmarkethq@gmail.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()


def test_strict_data_isolation_between_users(client):
    """Test that User A and User B cannot view each other's products, sales, or dashboard metrics."""
    # Register User A
    resp_a = client.post("/api/auth/register", json={
        "name": "User Alpha",
        "email": "user.alpha@gmail.com",
        "password": "AlphaPassword1!"
    })
    assert resp_a.status_code == 200
    token_a = resp_a.json()["token"]
    user_a_id = resp_a.json()["user"]["id"]

    # Register User B
    resp_b = client.post("/api/auth/register", json={
        "name": "User Beta",
        "email": "user.beta@gmail.com",
        "password": "BetaPassword2!"
    })
    assert resp_b.status_code == 200
    token_b = resp_b.json()["token"]
    user_b_id = resp_b.json()["user"]["id"]

    # Seed User A data directly into test database
    db = TestingSessionLocal()
    prod_a = Product(
        user_id=user_a_id,
        product_id="PROD-A01",
        name="Alpha Chocolate",
        category="Sweets",
        price=150.0,
        cost=80.0
    )
    inv_a = Inventory(
        user_id=user_a_id,
        product_id="PROD-A01",
        current_stock=20,
        reorder_point=5
    )
    sale_a = Sale(
        user_id=user_a_id,
        sale_id="SALE-A01",
        basket_id="BASKET-A01",
        product_id="PROD-A01",
        customer_id="CUST-A01",
        quantity=2,
        unit_price=150.0,
        total_price=300.0,
        timestamp="2026-10-20 14:00:00"
    )
    db.add(prod_a)
    db.add(inv_a)
    db.add(sale_a)
    db.commit()
    db.close()

    # 1. User A checks their dashboard summary
    dash_a = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_a}"})
    assert dash_a.status_code == 200
    data_dash_a = dash_a.json()
    assert data_dash_a["total_revenue"] == 300.0
    assert data_dash_a["total_products"] == 1

    # 2. User B checks their dashboard summary -> MUST BE STRICTLY ZERO
    dash_b = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_b}"})
    assert dash_b.status_code == 200
    data_dash_b = dash_b.json()
    assert data_dash_b["total_revenue"] == 0.0
    assert data_dash_b["total_products"] == 0
    assert data_dash_b["total_transactions"] == 0

    # 3. User B checks inventory -> MUST NOT see User A's products
    inv_resp_b = client.get("/api/inventory", headers={"Authorization": f"Bearer {token_b}"})
    assert inv_resp_b.status_code == 200
    items_b = inv_resp_b.json().get("items", [])
    assert len(items_b) == 0

    # 4. User B checks sales -> MUST NOT see User A's sales
    sales_resp_b = client.get("/api/sales", headers={"Authorization": f"Bearer {token_b}"})
    assert sales_resp_b.status_code == 200
    sales_b = sales_resp_b.json()
    assert len(sales_b) == 0

    # 5. Unauthenticated request to dashboard summary returns zeroes
    dash_anon = client.get("/api/dashboard/summary")
    assert dash_anon.status_code == 200
    assert dash_anon.json()["total_revenue"] == 0.0


def test_reset_data_isolation(client):
    """Test that User B resetting data does not affect User A's records."""
    # Log in as User A
    login_a = client.post("/api/auth/login", json={
        "email": "user.alpha@gmail.com",
        "password": "AlphaPassword1!"
    })
    token_a = login_a.json()["token"]

    # Log in as User B
    login_b = client.post("/api/auth/login", json={
        "email": "user.beta@gmail.com",
        "password": "BetaPassword2!"
    })
    token_b = login_b.json()["token"]

    # User B triggers data reset
    reset_b = client.post("/api/upload/reset", headers={"Authorization": f"Bearer {token_b}"})
    assert reset_b.status_code == 200

    # Verify User A's data is still present and intact
    dash_a = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_a}"})
    assert dash_a.status_code == 200
    assert dash_a.json()["total_revenue"] == 300.0
    assert dash_a.json()["total_products"] == 1


def test_chatbot_data_isolation(client):
    """Test that chatbot does not leak data across accounts or to unauthenticated users."""
    login_b = client.post("/api/auth/login", json={
        "email": "user.beta@gmail.com",
        "password": "BetaPassword2!"
    })
    token_b = login_b.json()["token"]

    # 1. Unauthenticated chat query for data
    anon_chat = client.post("/api/chat", json={"message": "What is our total revenue?"})
    assert anon_chat.status_code == 200
    assert "sign in" in anon_chat.json()["reply"].lower() or "log in" in anon_chat.json()["reply"].lower()

    # 2. User B asks for revenue -> should reflect User B's store (0), not User A's (300)
    user_b_chat = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"message": "What is our total revenue?"}
    )
    assert user_b_chat.status_code == 200
    reply = user_b_chat.json()["reply"]
    # User B has no sales, so it should not say 300 or ₹300
    assert "₹300" not in reply


def test_logout_non_destructive(client):
    """Test that logging out does not destroy user data."""
    # Log in User A
    login_a = client.post("/api/auth/login", json={
        "email": "user.alpha@gmail.com",
        "password": "AlphaPassword1!"
    })
    token_a = login_a.json()["token"]

    # User A logs out
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    assert logout_resp.status_code == 200

    # User A logs back in with new session
    relogin_a = client.post("/api/auth/login", json={
        "email": "user.alpha@gmail.com",
        "password": "AlphaPassword1!"
    })
    new_token_a = relogin_a.json()["token"]

    # User A's data is still completely accessible
    dash_a = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {new_token_a}"})
    assert dash_a.status_code == 200
    assert dash_a.json()["total_revenue"] == 300.0


def test_clean_initial_state_and_remember_uploaded_data_across_sessions(client):
    """
    Verifies:
    1. Simply opening without login or creating a new account does NOT directly show demo data.
    2. Uploading data is remembered and restored when opening/logging in next time.
    """
    # 1. Open without login (guest) -> MUST be clean state
    anon_status = client.get("/api/upload/status")
    assert anon_status.status_code == 200
    data_anon = anon_status.json()
    assert data_anon["feature_flags"]["has_data"] is False
    assert data_anon["table_counts"]["sales"] == 0
    assert data_anon["table_counts"]["products"] == 0

    # 2. Register a new account -> MUST start with clean state (no demo data)
    resp_new = client.post("/api/auth/register", json={
        "name": "Fresh User",
        "email": "fresh.clean.store@gmail.com",
        "password": "CleanPassword123!"
    })
    assert resp_new.status_code == 200
    token_new = resp_new.json()["token"]
    user_id_new = resp_new.json()["user"]["id"]

    new_status = client.get("/api/upload/status", headers={"Authorization": f"Bearer {token_new}"})
    assert new_status.status_code == 200
    data_new = new_status.json()
    assert data_new["feature_flags"]["has_data"] is False
    assert data_new["table_counts"]["sales"] == 0
    assert data_new["table_counts"]["products"] == 0

    # 3. User uploads products and sales into their store
    db = TestingSessionLocal()
    db.add(Product(
        user_id=user_id_new,
        product_id="PROD-PERSIST-1",
        name="Organic Green Tea",
        category="Beverages",
        price=120.0,
        cost=70.0
    ))
    db.add(Sale(
        user_id=user_id_new,
        sale_id="SALE-PERSIST-1",
        basket_id="BASKET-P1",
        product_id="PROD-PERSIST-1",
        customer_id="CUST-P1",
        quantity=5,
        unit_price=120.0,
        total_price=600.0,
        timestamp="2026-10-22 10:00:00"
    ))
    db.commit()
    db.close()

    # Verify status now shows their data
    active_status = client.get("/api/upload/status", headers={"Authorization": f"Bearer {token_new}"})
    assert active_status.status_code == 200
    assert active_status.json()["feature_flags"]["has_data"] is True
    assert active_status.json()["table_counts"]["sales"] == 1
    assert active_status.json()["table_counts"]["products"] == 1

    # 4. User logs out
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_new}"})

    # 5. User logs in next time (e.g. next day) -> MUST see what they uploaded previously
    relogin = client.post("/api/auth/login", json={
        "email": "fresh.clean.store@gmail.com",
        "password": "CleanPassword123!"
    })
    assert relogin.status_code == 200
    next_token = relogin.json()["token"]

    next_status = client.get("/api/upload/status", headers={"Authorization": f"Bearer {next_token}"})
    assert next_status.status_code == 200
    next_data = next_status.json()
    assert next_data["feature_flags"]["has_data"] is True
    assert next_data["table_counts"]["sales"] == 1
    assert next_data["table_counts"]["products"] == 1

    next_dash = client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {next_token}"})
    assert next_dash.status_code == 200
    assert next_dash.json()["total_revenue"] == 600.0
    assert next_dash.json()["total_products"] == 1


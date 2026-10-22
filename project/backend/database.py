"""
Database setup - PostgreSQL (Supabase) / SQLite with SQLAlchemy
Loads CSV data and provides session management
"""

import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, ForeignKey, event, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

DATABASE_URL = os.getenv("DATABASE_URL")


def _get_pg_engine(url: str):
    clean = url.strip()
    if clean.startswith("postgres://"):
        clean = clean.replace("postgres://", "postgresql://", 1)

    # Try explicit driver prefixes to prevent ModuleNotFoundError
    candidates = []
    if not clean.startswith("postgresql+"):
        candidates.append(clean.replace("postgresql://", "postgresql+psycopg2://", 1))
        candidates.append(clean.replace("postgresql://", "postgresql+psycopg://", 1))
    candidates.append(clean)

    last_err = None
    for target in candidates:
        try:
            eng = create_engine(target, echo=False, pool_pre_ping=True, pool_recycle=300)
            return eng
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err


def _init_engine():
    if DATABASE_URL and DATABASE_URL.strip():
        try:
            eng = _get_pg_engine(DATABASE_URL)
            with eng.connect() as conn:
                pass
            print("✅ Successfully connected to PostgreSQL (Supabase)!")
            return eng
        except Exception as e:
            print(f"⚠️ [WARNING] Could not connect to PostgreSQL ({e}).")
            print("➡️ Automatically falling back to local SQLite engine so server stays LIVE!")

    db_path = os.path.join(BASE_DIR, "supermarket.db")
    sqlite_eng = create_engine(f"sqlite:///{db_path}", echo=False)

    @event.listens_for(sqlite_eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return sqlite_eng


engine = _init_engine()
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()




# ──────────────────────────── ORM MODELS ────────────────────────────

class Supplier(Base):
    __tablename__ = "suppliers"
    user_id = Column(String(64), primary_key=True, default="", index=True)
    supplier_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    contact_email = Column(String)
    lead_time_days = Column(Integer)
    reliability_score = Column(Float)


class Product(Base):
    __tablename__ = "products"
    user_id = Column(String(64), primary_key=True, default="", index=True)
    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    supplier = Column(String)
    supplier_id = Column(String)
    shelf_life_days = Column(Integer)
    unit = Column(String)


class Customer(Base):
    __tablename__ = "customers"
    user_id = Column(String(64), primary_key=True, default="", index=True)
    customer_id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    membership_tier = Column(String)
    email = Column(String)
    phone = Column(String)
    zip_code = Column(String)
    loyalty_points = Column(Integer)
    preferred_section = Column(String)
    join_date = Column(String)


class Sale(Base):
    __tablename__ = "sales"
    user_id = Column(String(64), primary_key=True, default="", index=True)
    sale_id = Column(String, primary_key=True)
    basket_id = Column(String)
    product_id = Column(String)
    customer_id = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    discount = Column(Float)
    total_price = Column(Float)
    timestamp = Column(String)
    payment_method = Column(String)


class Inventory(Base):
    __tablename__ = "inventory"
    user_id = Column(String(64), primary_key=True, default="", index=True)
    product_id = Column(String, primary_key=True)
    current_stock = Column(Integer)
    max_stock = Column(Integer)
    reorder_point = Column(Integer)
    last_restock_date = Column(String)
    warehouse_location = Column(String)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    canonical_email = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    auth_provider = Column(String, default="email")  # "email" or "google"
    password_hash = Column(String, nullable=True)     # None for google auth
    avatar_url = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    last_login_at = Column(String, nullable=False)
    state_data = Column(Text, default="{}")          # JSON string storing user session state

    def __init__(self, **kwargs):
        if "email" in kwargs and kwargs["email"]:
            raw_email = kwargs["email"].strip().lower()
            kwargs["email"] = raw_email
            if "canonical_email" not in kwargs or not kwargs["canonical_email"]:
                try:
                    from auth import normalize_email
                    kwargs["canonical_email"] = normalize_email(raw_email)
                except Exception:
                    kwargs["canonical_email"] = raw_email
        super().__init__(**kwargs)


class UserSession(Base):
    __tablename__ = "user_sessions"
    token = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="google")
    provider_user_id = Column(String, nullable=False, index=True)  # Stable Google sub claim
    email = Column(String, nullable=False)
    email_verified = Column(Integer, default=1)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user_id"),
    )


class OAuthState(Base):
    __tablename__ = "oauth_states"
    state = Column(String, primary_key=True)
    code_verifier = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=False)
    dest = Column(String, default="/")
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)


class AccountLinkingTicket(Base):
    __tablename__ = "account_linking_tickets"
    ticket = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False, default="google")
    provider_user_id = Column(String, nullable=False)
    email = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)


def init_db():
    """Create tables (preserving schema/constraints) and ensure multi-tenant user isolation."""
    Base.metadata.create_all(engine)
    try:
        from migrate_multitenant import run_multitenant_migration
        run_multitenant_migration(engine)
    except Exception as e:
        print(f"[-] Multi-tenant migration check notice: {e}")
    print("Database tables initialized!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
Database setup - PostgreSQL (Supabase) / SQLite with SQLAlchemy
Loads CSV data and provides session management
"""

import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, ForeignKey, event
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


if DATABASE_URL and DATABASE_URL.strip():
    engine = _get_pg_engine(DATABASE_URL)

else:
    DB_PATH = os.path.join(BASE_DIR, "supermarket.db")
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()




# ──────────────────────────── ORM MODELS ────────────────────────────

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    contact_email = Column(String)
    lead_time_days = Column(Integer)
    reliability_score = Column(Float)


class Product(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    supplier = Column(String)
    supplier_id = Column(String, ForeignKey("suppliers.supplier_id"))
    shelf_life_days = Column(Integer)
    unit = Column(String)


class Customer(Base):
    __tablename__ = "customers"
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
    product_id = Column(String, primary_key=True)
    current_stock = Column(Integer)
    max_stock = Column(Integer)
    reorder_point = Column(Integer)
    last_restock_date = Column(String)
    warehouse_location = Column(String)


# ──────────────────────────── INIT ────────────────────────────

def init_db():
    """Create tables (preserving schema/constraints) and load CSV data if empty."""
    # Create tables with proper PKs, FKs, and NOT NULL constraints
    Base.metadata.create_all(engine)

    session = SessionLocal()

    # Check if data already loaded
    if session.query(Product).count() > 0:
        session.close()
        return

    print("Loading CSV data into database...")

    # Load in a single transaction, using append to preserve schema
    try:
        with engine.begin() as conn:
            # Suppliers first (products reference them via FK)
            suppliers_path = os.path.join(DATA_DIR, "suppliers.csv")
            if os.path.exists(suppliers_path):
                suppliers = pd.read_csv(suppliers_path)
                suppliers.to_sql("suppliers", conn, if_exists="append", index=False)
                print(f"  Loaded {len(suppliers)} suppliers")

            # Products (with supplier_id populated from supplier name)
            products_path = os.path.join(DATA_DIR, "products.csv")
            if os.path.exists(products_path):
                products = pd.read_csv(products_path)
                # Map supplier name -> supplier_id for FK
                if os.path.exists(suppliers_path):
                    sup_df = pd.read_csv(suppliers_path)
                    name_to_id = dict(zip(sup_df["name"], sup_df["supplier_id"]))
                    products["supplier_id"] = products["supplier"].map(name_to_id)
                products.to_sql("products", conn, if_exists="append", index=False)
                print(f"  Loaded {len(products)} products")

            # Customers
            customers_path = os.path.join(DATA_DIR, "customers.csv")
            if os.path.exists(customers_path):
                customers = pd.read_csv(customers_path)
                customers.to_sql("customers", conn, if_exists="append", index=False)
                print(f"  Loaded {len(customers)} customers")

            # Sales
            sales_path = os.path.join(DATA_DIR, "sales.csv")
            if os.path.exists(sales_path):
                sales = pd.read_csv(sales_path)
                sales.to_sql("sales", conn, if_exists="append", index=False)
                print(f"  Loaded {len(sales)} sales")

            # Inventory
            inventory_path = os.path.join(DATA_DIR, "inventory.csv")
            if os.path.exists(inventory_path):
                inventory = pd.read_csv(inventory_path)
                inventory.to_sql("inventory", conn, if_exists="append", index=False)
                print(f"  Loaded {len(inventory)} inventory records")

    except Exception as e:
        print(f"Error loading CSV data: {e}")
        raise

    session.close()
    print("Database initialized!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

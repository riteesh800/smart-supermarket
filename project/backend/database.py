"""
Database setup - SQLite with SQLAlchemy
Loads CSV data and provides session management
"""

import os
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, event
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DB_PATH = os.path.join(BASE_DIR, "supermarket.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()



# ──────────────────────────── ORM MODELS ────────────────────────────

class Product(Base):
    __tablename__ = "products"
    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float)
    supplier = Column(String)
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


class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    contact_email = Column(String)
    lead_time_days = Column(Integer)
    reliability_score = Column(Float)


# ──────────────────────────── INIT ────────────────────────────

def init_db():
    """Create tables and load CSV data."""
    Base.metadata.create_all(engine)

    session = SessionLocal()

    # Check if data already loaded
    if session.query(Product).count() > 0:
        session.close()
        return

    print("Loading CSV data into database...")

    # Load products
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    products.to_sql("products", engine, if_exists="replace", index=False)
    print(f"  Loaded {len(products)} products")

    # Load customers
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    customers.to_sql("customers", engine, if_exists="replace", index=False)
    print(f"  Loaded {len(customers)} customers")

    # Load sales
    sales = pd.read_csv(os.path.join(DATA_DIR, "sales.csv"))
    sales.to_sql("sales", engine, if_exists="replace", index=False)
    print(f"  Loaded {len(sales)} sales")

    # Load inventory
    inventory = pd.read_csv(os.path.join(DATA_DIR, "inventory.csv"))
    inventory.to_sql("inventory", engine, if_exists="replace", index=False)
    print(f"  Loaded {len(inventory)} inventory records")

    # Load suppliers
    suppliers_path = os.path.join(DATA_DIR, "suppliers.csv")
    if os.path.exists(suppliers_path):
        suppliers = pd.read_csv(suppliers_path)
        suppliers.to_sql("suppliers", engine, if_exists="replace", index=False)
        print(f"  Loaded {len(suppliers)} suppliers")

    session.close()
    print("Database initialized!")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

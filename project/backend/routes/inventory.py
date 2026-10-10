"""
Inventory API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    cost: Optional[float] = None
    supplier: Optional[str] = None
    shelf_life_days: Optional[int] = 30
    unit: Optional[str] = "piece"
    initial_stock: Optional[int] = 50
    max_stock: Optional[int] = 200
    reorder_point: Optional[int] = 20


@router.get("")
def get_inventory(search: Optional[str] = None, category: Optional[str] = None,
                  page: int = 1, limit: int = 50, db: Session = Depends(get_db)):
    """Get inventory with optional search, filter, pagination."""
    query = """
        SELECT p.product_id, p.name, p.category, p.price, p.cost, p.supplier,
               p.shelf_life_days, p.unit,
               i.current_stock, i.max_stock, i.reorder_point,
               i.last_restock_date, i.warehouse_location
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE 1=1
    """
    params = {}

    if search:
        query += " AND (p.name LIKE :search OR p.product_id LIKE :search)"
        params["search"] = f"%{search}%"
    if category:
        query += " AND p.category = :category"
        params["category"] = category

    # Get total count — separate query to avoid fragile string replacement
    count_sql = """
        SELECT COUNT(*)
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE 1=1
    """
    if search:
        count_sql += " AND (p.name LIKE :search OR p.product_id LIKE :search)"
    if category:
        count_sql += " AND p.category = :category"
    total = db.execute(text(count_sql), params).scalar()

    query += " ORDER BY i.current_stock ASC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = (page - 1) * limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    columns = result.keys()
    items = [dict(zip(columns, row)) for row in rows]

    return {"items": items, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.get("/all")
def get_all_inventory(db: Session = Depends(get_db)):
    """Get full inventory (no pagination, for charts)."""
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price, p.supplier,
               p.shelf_life_days, p.unit,
               i.current_stock, i.max_stock, i.reorder_point,
               i.last_restock_date, i.warehouse_location
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        ORDER BY i.current_stock ASC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/low-stock")
def get_low_stock(db: Session = Depends(get_db)):
    """Get products below reorder point."""
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price,
               i.current_stock, i.reorder_point, i.max_stock
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE i.current_stock <= i.reorder_point
        ORDER BY i.current_stock ASC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/by-category")
def get_inventory_by_category(db: Session = Depends(get_db)):
    """Get stock summary by category."""
    result = db.execute(text("""
        SELECT p.category,
               COUNT(*) as product_count,
               SUM(i.current_stock) as total_stock,
               AVG(i.current_stock) as avg_stock,
               SUM(CASE WHEN i.current_stock <= i.reorder_point THEN 1 ELSE 0 END) as low_stock_count
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        GROUP BY p.category
        ORDER BY total_stock DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/expiring-soon")
def get_expiring_soon(db: Session = Depends(get_db)):
    """Get products expiring within 7 days (based on shelf life + last restock)."""
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.shelf_life_days,
               i.current_stock, i.last_restock_date,
               julianday('now') - julianday(i.last_restock_date) as days_since_restock,
               p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) as days_remaining
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id
        WHERE p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) <= 7
          AND p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) > -30
        ORDER BY days_remaining ASC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get list of all categories."""
    result = db.execute(text("SELECT DISTINCT category FROM products ORDER BY category"))
    return [row[0] for row in result.fetchall()]


@router.post("")
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to inventory."""
    # Generate next product ID atomically
    last_num = db.execute(text(
        "SELECT MAX(CAST(SUBSTR(product_id, 2) AS INTEGER)) FROM products"
    )).scalar() or 0
    new_id = f"P{last_num + 1:04d}"

    # Insert product
    db.execute(text("""
        INSERT INTO products (product_id, name, category, price, cost, supplier, shelf_life_days, unit)
        VALUES (:pid, :name, :cat, :price, :cost, :supplier, :shelf, :unit)
    """), {
        "pid": new_id, "name": product.name, "cat": product.category,
        "price": product.price, "cost": product.cost or round(product.price * 0.55, 2),
        "supplier": product.supplier or "Unknown", "shelf": product.shelf_life_days, "unit": product.unit
    })

    # Insert inventory record
    db.execute(text("""
        INSERT INTO inventory (product_id, current_stock, max_stock, reorder_point, last_restock_date, warehouse_location)
        VALUES (:pid, :stock, :max, :reorder, date('now'), 'Aisle-1-Shelf-A')
    """), {
        "pid": new_id, "stock": product.initial_stock,
        "max": product.max_stock, "reorder": product.reorder_point
    })

    db.commit()
    return {"message": "Product added", "product_id": new_id}


@router.post("/restock/{product_id}")
def restock_product(product_id: str, quantity: int = 50, db: Session = Depends(get_db)):
    """Restock a product."""
    # Check product exists
    prod = db.execute(text("SELECT product_id FROM products WHERE product_id = :pid"), {"pid": product_id}).fetchone()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db.execute(text("""
        UPDATE inventory
        SET current_stock = MIN(current_stock + :qty, max_stock),
            last_restock_date = date('now')
        WHERE product_id = :pid
    """), {"pid": product_id, "qty": quantity})
    db.commit()

    # Get updated stock
    updated = db.execute(text("SELECT current_stock FROM inventory WHERE product_id = :pid"), {"pid": product_id}).scalar()
    return {"message": "Restocked", "product_id": product_id, "new_stock": updated}

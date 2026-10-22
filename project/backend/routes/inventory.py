"""
Inventory API routes — Strictly Isolated Per User
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, User
from auth import get_current_user, require_current_user

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
def get_inventory(
    search: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get inventory for authenticated user with optional search, filter, pagination."""
    if not current_user:
        return {"items": [], "total": 0, "page": 1, "pages": 1}

    uid = current_user.id
    query = """
        SELECT p.product_id, p.name, p.category, p.price, p.cost, p.supplier,
               p.shelf_life_days, p.unit,
               i.current_stock, i.max_stock, i.reorder_point,
               i.last_restock_date, i.warehouse_location
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid
    """
    params = {"uid": uid}

    page = max(1, page)
    limit = max(1, min(limit, 500))

    if search:
        query += " AND (p.name LIKE :search OR p.product_id LIKE :search)"
        params["search"] = f"%{search}%"
    if category:
        query += " AND p.category = :category"
        params["category"] = category

    count_sql = """
        SELECT COUNT(*)
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid
    """
    if search:
        count_sql += " AND (p.name LIKE :search OR p.product_id LIKE :search)"
    if category:
        count_sql += " AND p.category = :category"
    total = db.execute(text(count_sql), params).scalar() or 0

    query += " ORDER BY i.current_stock ASC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = (page - 1) * limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    columns = result.keys()
    items = [dict(zip(columns, row)) for row in rows]

    pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    return {"items": items, "total": total, "page": page, "pages": pages}


@router.get("/all")
def get_all_inventory(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full inventory for authenticated user (for charts)."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price, p.supplier,
               p.shelf_life_days, p.unit,
               i.current_stock, i.max_stock, i.reorder_point,
               i.last_restock_date, i.warehouse_location
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid
        ORDER BY i.current_stock ASC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/low-stock")
def get_low_stock(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products below reorder point for authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price,
               i.current_stock, i.reorder_point, i.max_stock
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid AND i.current_stock <= i.reorder_point
        ORDER BY i.current_stock ASC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/by-category")
def get_inventory_by_category(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get stock summary by category for authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT p.category,
               COUNT(*) as product_count,
               SUM(i.current_stock) as total_stock,
               ROUND(AVG(i.current_stock), 1) as avg_stock,
               SUM(CASE WHEN i.current_stock <= i.reorder_point THEN 1 ELSE 0 END) as low_stock_count
        FROM products p
        JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid
        GROUP BY p.category
        ORDER BY total_stock DESC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/expiring-soon")
def get_expiring_soon(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products expiring within 7 days for authenticated user."""
    if not current_user:
        return []
    uid = current_user.id
    is_pg = (db.bind.dialect.name == "postgresql")
    if is_pg:
        query = """
            SELECT p.product_id, p.name, p.category, p.shelf_life_days,
                   i.current_stock, i.last_restock_date,
                   (CURRENT_DATE - CAST(i.last_restock_date AS DATE)) as days_since_restock,
                   (p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) as days_remaining
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
            WHERE p.user_id = :uid
              AND (p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) <= 7
              AND (p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) > -30
            ORDER BY days_remaining ASC
        """
    else:
        query = """
            SELECT p.product_id, p.name, p.category, p.shelf_life_days,
                   i.current_stock, i.last_restock_date,
                   julianday('now') - julianday(i.last_restock_date) as days_since_restock,
                   p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) as days_remaining
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
            WHERE p.user_id = :uid
              AND p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) <= 7
              AND p.shelf_life_days - (julianday('now') - julianday(i.last_restock_date)) > -30
            ORDER BY days_remaining ASC
        """
    result = db.execute(text(query), {"uid": uid})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/categories")
def get_categories(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of categories for authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("SELECT DISTINCT category FROM products WHERE user_id = :uid ORDER BY category"), {"uid": current_user.id})
    return [row[0] for row in result.fetchall()]


@router.post("")
def add_product(
    product: ProductCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Add a new product to inventory for authenticated user."""
    uid = current_user.id
    existing_ids = set(db.execute(text("SELECT product_id FROM products WHERE user_id = :uid"), {"uid": uid}).scalars().all())
    p_nums = [int(pid[1:]) for pid in existing_ids if pid.startswith("P") and pid[1:].isdigit()]
    if p_nums:
        next_num = max(p_nums) + 1
    else:
        nums = [int(pid) for pid in existing_ids if pid.isdigit()]
        next_num = max(nums) + 1 if nums else len(existing_ids) + 1
    new_id = f"P{next_num:04d}"
    while new_id in existing_ids:
        next_num += 1
        new_id = f"P{next_num:04d}"

    sup_id = None
    if product.supplier:
        sup_row = db.execute(
            text("SELECT supplier_id FROM suppliers WHERE user_id = :uid AND (name = :sup OR supplier_id = :sup) LIMIT 1"),
            {"uid": uid, "sup": product.supplier}
        ).fetchone()
        if sup_row:
            sup_id = sup_row[0]

    db.execute(text("""
        INSERT INTO products (user_id, product_id, name, category, price, cost, supplier, supplier_id, shelf_life_days, unit)
        VALUES (:uid, :pid, :name, :cat, :price, :cost, :supplier, :sup_id, :shelf, :unit)
    """), {
        "uid": uid, "pid": new_id, "name": product.name, "cat": product.category,
        "price": product.price, "cost": product.cost or round(product.price * 0.55, 2),
        "supplier": product.supplier or "Unknown", "sup_id": sup_id,
        "shelf": product.shelf_life_days, "unit": product.unit
    })

    today_str = datetime.now().strftime("%Y-%m-%d")
    db.execute(text("""
        INSERT INTO inventory (user_id, product_id, current_stock, max_stock, reorder_point, last_restock_date, warehouse_location)
        VALUES (:uid, :pid, :stock, :max, :reorder, :today, 'Aisle-1-Shelf-A')
    """), {
        "uid": uid, "pid": new_id, "stock": product.initial_stock,
        "max": product.max_stock, "reorder": product.reorder_point,
        "today": today_str
    })

    db.commit()
    return {"message": "Product added", "product_id": new_id}


@router.post("/restock/{product_id}")
def restock_product(
    product_id: str,
    quantity: int = 50,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Restock a product for authenticated user."""
    uid = current_user.id
    prod = db.execute(text("SELECT product_id FROM products WHERE user_id = :uid AND product_id = :pid"), {"uid": uid, "pid": product_id}).fetchone()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found in your inventory")

    today_str = datetime.now().strftime("%Y-%m-%d")
    db.execute(text("""
        UPDATE inventory
        SET current_stock = CASE WHEN current_stock + :qty > max_stock THEN max_stock ELSE current_stock + :qty END,
            last_restock_date = :today
        WHERE user_id = :uid AND product_id = :pid
    """), {"uid": uid, "pid": product_id, "qty": quantity, "today": today_str})
    db.commit()

    updated = db.execute(text("SELECT current_stock FROM inventory WHERE user_id = :uid AND product_id = :pid"), {"uid": uid, "pid": product_id}).scalar()
    return {"message": "Restocked", "product_id": product_id, "new_stock": updated}

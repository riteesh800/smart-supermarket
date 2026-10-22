"""
Supplier API routes — Strictly Isolated Per User
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, User
from auth import get_current_user

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("")
def get_suppliers(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all suppliers for authenticated user with product counts."""
    if not current_user:
        return []

    result = db.execute(text("""
        SELECT s.supplier_id, s.name, s.contact_email, s.lead_time_days, s.reliability_score,
               COUNT(p.product_id) as products_supplied
        FROM suppliers s
        LEFT JOIN products p ON p.supplier_id = s.supplier_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY s.supplier_id, s.name, s.contact_email, s.lead_time_days, s.reliability_score
        ORDER BY s.reliability_score DESC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/performance")
def get_supplier_performance(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get supplier performance metrics for authenticated user."""
    if not current_user:
        return []

    uid = current_user.id
    result = db.execute(text("""
        SELECT s.supplier_id, s.name, s.lead_time_days, s.reliability_score,
               COUNT(DISTINCT p.product_id) as products_supplied,
               COUNT(DISTINCT p.category) as categories_covered,
               COALESCE(SUM(sa.total_price), 0) as total_revenue_generated,
               COALESCE(SUM(sa.quantity), 0) as total_units_sold
        FROM suppliers s
        LEFT JOIN products p ON p.supplier_id = s.supplier_id AND p.user_id = :uid
        LEFT JOIN sales sa ON sa.product_id = p.product_id AND sa.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY s.supplier_id, s.name, s.lead_time_days, s.reliability_score
        ORDER BY total_revenue_generated DESC
    """), {"uid": uid})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/{supplier_id}")
def get_supplier_detail(
    supplier_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get supplier detail with products for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please sign in to view supplier details.")

    uid = current_user.id
    sup = db.execute(text("SELECT * FROM suppliers WHERE user_id = :uid AND supplier_id = :sid"), {"uid": uid, "sid": supplier_id}).fetchone()
    if not sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    sup_dict = dict(zip(["supplier_id", "name", "contact_email", "lead_time_days", "reliability_score"], sup[1:6] if sup[0] == uid else sup[:5]))

    products = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price,
               i.current_stock, i.reorder_point
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id AND i.user_id = :uid
        WHERE p.user_id = :uid AND p.supplier_id = :sid
        ORDER BY p.category, p.name
    """), {"uid": uid, "sid": supplier_id})
    prod_rows = products.fetchall()
    prod_cols = products.keys()

    sup_dict["products"] = [dict(zip(prod_cols, row)) for row in prod_rows]
    return sup_dict

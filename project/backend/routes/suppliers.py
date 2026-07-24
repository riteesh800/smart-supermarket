"""
Supplier API routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("")
def get_suppliers(db: Session = Depends(get_db)):
    """Get all suppliers with product counts."""
    result = db.execute(text("""
        SELECT s.supplier_id, s.name, s.contact_email, s.lead_time_days, s.reliability_score,
               COUNT(p.product_id) as products_supplied
        FROM suppliers s
        LEFT JOIN products p ON p.supplier = s.name
        GROUP BY s.supplier_id
        ORDER BY s.reliability_score DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/performance")
def get_supplier_performance(db: Session = Depends(get_db)):
    """Get supplier performance metrics."""
    result = db.execute(text("""
        SELECT s.supplier_id, s.name, s.lead_time_days, s.reliability_score,
               COUNT(DISTINCT p.product_id) as products_supplied,
               COUNT(DISTINCT p.category) as categories_covered,
               COALESCE(SUM(sa.total_price), 0) as total_revenue_generated,
               COALESCE(SUM(sa.quantity), 0) as total_units_sold
        FROM suppliers s
        LEFT JOIN products p ON p.supplier = s.name
        LEFT JOIN sales sa ON sa.product_id = p.product_id
        GROUP BY s.supplier_id
        ORDER BY total_revenue_generated DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/{supplier_id}")
def get_supplier_detail(supplier_id: str, db: Session = Depends(get_db)):
    """Get supplier detail with products."""
    # Supplier info
    sup = db.execute(text("SELECT * FROM suppliers WHERE supplier_id = :sid"), {"sid": supplier_id}).fetchone()
    if not sup:
        return {"error": "Supplier not found"}
    sup_dict = dict(zip(["supplier_id", "name", "contact_email", "lead_time_days", "reliability_score"], sup))

    # Products from this supplier
    products = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price,
               i.current_stock, i.reorder_point
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        WHERE p.supplier = :sname
        ORDER BY p.category, p.name
    """), {"sname": sup_dict["name"]})
    prod_rows = products.fetchall()
    prod_cols = products.keys()

    sup_dict["products"] = [dict(zip(prod_cols, row)) for row in prod_rows]
    return sup_dict

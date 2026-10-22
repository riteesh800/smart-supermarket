"""
Sales API routes — Strictly Isolated Per User
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, User
from auth import get_current_user

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("")
def get_sales(
    limit: int = 100,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent sales transactions for the authenticated user."""
    if not current_user:
        return []
    limit = max(1, min(limit, 1000))
    result = db.execute(text("""
        SELECT s.sale_id, s.basket_id, s.product_id,
               COALESCE(p.name, s.product_id) as product_name,
               COALESCE(p.category, 'General') as category,
               s.customer_id, s.quantity, s.unit_price, s.discount,
               s.total_price, s.timestamp, s.payment_method
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        ORDER BY s.timestamp DESC
        LIMIT :limit
    """), {"limit": limit, "uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/revenue")
def get_revenue(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue aggregated by day, week, month for the authenticated user."""
    if not current_user:
        return {"daily": [], "monthly": []}

    uid = current_user.id
    # Daily revenue
    daily = db.execute(text("""
        SELECT SUBSTR(timestamp, 1, 10) as date,
               SUM(total_price) as revenue,
               COUNT(*) as transactions,
               SUM(quantity) as units_sold
        FROM sales
        WHERE user_id = :uid
        GROUP BY SUBSTR(timestamp, 1, 10)
        ORDER BY date ASC
    """), {"uid": uid})
    daily_rows = daily.fetchall()
    daily_cols = daily.keys()
    daily_data = [dict(zip(daily_cols, row)) for row in daily_rows]

    # Monthly revenue
    monthly = db.execute(text("""
        SELECT SUBSTR(timestamp, 1, 7) as month,
               SUM(total_price) as revenue,
               COUNT(*) as transactions,
               SUM(quantity) as units_sold
        FROM sales
        WHERE user_id = :uid
        GROUP BY SUBSTR(timestamp, 1, 7)
        ORDER BY month ASC
    """), {"uid": uid})
    monthly_rows = monthly.fetchall()
    monthly_cols = monthly.keys()
    monthly_data = [dict(zip(monthly_cols, row)) for row in monthly_rows]

    return {"daily": daily_data, "monthly": monthly_data}


@router.get("/best-sellers")
def get_best_sellers(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top selling products for the authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT COALESCE(p.product_id, s.product_id) as product_id,
               COALESCE(MAX(p.name), MAX(s.product_id)) as name,
               COALESCE(MAX(p.category), 'General') as category,
               COALESCE(MAX(p.price), MAX(s.unit_price), 0) as price,
               SUM(s.quantity) as total_quantity,
               SUM(s.total_price) as total_revenue,
               COUNT(s.sale_id) as total_transactions
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY COALESCE(p.product_id, s.product_id)
        ORDER BY total_revenue DESC
        LIMIT 20
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/by-category")
def get_sales_by_category(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales breakdown by category for the authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT COALESCE(p.category, 'General') as category,
               SUM(s.total_price) as total_revenue,
               SUM(s.quantity) as total_quantity,
               COUNT(s.sale_id) as total_transactions,
               AVG(s.total_price) as avg_transaction
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY COALESCE(p.category, 'General')
        ORDER BY total_revenue DESC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/hourly-heatmap")
def get_hourly_heatmap(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales count by hour and day-of-week for heatmap."""
    if not current_user:
        return []
    is_pg = (db.bind.dialect.name == "postgresql")
    if is_pg:
        query = """
            SELECT CAST(EXTRACT(DOW FROM timestamp::timestamp) AS INTEGER) as day_of_week,
                   CAST(EXTRACT(HOUR FROM timestamp::timestamp) AS INTEGER) as hour,
                   COUNT(*) as sales_count,
                   SUM(total_price) as revenue
            FROM sales
            WHERE user_id = :uid
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        """
    else:
        query = """
            SELECT CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
                   CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                   COUNT(*) as sales_count,
                   SUM(total_price) as revenue
            FROM sales
            WHERE user_id = :uid
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        """
    result = db.execute(text(query), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/payment-breakdown")
def get_payment_breakdown(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment method distribution for the authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT payment_method,
               COUNT(*) as count,
               SUM(total_price) as total_revenue,
               AVG(total_price) as avg_transaction
        FROM sales
        WHERE user_id = :uid
        GROUP BY payment_method
        ORDER BY total_revenue DESC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/profit-margins")
def get_profit_margins(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get profit margin analysis by category for the authenticated user."""
    if not current_user:
        return []
    result = db.execute(text("""
        SELECT COALESCE(p.category, 'General') as category,
               SUM(s.total_price) as total_revenue,
               SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, s.unit_price * 0.55, 0)) as total_cost,
               SUM(s.total_price) - SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, s.unit_price * 0.55, 0)) as total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY COALESCE(p.category, 'General')
        ORDER BY total_profit DESC
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    output = []
    for row in rows:
        item = dict(zip(columns, row))
        rev = float(item.get("total_revenue") or 0)
        profit = float(item.get("total_profit") or 0)
        item["margin_pct"] = round(profit / rev * 100, 1) if rev > 0 else 0.0
        output.append(item)
    return output

"""
Sales API routes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("")
def get_sales(limit: int = 100, db: Session = Depends(get_db)):
    """Get recent sales transactions."""
    result = db.execute(text("""
        SELECT s.sale_id, s.basket_id, s.product_id, p.name as product_name, p.category,
               s.customer_id, s.quantity, s.unit_price, s.discount,
               s.total_price, s.timestamp, s.payment_method
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        ORDER BY s.timestamp DESC
        LIMIT :limit
    """), {"limit": limit})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/revenue")
def get_revenue(db: Session = Depends(get_db)):
    """Get revenue aggregated by day, week, month."""
    # Daily revenue
    daily = db.execute(text("""
        SELECT DATE(timestamp) as date,
               SUM(total_price) as revenue,
               COUNT(*) as transactions,
               SUM(quantity) as units_sold
        FROM sales
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    """))
    daily_rows = daily.fetchall()
    daily_cols = daily.keys()
    daily_data = [dict(zip(daily_cols, row)) for row in daily_rows]

    # Monthly revenue
    monthly = db.execute(text("""
        SELECT strftime('%Y-%m', timestamp) as month,
               SUM(total_price) as revenue,
               COUNT(*) as transactions,
               SUM(quantity) as units_sold
        FROM sales
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY month ASC
    """))
    monthly_rows = monthly.fetchall()
    monthly_cols = monthly.keys()
    monthly_data = [dict(zip(monthly_cols, row)) for row in monthly_rows]

    return {"daily": daily_data, "monthly": monthly_data}


@router.get("/best-sellers")
def get_best_sellers(db: Session = Depends(get_db)):
    """Get top selling products."""
    result = db.execute(text("""
        SELECT p.product_id, p.name, p.category, p.price,
               SUM(s.quantity) as total_quantity,
               SUM(s.total_price) as total_revenue,
               COUNT(s.sale_id) as total_transactions
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.product_id
        ORDER BY total_revenue DESC
        LIMIT 20
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/by-category")
def get_sales_by_category(db: Session = Depends(get_db)):
    """Get sales breakdown by category."""
    result = db.execute(text("""
        SELECT p.category,
               SUM(s.total_price) as total_revenue,
               SUM(s.quantity) as total_quantity,
               COUNT(s.sale_id) as total_transactions,
               AVG(s.total_price) as avg_transaction
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_revenue DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/hourly-heatmap")
def get_hourly_heatmap(db: Session = Depends(get_db)):
    """Get sales count by hour and day-of-week for heatmap."""
    result = db.execute(text("""
        SELECT CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
               CAST(strftime('%H', timestamp) AS INTEGER) as hour,
               COUNT(*) as sales_count,
               SUM(total_price) as revenue
        FROM sales
        GROUP BY day_of_week, hour
        ORDER BY day_of_week, hour
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/payment-breakdown")
def get_payment_breakdown(db: Session = Depends(get_db)):
    """Get payment method distribution."""
    result = db.execute(text("""
        SELECT payment_method,
               COUNT(*) as count,
               SUM(total_price) as total_revenue,
               AVG(total_price) as avg_transaction
        FROM sales
        GROUP BY payment_method
        ORDER BY total_revenue DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.get("/profit-margins")
def get_profit_margins(db: Session = Depends(get_db)):
    """Get profit margin analysis by category."""
    result = db.execute(text("""
        SELECT p.category,
               SUM(s.total_price) as total_revenue,
               SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, 0)) as total_cost,
               SUM(s.total_price) - SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, 0)) as total_profit,
               CASE WHEN SUM(s.total_price) > 0
                    THEN ROUND((SUM(s.total_price) - SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, 0))) / SUM(s.total_price) * 100, 1)
                    ELSE 0.0 END as margin_pct
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_profit DESC
    """))
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]

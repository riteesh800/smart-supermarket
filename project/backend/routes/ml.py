"""
ML prediction API routes
"""

from fastapi import APIRouter, Depends, HTTPException
import joblib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from auth import require_api_key

router = APIRouter(prefix="/api", tags=["ml"])

ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models", "saved")


def load_model(filename):
    path = os.path.join(ML_DIR, filename)
    if not os.path.exists(path):
        return None
    return joblib.load(path)


@router.get("/forecast")
def get_all_forecasts():
    """Get demand forecasts for all categories."""
    data = load_model("demand_forecasts.joblib")
    if not data:
        raise HTTPException(status_code=404, detail="Forecast model not trained. Load data and retrain models first.")
    result = {}
    for cat, val in data.items():
        result[cat] = {
            "forecast": val["forecast"],
            "historical_last_60": val["historical"][-60:] if len(val["historical"]) > 60 else val["historical"],
            "model": val.get("model", "holt_winters"),
        }
    return result


@router.get("/forecast/{category}")
def get_category_forecast(category: str):
    """Get demand forecast for specific category."""
    data = load_model("demand_forecasts.joblib")
    if not data:
        raise HTTPException(status_code=404, detail="Forecast model not trained")
    if category not in data:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found. Available: {list(data.keys())}")
    return data[category]


@router.get("/recommendations")
def get_recommendations():
    """Get product recommendations and suggestions."""
    data = load_model("recommendations.joblib")
    if not data:
        raise HTTPException(status_code=404, detail="Recommendation model not trained")
    return {
        "suggestions": data["suggestions"],
        "top_rules": data["rules"][:20],
        "total_rules": data["total_rules"],
        "total_baskets": data["total_baskets"]
    }


@router.get("/anomalies")
def get_anomalies():
    """Get detected sales anomalies."""
    data = load_model("anomaly_detection.joblib")
    if not data:
        raise HTTPException(status_code=404, detail="Anomaly model not trained")
    return {
        "anomalies": data["anomalies"],
        "total_anomalies": data["total_anomalies"],
        "spikes": data["spikes"],
        "drops": data["drops"],
        "daily_summary": data["daily_summary"][-60:]  # Last 60 days
    }


@router.get("/pricing")
def get_pricing():
    """Get dynamic pricing suggestions."""
    data = load_model("dynamic_pricing.joblib")
    if not data:
        raise HTTPException(status_code=404, detail="Pricing model not trained")
    return {
        "suggestions": data["suggestions"],
        "action_summary": data["action_summary"],
        "avg_change_pct": data["avg_change_pct"]
    }


@router.post("/ml/retrain")
def retrain_models(_api_key: str = Depends(require_api_key)):
    """Retrain all ML models. Requires API key."""
    ml_dir = os.path.dirname(ML_DIR)
    train_script = os.path.join(ml_dir, "train_all.py")

    try:
        result = subprocess.run(
            [sys.executable, train_script],
            capture_output=True, text=True, timeout=120, cwd=ml_dir
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Training failed: {result.stderr[:500]}")
        return {
            "status": "success",
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Training timed out (120s limit)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training error: {str(e)}")


@router.get("/dashboard/summary")
def get_dashboard_summary():
    """Get KPI summary for dashboard."""
    from sqlalchemy import text
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Total revenue
        rev = db.execute(text("SELECT SUM(total_price) FROM sales")).scalar() or 0

        # Total cost (profit calc)
        cost = db.execute(text("""
            SELECT SUM(s.quantity * p.cost) FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE p.cost IS NOT NULL
        """)).scalar() or 0

        # Total products
        products = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0

        # Total customers
        customers = db.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0

        # Total transactions
        transactions = db.execute(text("SELECT COUNT(*) FROM sales")).scalar() or 0

        # Total baskets
        baskets = db.execute(text("SELECT COUNT(DISTINCT basket_id) FROM sales")).scalar() or 0

        # Low stock count
        low_stock = db.execute(text(
            "SELECT COUNT(*) FROM inventory WHERE current_stock <= reorder_point"
        )).scalar() or 0

        # Avg transaction value
        avg_txn = db.execute(text("SELECT AVG(total_price) FROM sales")).scalar() or 0

        # Avg basket value
        avg_basket = rev / baskets if baskets > 0 else 0

        # Top category by revenue
        top_cat = db.execute(text("""
            SELECT p.category, SUM(s.total_price) as rev
            FROM sales s JOIN products p ON s.product_id = p.product_id
            GROUP BY p.category ORDER BY rev DESC LIMIT 1
        """)).fetchone()

        # Total categories
        total_cats = db.execute(text("SELECT COUNT(DISTINCT category) FROM products")).scalar() or 0

        return {
            "total_revenue": round(rev, 2),
            "total_cost": round(cost, 2),
            "total_profit": round(rev - cost, 2),
            "profit_margin": round((rev - cost) / rev * 100, 1) if rev > 0 else 0,
            "total_products": products,
            "total_customers": customers,
            "total_transactions": transactions,
            "total_baskets": baskets,
            "low_stock_alerts": low_stock,
            "avg_transaction_value": round(avg_txn, 2),
            "avg_basket_value": round(avg_basket, 2),
            "top_category": top_cat[0] if top_cat else "N/A",
            "top_category_revenue": round(top_cat[1], 2) if top_cat else 0,
            "total_categories": total_cats,
        }
    finally:
        db.close()

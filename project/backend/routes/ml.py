"""
ML prediction API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import joblib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from auth import get_current_user, User
from database import get_db, SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["ml"])

ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models", "saved")


def load_model(filename: str, user_id: Optional[str] = None):
    if not user_id:
        return None
    path = os.path.join(ML_DIR, str(user_id), filename)
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


@router.get("/forecast")
def get_all_forecasts(current_user: Optional[User] = Depends(get_current_user)):
    """Get demand forecasts for all categories strictly for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to view demand forecasts.")
    data = load_model("demand_forecasts.joblib", user_id=current_user.id)
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


@router.get("/forecast/{category:path}")
def get_category_forecast(category: str, current_user: Optional[User] = Depends(get_current_user)):
    """Get demand forecast for specific category strictly for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to view demand forecasts.")
    data = load_model("demand_forecasts.joblib", user_id=current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="Forecast model not trained")
    if category in data:
        return data[category]
    # Fallback to case-insensitive lookup
    matched = next((k for k in data if k.lower() == category.lower()), None)
    if matched:
        return data[matched]
    raise HTTPException(status_code=404, detail=f"Category '{category}' not found. Available: {list(data.keys())}")


@router.get("/recommendations")
def get_recommendations(current_user: Optional[User] = Depends(get_current_user)):
    """Get product recommendations strictly for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to view recommendations.")
    data = load_model("recommendations.joblib", user_id=current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="Recommendation model not trained")
    return {
        "suggestions": data["suggestions"],
        "top_rules": data["rules"][:20],
        "total_rules": data["total_rules"],
        "total_baskets": data["total_baskets"]
    }


@router.get("/anomalies")
def get_anomalies(current_user: Optional[User] = Depends(get_current_user)):
    """Get detected sales anomalies strictly for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to view anomalies.")
    data = load_model("anomaly_detection.joblib", user_id=current_user.id)
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
def get_pricing(current_user: Optional[User] = Depends(get_current_user)):
    """Get dynamic pricing suggestions strictly for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in to view dynamic pricing.")
    data = load_model("dynamic_pricing.joblib", user_id=current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="Pricing model not trained")
    return {
        "suggestions": data["suggestions"],
        "action_summary": data["action_summary"],
        "avg_change_pct": data["avg_change_pct"]
    }


@router.post("/ml/retrain")
def retrain_models(current_user: Optional[User] = Depends(get_current_user)):
    """Retrain all ML models for the authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required to retrain models")
    ml_dir = os.path.dirname(ML_DIR)
    train_script = os.path.join(ml_dir, "train_all.py")

    try:
        result = subprocess.run(
            [sys.executable, train_script, "--user-id", str(current_user.id)],
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
def get_dashboard_summary(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get KPI summary for dashboard strictly isolated for authenticated user."""
    if not current_user:
        return {
            "total_revenue": 0.0,
            "total_cost": 0.0,
            "total_profit": 0.0,
            "profit_margin": 0.0,
            "total_products": 0,
            "total_customers": 0,
            "total_transactions": 0,
            "total_baskets": 0,
            "low_stock_alerts": 0,
            "avg_transaction_value": 0.0,
            "avg_basket_value": 0.0,
            "top_category": "N/A",
            "top_category_revenue": 0.0,
            "total_categories": 0,
        }

    from sqlalchemy import text

    uid = current_user.id

    # Total revenue
    rev = db.execute(
        text("SELECT SUM(total_price) FROM sales WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Total cost (profit calc)
    cost = db.execute(text("""
        SELECT SUM(s.quantity * COALESCE(p.cost, p.price * 0.55, s.unit_price * 0.55, 0))
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
    """), {"uid": uid}).scalar() or 0

    # Total products
    products = db.execute(
        text("SELECT COUNT(*) FROM products WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Total customers
    customers = db.execute(
        text("SELECT COUNT(*) FROM customers WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Total transactions
    transactions = db.execute(
        text("SELECT COUNT(*) FROM sales WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Total baskets
    baskets = db.execute(
        text("SELECT COUNT(DISTINCT basket_id) FROM sales WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Low stock count
    low_stock = db.execute(text(
        "SELECT COUNT(*) FROM inventory WHERE user_id = :uid AND current_stock <= reorder_point"
    ), {"uid": uid}).scalar() or 0

    # Avg transaction value
    avg_txn = db.execute(
        text("SELECT AVG(total_price) FROM sales WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

    # Avg basket value
    avg_basket = rev / baskets if baskets > 0 else 0

    # Top category by revenue
    top_cat = db.execute(text("""
        SELECT COALESCE(p.category, 'General') as cat, SUM(s.total_price) as rev
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id AND p.user_id = :uid
        WHERE s.user_id = :uid
        GROUP BY cat ORDER BY rev DESC LIMIT 1
    """), {"uid": uid}).fetchone()

    # Total categories
    total_cats = db.execute(
        text("SELECT COUNT(DISTINCT category) FROM products WHERE user_id = :uid"),
        {"uid": uid}
    ).scalar() or 0

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

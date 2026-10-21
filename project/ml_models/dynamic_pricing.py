"""
Dynamic Pricing Engine
Suggests price adjustments based on demand, stock levels, and elasticity
"""

import pandas as pd
import numpy as np
import joblib
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved")
os.makedirs(SAVE_DIR, exist_ok=True)


def load_table(table_name):
    db_path = os.path.join(os.path.dirname(BASE_DIR), "backend", "supermarket.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone()[0] > 0:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                if len(df) > 0:
                    conn.close()
                    return df
            conn.close()
        except Exception as e:
            print(f"Error loading {table_name} from database: {e}")
    # Fallback to CSV
    csv_path = os.path.join(DATA_DIR, f"{table_name}.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def compute_demand_metrics(sales_df, products_df, inventory_df):
    """Compute demand velocity & stock health per product."""
    if sales_df.empty or products_df.empty:
        return pd.DataFrame()

    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["timestamp"]).dt.date

    # Recent 30 day demand
    max_date = sales_df["date"].max()
    if pd.isnull(max_date):
        max_date = pd.Timestamp.now().date()
    cutoff = (pd.Timestamp(max_date) - pd.Timedelta(days=30)).date()
    recent = sales_df[sales_df["date"] >= cutoff]

    demand = recent.groupby("product_id").agg(
        recent_quantity=("quantity", "sum"),
        recent_revenue=("total_price", "sum"),
        recent_transactions=("sale_id", "nunique")
    ).reset_index()

    # Overall demand
    total_demand = sales_df.groupby("product_id").agg(
        total_quantity=("quantity", "sum"),
        avg_quantity_per_day=("quantity", lambda x: x.sum() / max(1, (max_date - sales_df["date"].min()).days))
    ).reset_index()

    metrics = products_df.merge(demand, on="product_id", how="left")
    metrics = metrics.merge(total_demand, on="product_id", how="left")
    metrics = metrics.merge(inventory_df[["product_id", "current_stock", "reorder_point"]], on="product_id", how="left")

    metrics = metrics.fillna(0)
    return metrics


def suggest_pricing(metrics_df):
    """Generate pricing suggestions based on demand & stock."""
    suggestions = []
    if metrics_df.empty:
        return suggestions

    for _, row in metrics_df.iterrows():
        current_price = row["price"]
        stock = row["current_stock"]
        reorder = row["reorder_point"]
        recent_qty = row["recent_quantity"]
        avg_daily = row["avg_quantity_per_day"]

        # Days of stock remaining
        days_remaining = stock / avg_daily if avg_daily > 0 else 999

        # Decision logic
        action = "Hold"
        suggested_price = current_price
        reason = "Demand and stock balanced"
        confidence = 0.5

        if stock <= reorder and recent_qty > avg_daily * 20:
            # Low stock + high demand -> increase price
            increase = min(0.15, max(0.05, 1 - (stock / max(1, reorder))))
            suggested_price = round(current_price * (1 + increase), 2)
            action = "Increase"
            reason = f"Low stock ({int(stock)} units) with high demand"
            confidence = 0.8
        elif days_remaining < 7 and recent_qty > avg_daily * 25:
            # Very low stock -> premium pricing
            suggested_price = round(current_price * 1.12, 2)
            action = "Increase"
            reason = f"Only {int(days_remaining)} days of stock left"
            confidence = 0.85
        elif stock > reorder * 3 and recent_qty < avg_daily * 15:
            # Overstocked + low demand -> markdown
            decrease = min(0.20, max(0.05, ((stock / max(1, reorder * 3)) - 1) * 0.1))
            suggested_price = round(current_price * (1 - decrease), 2)
            action = "Decrease"
            reason = f"Overstocked ({int(stock)} units) with declining demand"
            confidence = 0.75
        elif row.get("shelf_life_days", 999) <= 7 and days_remaining > 14:
            # Short shelf life + too much stock
            suggested_price = round(current_price * 0.85, 2)
            action = "Decrease"
            reason = "Short shelf life, need to move inventory"
            confidence = 0.7

        suggestions.append({
            "product_id": row["product_id"],
            "product_name": row["name"],
            "category": row["category"],
            "current_price": current_price,
            "suggested_price": suggested_price,
            "price_change_pct": round((suggested_price - current_price) / current_price * 100, 1) if current_price > 0 else 0,
            "action": action,
            "reason": reason,
            "confidence": round(confidence, 2),
            "current_stock": int(stock),
            "days_of_stock": round(days_remaining, 1),
            "recent_demand_30d": int(recent_qty)
        })

    return sorted(suggestions, key=lambda x: abs(x["price_change_pct"]), reverse=True)


def train():
    sales = load_table("sales")
    products = load_table("products")
    inventory = load_table("inventory")

    if sales.empty or products.empty:
        print("  No sales or product data available for dynamic pricing.")
        return {"suggestions": [], "action_summary": {}, "avg_change_pct": 0.0}

    # Ensure inventory has records for all products
    if inventory.empty or "current_stock" not in inventory.columns or "product_id" not in inventory.columns:
        inventory = pd.DataFrame({
            "product_id": products["product_id"],
            "current_stock": 50,
            "max_stock": 100,
            "reorder_point": 10,
            "last_restock_date": "2026-01-01",
            "warehouse_location": "A1"
        })
    else:
        existing_inv_pids = set(inventory["product_id"].astype(str))
        missing_pids = [pid for pid in products["product_id"].astype(str) if pid not in existing_inv_pids]
        if missing_pids:
            missing_inv = pd.DataFrame({
                "product_id": missing_pids,
                "current_stock": 50,
                "max_stock": 100,
                "reorder_point": 10,
                "last_restock_date": "2026-01-01",
                "warehouse_location": "A1"
            })
            inventory = pd.concat([inventory, missing_inv], ignore_index=True)

    metrics = compute_demand_metrics(sales, products, inventory)
    suggestions = suggest_pricing(metrics)

    # Summary
    if suggestions:
        actions = pd.DataFrame(suggestions)
        action_summary = actions["action"].value_counts().to_dict()
        avg_change = round(actions["price_change_pct"].mean(), 2)
    else:
        action_summary = {}
        avg_change = 0.0

    result = {
        "suggestions": suggestions,
        "action_summary": action_summary,
        "avg_change_pct": avg_change,
    }

    joblib.dump(result, os.path.join(SAVE_DIR, "dynamic_pricing.joblib"))

    increase = action_summary.get("Increase", 0)
    decrease = action_summary.get("Decrease", 0)
    hold = action_summary.get("Hold", 0)
    print(f"  Pricing: {increase} increase, {decrease} decrease, {hold} hold")
    return result


if __name__ == "__main__":
    print("Computing dynamic pricing suggestions...")
    train()
    print("Done!")


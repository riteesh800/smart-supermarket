"""
Anomaly Detection using Isolation Forest
Flags unusual sales patterns (sudden drops or spikes)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved")
os.makedirs(SAVE_DIR, exist_ok=True)

try:
    from data_loader import load_table
except ImportError:
    from ml_models.data_loader import load_table



def prepare_daily_features(sales_df):
    """Create daily features for anomaly detection."""
    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["timestamp"]).dt.date
    sales_df["date"] = pd.to_datetime(sales_df["date"])

    daily = sales_df.groupby("date").agg(
        total_sales=("total_price", "sum"),
        total_quantity=("quantity", "sum"),
        num_transactions=("sale_id", "nunique"),
        avg_transaction_value=("total_price", "mean"),
        unique_products=("product_id", "nunique"),
        unique_customers=("customer_id", "nunique")
    ).reset_index()

    # Add rolling features
    daily = daily.sort_values("date")
    daily["sales_7d_avg"] = daily["total_sales"].rolling(7, min_periods=1).mean()
    daily["sales_deviation"] = daily["total_sales"] - daily["sales_7d_avg"]
    daily["quantity_7d_avg"] = daily["total_quantity"].rolling(7, min_periods=1).mean()

    return daily


def detect_anomalies(daily_df, contamination=0.05):
    """Run Isolation Forest on daily sales features."""
    features = ["total_sales", "total_quantity", "num_transactions",
                 "sales_deviation", "unique_products"]

    daily_df = daily_df.copy()
    if len(daily_df) < 5:
        # Too few samples for IsolationForest to run, return no anomalies
        daily_df["anomaly_score"] = 1
        daily_df["is_anomaly"] = False
        return daily_df, None, pd.DataFrame(columns=features + ["date", "sales_7d_avg", "sales_deviation", "anomaly_type", "severity"])

    X = daily_df[features].fillna(0).values

    try:
        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        daily_df["anomaly_score"] = model.fit_predict(X)
        daily_df["is_anomaly"] = daily_df["anomaly_score"] == -1
    except Exception:
        try:
            model = IsolationForest(
                contamination='auto',
                random_state=42,
                n_estimators=100
            )
            daily_df["anomaly_score"] = model.fit_predict(X)
            daily_df["is_anomaly"] = daily_df["anomaly_score"] == -1
        except Exception:
            daily_df["anomaly_score"] = 1
            daily_df["is_anomaly"] = False
            return daily_df, None, pd.DataFrame(columns=features + ["date", "sales_7d_avg", "sales_deviation", "anomaly_type", "severity"])

    # Classify anomaly type
    anomalies = daily_df[daily_df["is_anomaly"]].copy()
    if len(anomalies) > 0:
        anomalies["anomaly_type"] = anomalies.apply(
            lambda r: "Spike" if r["sales_deviation"] > 0 else "Drop", axis=1
        )
        median_dev = anomalies["sales_deviation"].abs().median()
        anomalies["severity"] = anomalies["sales_deviation"].abs().apply(
            lambda x: "High" if x > median_dev else "Medium"
        )
    else:
        anomalies["anomaly_type"] = pd.Series(dtype=str)
        anomalies["severity"] = pd.Series(dtype=str)

    return daily_df, model, anomalies


def train():
    sales = load_table("sales")
    if sales.empty:
        print("  No sales data available for anomaly detection.")
        return {"anomalies": [], "total_anomalies": 0, "spikes": 0, "drops": 0, "daily_summary": []}

    daily = prepare_daily_features(sales)
    daily_all, model, anomalies = detect_anomalies(daily)

    if not anomalies.empty:
        anomaly_records = anomalies[[
            "date", "total_sales", "total_quantity", "num_transactions",
            "sales_7d_avg", "sales_deviation", "anomaly_type", "severity"
        ]].copy()
        anomaly_records["date"] = anomaly_records["date"].dt.strftime("%Y-%m-%d")
        anomaly_records["total_sales"] = anomaly_records["total_sales"].round(2)
        anomaly_records["sales_7d_avg"] = anomaly_records["sales_7d_avg"].round(2)
        anomaly_records["sales_deviation"] = anomaly_records["sales_deviation"].round(2)
        anomaly_list = anomaly_records.to_dict(orient="records")
    else:
        anomaly_list = []

    result = {
        "model": model,
        "anomalies": anomaly_list,
        "total_anomalies": len(anomalies),
        "spikes": len(anomalies[anomalies["anomaly_type"] == "Spike"]) if not anomalies.empty else 0,
        "drops": len(anomalies[anomalies["anomaly_type"] == "Drop"]) if not anomalies.empty else 0,
        "daily_summary": daily_all[["date", "total_sales", "total_quantity", "is_anomaly"]].assign(
            date=lambda x: x["date"].dt.strftime("%Y-%m-%d")
        ).to_dict(orient="records")
    }

    joblib.dump(result, os.path.join(SAVE_DIR, "anomaly_detection.joblib"))
    print(f"  Detected {len(anomalies)} anomalies ({result['spikes']} spikes, {result['drops']} drops)")
    return result


if __name__ == "__main__":
    print("Training anomaly detection model...")
    train()
    print("Done!")


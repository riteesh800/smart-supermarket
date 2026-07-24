"""
Customer Segmentation using RFM Analysis + K-Means Clustering
5 segments: Champions, Loyal, Potential, At Risk, Lost
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
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


def compute_rfm(sales_df, reference_date=None):
    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["timestamp"]).dt.date

    if reference_date is None:
        reference_date = sales_df["date"].max()

    rfm = sales_df.groupby("customer_id").agg(
        recency=("date", lambda x: (reference_date - x.max()).days),
        frequency=("sale_id", "nunique"),
        monetary=("total_price", "sum")
    ).reset_index()

    rfm["monetary"] = rfm["monetary"].round(2)
    return rfm


def segment_customers(rfm_df, n_clusters=5):
    # Adjust number of clusters based on sample size
    n_samples = len(rfm_df)
    n_clusters = min(n_clusters, n_samples)
    if n_clusters < 1:
        # Return empty/dummy results
        return rfm_df, None, None, pd.DataFrame(), {}

    features = rfm_df[["recency", "frequency", "monetary"]].values
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm_df = rfm_df.copy()
    rfm_df["cluster"] = kmeans.fit_predict(scaled)

    # Label clusters based on characteristics
    cluster_summary = rfm_df.groupby("cluster").agg(
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        count=("customer_id", "count")
    ).reset_index()

    # Sort by monetary descending to assign labels
    cluster_summary = cluster_summary.sort_values("avg_monetary", ascending=False)
    labels = ["Champions", "Loyal Customers", "Potential", "At Risk", "Lost"]
    label_map = dict(zip(cluster_summary["cluster"], labels[:n_clusters]))
    rfm_df["segment"] = rfm_df["cluster"].map(label_map)

    return rfm_df, kmeans, scaler, cluster_summary, label_map


def train():
    sales = load_table("sales")
    customers = load_table("customers")

    if sales.empty or "customer_id" not in sales.columns:
        print("  No sales data available for customer segmentation.")
        return pd.DataFrame()

    rfm = compute_rfm(sales)
    segmented, model, scaler, summary, label_map = segment_customers(rfm)

    # Merge with customer details
    if not customers.empty and "customer_id" in customers.columns:
        result = segmented.merge(customers, on="customer_id", how="left")
    else:
        result = segmented.copy()

    # Fill missing details with defaults
    for col in ["first_name", "last_name", "email", "phone", "gender", "membership_tier"]:
        if col not in result.columns:
            if col in ["first_name", "last_name"]:
                result[col] = result["customer_id"].astype(str)
            elif col == "membership_tier":
                result[col] = "Standard"
            else:
                result[col] = "Unknown"
        else:
            result[col] = result[col].fillna("Unknown" if col != "membership_tier" else "Standard")

    # Save
    joblib.dump({
        "model": model,
        "scaler": scaler,
        "label_map": label_map,
        "segmented_data": result.to_dict(orient="records"),
        "cluster_summary": summary.to_dict(orient="records") if not summary.empty else [],
        "segment_counts": result["segment"].value_counts().to_dict() if "segment" in result.columns else {},
        "top_customers": result.nlargest(20, "monetary")[
            ["customer_id", "first_name", "last_name", "segment",
             "recency", "frequency", "monetary", "membership_tier"]
        ].to_dict(orient="records") if "segment" in result.columns else []
    }, os.path.join(SAVE_DIR, "customer_segments.joblib"))

    if "segment" in result.columns:
        print(f"  Segmented {len(result)} customers into segments:")
        for seg, count in result["segment"].value_counts().items():
            print(f"    {seg}: {count}")
    return result


if __name__ == "__main__":
    print("Training customer segmentation model...")
    train()
    print("Done!")


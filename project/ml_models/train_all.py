"""
Train all ML models for the Smart Supermarket system
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
SAVE_DIR = os.path.join(BASE_DIR, "saved")


def train_all(user_id=None):
    save_dir = os.path.join(SAVE_DIR, user_id) if user_id else SAVE_DIR
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 50)
    print(f"Training All ML Models (Target Directory: {save_dir})")
    print("=" * 50)

    print("\n1. Demand Forecasting (ARIMA/Holt-Winters)...")
    from demand_forecast import train_all_categories
    train_all_categories(user_id=user_id, save_dir=save_dir)

    print("\n2. Customer Segmentation (K-Means + RFM)...")
    from customer_segmentation import train as train_cust
    train_cust(user_id=user_id, save_dir=save_dir)

    print("\n3. Product Recommendations (Apriori)...")
    from recommender import train as train_rec
    train_rec(user_id=user_id, save_dir=save_dir)

    print("\n4. Anomaly Detection (Isolation Forest)...")
    from anomaly_detection import train as train_anom
    train_anom(user_id=user_id, save_dir=save_dir)

    print("\n5. Dynamic Pricing Engine...")
    from dynamic_pricing import train as train_price
    train_price(user_id=user_id, save_dir=save_dir)

    print("\n" + "=" * 50)
    print("All models trained successfully!")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ML models for SmartMart")
    parser.add_argument("--user-id", default=None, help="User ID to train models for")
    args = parser.parse_args()
    train_all(user_id=args.user_id)

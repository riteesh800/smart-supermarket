"""
Train all ML models for the Smart Supermarket system
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def train_all():
    print("=" * 50)
    print("Training All ML Models")
    print("=" * 50)

    print("\n1. Demand Forecasting (ARIMA)...")
    from demand_forecast import train_all_categories
    train_all_categories()

    print("\n2. Customer Segmentation (K-Means + RFM)...")
    from customer_segmentation import train
    train()

    print("\n3. Product Recommendations (Apriori)...")
    from recommender import train as train_rec
    train_rec()

    print("\n4. Anomaly Detection (Isolation Forest)...")
    from anomaly_detection import train as train_anom
    train_anom()

    print("\n5. Dynamic Pricing Engine...")
    from dynamic_pricing import train as train_price
    train_price()

    print("\n" + "=" * 50)
    print("All models trained successfully!")
    print("=" * 50)


if __name__ == "__main__":
    train_all()

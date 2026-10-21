"""
Product Recommendation using Association Rule Mining (Apriori)
Finds frequently co-purchased products using basket_id
"""

import pandas as pd
import numpy as np
from itertools import combinations
from collections import defaultdict
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



def build_baskets(sales_df):
    """Group products by basket_id (preferred), customer+date, or timestamp."""
    sales_df = sales_df.copy()
    if sales_df.empty or "product_id" not in sales_df.columns:
        return []

    # Clean product IDs
    sales_df = sales_df[sales_df["product_id"].notnull() & (sales_df["product_id"] != "")]

    # Strategy 1: Explicit basket_id
    if "basket_id" in sales_df.columns:
        b = sales_df.groupby("basket_id")["product_id"].apply(list).reset_index()
        multi = b[b["product_id"].apply(len) >= 2]
        if len(multi) >= 2:
            return multi["product_id"].tolist()

    # Strategy 2: customer_id + date
    if "customer_id" in sales_df.columns and "timestamp" in sales_df.columns:
        sales_df["date"] = pd.to_datetime(sales_df["timestamp"], errors="coerce").dt.date
        valid_cust = sales_df[sales_df["customer_id"].notnull() & (sales_df["customer_id"] != "UNKNOWN")]
        if not valid_cust.empty:
            b = valid_cust.groupby(["customer_id", "date"])["product_id"].apply(list).reset_index()
            multi = b[b["product_id"].apply(len) >= 2]
            if len(multi) >= 2:
                return multi["product_id"].tolist()

    # Strategy 3: invoice/timestamp group
    if "timestamp" in sales_df.columns:
        parsed_dt = pd.to_datetime(sales_df["timestamp"], errors="coerce")
        sales_df["time_slot"] = parsed_dt.dt.floor("15min")
        b = sales_df.dropna(subset=["time_slot"]).groupby("time_slot")["product_id"].apply(list).reset_index()
        multi = b[b["product_id"].apply(len) >= 2]
        return multi["product_id"].tolist()

    return []


def compute_item_frequencies(baskets, min_support_count=2):
    """Count individual item frequencies."""
    item_counts = defaultdict(int)
    for basket in baskets:
        for item in set(basket):
            item_counts[item] += 1
    return {k: v for k, v in item_counts.items() if v >= min_support_count}


def compute_pair_frequencies(baskets, frequent_items, min_support_count=1):
    """Count pair frequencies for frequent items only."""
    pair_counts = defaultdict(int)
    freq_set = set(frequent_items.keys())
    for basket in baskets:
        items = sorted(set(basket) & freq_set)
        for pair in combinations(items, 2):
            pair_counts[pair] += 1
    return {k: v for k, v in pair_counts.items() if v >= min_support_count}


def compute_association_rules(item_freq, pair_freq, n_baskets, min_confidence=0.03):
    """Generate association rules with confidence and lift."""
    rules = []
    if n_baskets == 0:
        return rules
    for (item_a, item_b), pair_count in pair_freq.items():
        support = pair_count / n_baskets

        # A -> B
        conf_ab = pair_count / item_freq[item_a] if item_a in item_freq and item_freq[item_a] > 0 else 0
        lift_ab = conf_ab / (item_freq[item_b] / n_baskets) if item_b in item_freq and item_freq[item_b] > 0 else 0
        if conf_ab >= min_confidence:
            rules.append({
                "antecedent": item_a,
                "consequent": item_b,
                "support": round(support, 4),
                "confidence": round(conf_ab, 4),
                "lift": round(lift_ab, 4)
            })

        # B -> A
        conf_ba = pair_count / item_freq[item_b] if item_b in item_freq and item_freq[item_b] > 0 else 0
        lift_ba = conf_ba / (item_freq[item_a] / n_baskets) if item_a in item_freq and item_freq[item_a] > 0 else 0
        if conf_ba >= min_confidence:
            rules.append({
                "antecedent": item_b,
                "consequent": item_a,
                "support": round(support, 4),
                "confidence": round(conf_ba, 4),
                "lift": round(lift_ba, 4)
            })

    return sorted(rules, key=lambda x: x["lift"], reverse=True)


def train():
    sales = load_table("sales")
    products = load_table("products")

    if sales.empty:
        print("  No sales data available for recommendations.")
        result = {"rules": [], "suggestions": [], "total_rules": 0, "total_baskets": 0}
        joblib.dump(result, os.path.join(SAVE_DIR, "recommendations.joblib"))
        return result

    product_names = dict(zip(products["product_id"], products["name"])) if not products.empty and "product_id" in products.columns and "name" in products.columns else {}
    product_categories = dict(zip(products["product_id"], products["category"])) if not products.empty and "product_id" in products.columns and "category" in products.columns else {}

    baskets = build_baskets(sales)
    print(f"  Built {len(baskets)} baskets")

    n_baskets = len(baskets)
    # Dynamically scale thresholds based on realistic market basket support
    min_support = max(2, int(n_baskets * 0.005)) if n_baskets > 0 else 2
    min_pair_support = max(1, int(n_baskets * 0.0008)) if n_baskets > 0 else 1
    min_conf = 0.03

    item_freq = compute_item_frequencies(baskets, min_support_count=min_support)
    pair_freq = compute_pair_frequencies(baskets, item_freq, min_support_count=min_pair_support)
    rules = compute_association_rules(item_freq, pair_freq, n_baskets, min_confidence=min_conf)

    # Enrich rules with product names
    for rule in rules:
        rule["antecedent_name"] = product_names.get(rule["antecedent"], rule["antecedent"])
        rule["consequent_name"] = product_names.get(rule["consequent"], rule["consequent"])
        rule["antecedent_category"] = product_categories.get(rule["antecedent"], "Unknown")
        rule["consequent_category"] = product_categories.get(rule["consequent"], "Unknown")

    # Top restock/promote suggestions based on high-lift rules
    suggestions = []
    seen = set()
    for rule in rules[:50]:
        pid = rule["consequent"]
        if pid not in seen:
            seen.add(pid)
            suggestions.append({
                "product_id": pid,
                "product_name": rule["consequent_name"],
                "category": rule["consequent_category"],
                "reason": f"Frequently bought with {rule['antecedent_name']}",
                "lift": rule["lift"]
            })

    result = {
        "rules": rules[:100],
        "suggestions": suggestions[:20],
        "total_rules": len(rules),
        "total_baskets": len(baskets)
    }

    joblib.dump(result, os.path.join(SAVE_DIR, "recommendations.joblib"))
    print(f"  Found {len(rules)} association rules")
    print(f"  Top {len(suggestions)} product suggestions generated")
    return result


if __name__ == "__main__":
    print("Training recommendation model...")
    train()
    print("Done!")


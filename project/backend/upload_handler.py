"""
Upload Handler — Core logic for CSV parsing, column auto-detection, and data normalization.
Makes SmartMart work with any retail/supermarket CSV dataset.
"""

import pandas as pd
import numpy as np
import os
import json
import re
from datetime import datetime

# ──────────────── COLUMN AUTO-DETECTION ────────────────
# Maps common column name variations to our internal field names.
# First match wins. Case-insensitive, whitespace/underscore normalized.

COLUMN_PATTERNS = {
    # Product fields
    "product_id": [
        r"product.?id", r"prod.?id", r"item.?id", r"sku", r"product.?code",
        r"item.?code", r"upc", r"barcode", r"article.?no",
    ],
    "name": [
        r"product.?name", r"item.?name", r"name", r"description",
        r"product.?desc", r"item.?desc", r"product$", r"item$", r"title",
    ],
    "category": [
        r"category", r"product.?category", r"dept", r"department",
        r"product.?type", r"class", r"sub.?category", r"group",
    ],
    "price": [
        r"price", r"unit.?price", r"selling.?price", r"retail.?price",
        r"sale.?price", r"mrp", r"list.?price",
    ],
    "cost": [
        r"cost", r"cost.?price", r"purchase.?price", r"cogs",
        r"wholesale.?price", r"buy.?price", r"unit.?cost",
    ],
    "supplier": [
        r"supplier", r"vendor", r"manufacturer", r"brand", r"supplier.?name",
    ],
    "shelf_life_days": [
        r"shelf.?life", r"expiry.?days", r"best.?before",
    ],
    "unit": [
        r"unit", r"uom", r"unit.?of.?measure",
    ],

    # Customer fields
    "customer_id": [
        r"customer.?id", r"cust.?id", r"customer.?no", r"buyer.?id",
        r"client.?id", r"member.?id", r"loyalty.?id",
    ],
    "first_name": [
        r"first.?name", r"fname", r"given.?name",
    ],
    "last_name": [
        r"last.?name", r"lname", r"surname", r"family.?name",
    ],
    "customer_name": [
        r"customer.?name", r"cust.?name", r"buyer.?name", r"client.?name", r"full.?name",
    ],
    "age": [
        r"age", r"customer.?age",
    ],
    "gender": [
        r"gender", r"sex",
    ],
    "membership_tier": [
        r"tier", r"membership", r"loyalty.?tier", r"membership.?tier",
        r"level", r"customer.?tier", r"vip",
    ],
    "email": [
        r"email", r"e.?mail", r"customer.?email",
    ],
    "phone": [
        r"phone", r"telephone", r"mobile", r"cell", r"contact",
    ],
    "zip_code": [
        r"zip", r"zip.?code", r"postal", r"postal.?code", r"pincode",
    ],

    # Sales fields
    "sale_id": [
        r"sale.?id", r"transaction.?id", r"order.?id", r"invoice.?id",
        r"receipt.?id", r"txn.?id",
    ],
    "basket_id": [
        r"basket.?id", r"cart.?id", r"order.?id", r"invoice.?id",
        r"receipt.?id", r"transaction.?id", r"session.?id",
    ],
    "quantity": [
        r"quantity", r"qty", r"units", r"amount", r"count",
        r"units.?sold", r"qty.?sold",
    ],
    "total_price": [
        r"total", r"total.?price", r"revenue", r"sale.?amount",
        r"order.?total", r"line.?total", r"extended.?price", r"total.?amount",
        r"net.?amount", r"gross.?amount",
    ],
    "discount": [
        r"discount", r"discount.?pct", r"discount.?amount", r"markdown",
    ],
    "timestamp": [
        r"date", r"timestamp", r"sale.?date", r"transaction.?date",
        r"order.?date", r"purchase.?date", r"invoice.?date", r"datetime",
        r"time", r"created.?at",
    ],
    "payment_method": [
        r"payment", r"payment.?method", r"pay.?type", r"payment.?type",
        r"payment.?mode", r"tender",
    ],

    # Inventory fields
    "current_stock": [
        r"stock", r"current.?stock", r"quantity.?on.?hand", r"qoh",
        r"in.?stock", r"available", r"inventory", r"on.?hand",
    ],
    "max_stock": [
        r"max.?stock", r"capacity", r"max.?capacity", r"max.?qty",
    ],
    "reorder_point": [
        r"reorder", r"reorder.?point", r"reorder.?level", r"min.?stock",
        r"safety.?stock",
    ],
    "last_restock_date": [
        r"last.?restock.?date", r"restock.?date", r"last.?replenishment.?date",
    ],
    "warehouse_location": [
        r"warehouse.?location", r"storage.?location", r"location", r"aisle",
    ],

    # Supplier fields
    "supplier_id": [
        r"supplier.?id", r"vendor.?id", r"supplier.?code",
    ],
    "contact_email": [
        r"contact.?email", r"supplier.?email", r"vendor.?email",
    ],
    "lead_time_days": [
        r"lead.?time", r"lead.?time.?days", r"delivery.?days", r"delivery.?time",
    ],
    "reliability_score": [
        r"reliability", r"reliability.?score", r"rating", r"vendor.?rating",
        r"supplier.?rating", r"performance.?score",
    ],
}


def normalize_col_name(name):
    """Normalize column name for matching: lowercase, replace special chars with underscore."""
    return re.sub(r"[^a-z0-9]", "", name.lower().strip())


def detect_column_mapping(columns):
    """
    Auto-detect column mappings from CSV column names.
    Returns dict: {internal_field: csv_column_name} and list of unmapped columns.
    """
    mapping = {}
    used_cols = set()

    normalized = {col: normalize_col_name(col) for col in columns}

    for field, patterns in COLUMN_PATTERNS.items():
        for pattern in patterns:
            for col, norm in normalized.items():
                if col in used_cols:
                    continue
                if re.fullmatch(pattern, norm):
                    mapping[field] = col
                    used_cols.add(col)
                    break
            if field in mapping:
                break

    unmapped = [c for c in columns if c not in used_cols]
    return mapping, unmapped


def detect_file_type(columns, mapping):
    """Detect if a CSV is sales, products, customers, inventory, or suppliers based on detected columns."""
    # Count how many fields of each type we found
    sales_fields = {"sale_id", "basket_id", "quantity", "total_price", "timestamp", "payment_method", "discount"}
    product_fields = {"product_id", "name", "category", "price", "cost", "supplier", "shelf_life_days", "unit"}
    customer_fields = {"customer_id", "first_name", "last_name", "customer_name", "age", "gender", "membership_tier", "email"}
    inventory_fields = {"current_stock", "max_stock", "reorder_point"}
    supplier_fields = {"supplier_id", "contact_email", "lead_time_days", "reliability_score"}

    mapped_set = set(mapping.keys())

    scores = {
        "sales": len(mapped_set & sales_fields) + (2 if "timestamp" in mapped_set else 0) + (2 if "quantity" in mapped_set else 0),
        "products": len(mapped_set & product_fields) + (2 if "name" in mapped_set else 0),
        "customers": len(mapped_set & customer_fields) + (2 if "customer_name" in mapped_set or "first_name" in mapped_set else 0),
        "inventory": len(mapped_set & inventory_fields) + (2 if "current_stock" in mapped_set else 0),
        "suppliers": len(mapped_set & supplier_fields) + (2 if "supplier_id" in mapped_set else 0) + (2 if "lead_time_days" in mapped_set else 0),
    }

    best = max(scores, key=scores.get)
    if scores[best] < 2:
        return "unknown"
    return best


def preview_csv(file_content, filename="data.csv"):
    """Parse uploaded CSV and return preview + detected mapping."""
    try:
        df = pd.read_csv(file_content, nrows=100)
    except Exception as e:
        return {"error": f"Failed to parse CSV: {str(e)}"}

    columns = df.columns.tolist()
    mapping, unmapped = detect_column_mapping(columns)
    file_type = detect_file_type(columns, mapping)

    # Sample rows for preview
    preview_rows = df.head(10).fillna("").to_dict(orient="records")

    return {
        "filename": filename,
        "total_rows": len(df),
        "columns": columns,
        "detected_mapping": mapping,
        "unmapped_columns": unmapped,
        "detected_type": file_type,
        "preview_rows": preview_rows,
    }


def normalize_sales(df, mapping):
    """Normalize a sales DataFrame to our internal schema."""
    result = pd.DataFrame()

    # Required: some form of product identifier
    if "product_id" in mapping:
        result["product_id"] = df[mapping["product_id"]].astype(str)
    elif "name" in mapping:
        # Use product name as ID if no explicit ID
        result["product_id"] = df[mapping["name"]].astype(str)
    else:
        result["product_id"] = [f"P{i:04d}" for i in range(1, len(df) + 1)]

    # Sale ID
    if "sale_id" in mapping:
        result["sale_id"] = df[mapping["sale_id"]].astype(str)
    else:
        result["sale_id"] = [f"S{i:06d}" for i in range(1, len(df) + 1)]

    # Basket ID
    if "basket_id" in mapping:
        result["basket_id"] = df[mapping["basket_id"]].astype(str)
    elif "sale_id" in mapping:
        result["basket_id"] = df[mapping["sale_id"]].astype(str)
    else:
        result["basket_id"] = result["sale_id"]

    # Customer ID
    if "customer_id" in mapping:
        result["customer_id"] = df[mapping["customer_id"]].astype(str)
    else:
        result["customer_id"] = "UNKNOWN"

    # Quantity
    if "quantity" in mapping:
        result["quantity"] = pd.to_numeric(df[mapping["quantity"]], errors="coerce").fillna(1).astype(int)
    else:
        result["quantity"] = 1

    # Price / total
    if "price" in mapping:
        result["unit_price"] = pd.to_numeric(df[mapping["price"]], errors="coerce").fillna(0)
    elif "total_price" in mapping and "quantity" in mapping:
        qty = pd.to_numeric(df[mapping["quantity"]], errors="coerce").fillna(1)
        total = pd.to_numeric(df[mapping["total_price"]], errors="coerce").fillna(0)
        result["unit_price"] = (total / qty.replace(0, 1)).round(2)
    else:
        result["unit_price"] = 0

    # Discount
    if "discount" in mapping:
        disc = pd.to_numeric(df[mapping["discount"]], errors="coerce").fillna(0)
        if (disc > 1).any():
            disc = disc / 100.0
        result["discount"] = disc.clip(0, 1)
    else:
        result["discount"] = 0.0

    if "total_price" in mapping:
        result["total_price"] = pd.to_numeric(df[mapping["total_price"]], errors="coerce").fillna(0)
    else:
        result["total_price"] = (result["unit_price"] * result["quantity"] * (1 - result["discount"])).round(2)

    # Timestamp
    if "timestamp" in mapping:
        result["timestamp"] = pd.to_datetime(df[mapping["timestamp"]], errors="coerce", format="mixed")
        result["timestamp"] = result["timestamp"].fillna(pd.Timestamp.now())
        result["timestamp"] = result["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Spread timestamps sequentially over the last 90 days to provide historical depth
        import numpy as np
        n_rows = len(df)
        if n_rows > 0:
            now = pd.Timestamp.now()
            start_date = now - pd.Timedelta(days=90)
            times = pd.date_range(start=start_date, end=now, periods=n_rows)
            result["timestamp"] = times.strftime("%Y-%m-%d %H:%M:%S")
        else:
            result["timestamp"] = pd.Series(dtype=str)

    # Payment method
    if "payment_method" in mapping:
        result["payment_method"] = df[mapping["payment_method"]].fillna("Unknown").astype(str)
    else:
        result["payment_method"] = "Unknown"

    return result


def normalize_products(df, mapping):
    """Normalize a products DataFrame to our internal schema."""
    result = pd.DataFrame()

    if "product_id" in mapping:
        result["product_id"] = df[mapping["product_id"]].astype(str)
    else:
        result["product_id"] = [f"P{i:04d}" for i in range(1, len(df) + 1)]

    if "name" in mapping:
        result["name"] = df[mapping["name"]].astype(str)
    else:
        result["name"] = result["product_id"]

    result["category"] = df[mapping["category"]].astype(str) if "category" in mapping else "General"
    result["price"] = pd.to_numeric(df[mapping["price"]], errors="coerce").fillna(0) if "price" in mapping else 0
    result["cost"] = pd.to_numeric(df[mapping["cost"]], errors="coerce").fillna(0) if "cost" in mapping else None
    result["supplier"] = df[mapping["supplier"]].astype(str) if "supplier" in mapping else "Unknown"
    result["shelf_life_days"] = pd.to_numeric(df[mapping["shelf_life_days"]], errors="coerce").fillna(30).astype(int) if "shelf_life_days" in mapping else 30
    result["unit"] = df[mapping["unit"]].astype(str) if "unit" in mapping else "piece"

    return result


def normalize_customers(df, mapping):
    """Normalize a customers DataFrame to our internal schema."""
    result = pd.DataFrame()

    if "customer_id" in mapping:
        result["customer_id"] = df[mapping["customer_id"]].astype(str)
    else:
        result["customer_id"] = [f"C{i:04d}" for i in range(1, len(df) + 1)]

    # Handle combined name vs separate first/last
    if "first_name" in mapping:
        result["first_name"] = df[mapping["first_name"]].fillna("Unknown").astype(str)
    elif "customer_name" in mapping:
        names = df[mapping["customer_name"]].fillna("Unknown").astype(str).str.split(" ", n=1, expand=True)
        result["first_name"] = names[0]
    else:
        result["first_name"] = "Customer"

    if "last_name" in mapping:
        result["last_name"] = df[mapping["last_name"]].fillna("").astype(str)
    elif "customer_name" in mapping:
        names = df[mapping["customer_name"]].fillna("Unknown").astype(str).str.split(" ", n=1, expand=True)
        result["last_name"] = names[1] if 1 in names.columns else ""
    else:
        result["last_name"] = result["customer_id"]

    result["age"] = pd.to_numeric(df[mapping["age"]], errors="coerce").fillna(30).astype(int) if "age" in mapping else 30
    result["gender"] = df[mapping["gender"]].fillna("Other").astype(str) if "gender" in mapping else "Other"
    result["membership_tier"] = df[mapping["membership_tier"]].fillna("Bronze").astype(str) if "membership_tier" in mapping else "Bronze"
    result["email"] = df[mapping["email"]].fillna("").astype(str) if "email" in mapping else ""
    result["phone"] = df[mapping["phone"]].fillna("").astype(str) if "phone" in mapping else ""
    result["zip_code"] = df[mapping["zip_code"]].fillna("").astype(str) if "zip_code" in mapping else ""
    result["loyalty_points"] = 0
    result["preferred_section"] = ""
    result["join_date"] = datetime.now().strftime("%Y-%m-%d")

    return result


def normalize_inventory(df, mapping):
    """Normalize an inventory DataFrame to the database inventory schema."""
    if "product_id" not in mapping:
        raise ValueError("Inventory data requires a product ID column.")

    result = pd.DataFrame()
    result["product_id"] = df[mapping["product_id"]].astype(str)
    for field in ("current_stock", "max_stock", "reorder_point"):
        if field in mapping:
            result[field] = pd.to_numeric(df[mapping[field]], errors="coerce").fillna(0).astype(int)
        else:
            result[field] = 0

    if "last_restock_date" in mapping:
        dates = pd.to_datetime(df[mapping["last_restock_date"]], errors="coerce")
        result["last_restock_date"] = dates.dt.strftime("%Y-%m-%d")
    else:
        result["last_restock_date"] = None

    if "warehouse_location" in mapping:
        result["warehouse_location"] = df[mapping["warehouse_location"]].fillna("").astype(str)
    else:
        result["warehouse_location"] = ""

    return result


def normalize_suppliers(df, mapping):
    """Normalize a suppliers DataFrame to our internal schema."""
    result = pd.DataFrame()

    if "supplier_id" in mapping:
        result["supplier_id"] = df[mapping["supplier_id"]].astype(str)
    else:
        result["supplier_id"] = [f"SUP{i:03d}" for i in range(1, len(df) + 1)]

    if "name" in mapping:
        result["name"] = df[mapping["name"]].astype(str)
    else:
        result["name"] = result["supplier_id"]

    result["contact_email"] = df[mapping["contact_email"]].fillna("").astype(str) if "contact_email" in mapping else ""
    result["lead_time_days"] = pd.to_numeric(df[mapping["lead_time_days"]], errors="coerce").fillna(7).astype(int) if "lead_time_days" in mapping else 7
    if "reliability_score" in mapping:
        rel = pd.to_numeric(df[mapping["reliability_score"]], errors="coerce").fillna(0.5)
        if (rel > 1).any():
            rel = rel / 100.0
        result["reliability_score"] = rel.clip(0, 1)
    else:
        result["reliability_score"] = 0.5

    return result


def extract_products_from_sales(sales_df):
    """Auto-generate products table from sales data when no products CSV provided."""
    agg_dict = {"price": ("unit_price", "median")}
    if "name" in sales_df.columns:
        agg_dict["name"] = ("name", "first")
    if "category" in sales_df.columns:
        agg_dict["category"] = ("category", "first")

    products = sales_df.groupby("product_id").agg(**agg_dict).reset_index()

    if "name" not in products.columns:
        products["name"] = products["product_id"]
    if "category" not in products.columns:
        products["category"] = "General"
    products["cost"] = (products["price"] * 0.55).round(2)
    products["supplier"] = "Unknown"
    products["shelf_life_days"] = 30
    products["unit"] = "piece"

    return products


def extract_customers_from_sales(sales_df):
    """Auto-generate customers table from sales data when no customers CSV provided."""
    customer_ids = sales_df["customer_id"].unique()
    customer_ids = [c for c in customer_ids if c != "UNKNOWN"]

    if len(customer_ids) == 0:
        return pd.DataFrame()

    customers = pd.DataFrame({"customer_id": customer_ids})
    customers["first_name"] = "Customer"
    customers["last_name"] = customers["customer_id"]
    customers["age"] = 30
    customers["gender"] = "Other"
    customers["membership_tier"] = "Bronze"
    customers["email"] = ""
    customers["phone"] = ""
    customers["zip_code"] = ""
    customers["loyalty_points"] = 0
    customers["preferred_section"] = ""
    customers["join_date"] = datetime.now().strftime("%Y-%m-%d")

    return customers


def generate_inventory_from_products(products_df):
    """Auto-generate inventory table."""
    import random
    rng = random.Random(42)
    inventory = pd.DataFrame()
    inventory["product_id"] = products_df["product_id"]
    inventory["current_stock"] = [rng.randint(10, 200) for _ in range(len(products_df))]
    inventory["max_stock"] = [rng.randint(200, 400) for _ in range(len(products_df))]
    inventory["reorder_point"] = [rng.randint(10, 50) for _ in range(len(products_df))]
    inventory["last_restock_date"] = datetime.now().strftime("%Y-%m-%d")
    inventory["warehouse_location"] = [f"Aisle-{rng.randint(1,30)}-Shelf-{chr(65+rng.randint(0,7))}" for _ in range(len(products_df))]
    return inventory


def compute_feature_flags(mapping_info):
    """Determine which features are available based on uploaded data."""
    all_fields = set()
    for info in mapping_info.values():
        all_fields.update(info.get("mapping", {}).keys())

    has_data = len(mapping_info) > 0
    has_sales = "sales" in mapping_info
    has_products = "products" in mapping_info
    has_customers = "customers" in mapping_info
    has_suppliers = "suppliers" in mapping_info
    has_customer_ids = "customer_id" in all_fields and has_sales
    has_cost = "cost" in all_fields
    has_categories = "category" in all_fields
    has_timestamps = "timestamp" in all_fields
    has_payment = "payment_method" in all_fields
    has_basket = "basket_id" in all_fields

    return {
        "has_data": has_data,
        "has_sales": has_sales,
        "has_products": has_products,
        "has_customers": has_customers or has_customer_ids,
        "has_cost": has_cost,
        "has_categories": has_categories,
        "has_timestamps": has_timestamps,
        "has_payment": has_payment,
        "has_basket": has_basket,
        # Derived feature availability
        "enable_dashboard": has_sales,
        "enable_inventory": has_data,
        "enable_sales": has_sales,
        "enable_customers": has_customers or has_customer_ids,
        "enable_suppliers": has_suppliers or (has_products and "supplier" in all_fields),
        "enable_forecast": has_sales,
        "enable_recommendations": has_sales,
        "enable_pricing": has_sales,
        "enable_heatmap": has_sales,
        "enable_anomalies": has_sales,
        "enable_profit": has_sales, # Enable profit overview (chatbot uses fallback cost estimation)
        "enable_demographics": has_customers or has_customer_ids or has_sales,
        "enable_retention": has_sales,
    }

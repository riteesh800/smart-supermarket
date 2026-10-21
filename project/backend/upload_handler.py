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
        r"prod.?code", r"item.?code", r"upc", r"barcode", r"article.?no.*",
        r"article.?num.*", r"stock.?code", r"stockcode", r"item.?no.*",
        r"item.?num.*", r"material.?no.*", r"material.?id", r"asin",
        r"item.?identifier", r"item$",
    ],
    "name": [
        r"product.?name", r"prod.?name", r"item.?name", r"description",
        r"product.?desc.*", r"item.?desc.*", r"title", r"article",
        r"merchandise", r"goods.?name", r"item.?title", r"product$",
        r"name$",
    ],
    "category": [
        r"category", r"product.?category", r"prod.?category", r"dept.*",
        r"department.*", r"product.?type", r"class.*", r"sub.?category.*",
        r"group", r"product.?line", r"prod.?line", r"aisle",
        r"merchandise.?category", r"item.?type", r"family", r"sector",
        r"segment",
    ],
    "price": [
        r"unit.?price", r"unitprice", r"price", r"selling.?price",
        r"retail.?price", r"sale.?price", r"mrp", r"list.?price",
        r"item.?price", r"rate", r"item.?mrp", r"cost.?per.?unit",
    ],
    "cost": [
        r"cost", r"cost.?price", r"unit.?cost", r"purchase.?price",
        r"cogs", r"cost.?of.?goods.*", r"wholesale.?price", r"buy.?price",
        r"base.?price",
    ],
    "supplier": [
        r"supplier", r"vendor", r"manufacturer", r"brand", r"supplier.?name",
        r"vendor.?name", r"brand.?name", r"outlet.?identifier", r"store",
    ],
    "shelf_life_days": [
        r"shelf.?life.*", r"expiry.?days", r"best.?before.*", r"expiration.*",
    ],
    "unit": [
        r"unit", r"uom", r"unit.?of.?measure", r"packaging", r"pack.?size",
    ],

    # Customer fields
    "customer_id": [
        r"customer.?id", r"cust.?id", r"customer.?no.*", r"cust.?no.*",
        r"buyer.?id", r"client.?id", r"member.?id", r"member.?num.*",
        r"loyalty.?id", r"account.?id", r"user.?id", r"client.?no.*",
        r"card.?no.*",
    ],
    "first_name": [
        r"first.?name", r"fname", r"given.?name", r"first",
    ],
    "last_name": [
        r"last.?name", r"lname", r"surname", r"family.?name", r"last",
    ],
    "customer_name": [
        r"customer.?name", r"cust.?name", r"buyer.?name", r"client.?name",
        r"full.?name", r"member.?name", r"customer",
    ],
    "age": [
        r"age", r"customer.?age", r"cust.?age",
    ],
    "gender": [
        r"gender", r"sex",
    ],
    "membership_tier": [
        r"tier", r"membership", r"loyalty.?tier", r"membership.?tier",
        r"membership.?type", r"member.?type", r"level", r"customer.?tier",
        r"customer.?type", r"cust.?type", r"vip", r"customer.?segment",
    ],
    "email": [
        r"email", r"e.?mail", r"customer.?email", r"cust.?email", r"mail",
    ],
    "phone": [
        r"phone.*", r"telephone", r"mobile.*", r"cell", r"contact",
        r"cust.?mobile",
    ],
    "zip_code": [
        r"zip", r"zip.?code", r"postal.*", r"pincode", r"pin.?code",
        r"postcode",
    ],

    # Sales fields
    "sale_id": [
        r"sale.?id", r"transaction.?id", r"trans.?id", r"order.?id",
        r"invoice.?id", r"invoice.?no.*", r"invoiceno", r"receipt.?id",
        r"receipt.?no.*", r"bill.?no.*", r"bill.?id", r"txn.?id",
    ],
    "basket_id": [
        r"basket.?id", r"cart.?id", r"order.?id", r"invoice.?id",
        r"invoice.?no.*", r"invoiceno", r"receipt.?id", r"bill.?no.*",
        r"transaction.?id", r"session.?id", r"trans.?id",
    ],
    "quantity": [
        r"quantity", r"qty", r"units", r"amount.?ordered", r"count",
        r"units.?sold", r"qty.?sold", r"quantity.?ordered", r"qty.?ordered",
        r"volume", r"pieces",
    ],
    "total_price": [
        r"total", r"total.?price", r"total.?amount", r"revenue",
        r"sale.?amount", r"sales", r"order.?total", r"line.?total",
        r"extended.?price", r"net.?amount", r"net.?amt", r"gross.?amount",
        r"gross.?income", r"total.?sales", r"final.?amount", r"bill.?amount",
        r"amount",
    ],
    "discount": [
        r"discount.*", r"disc.*", r"markdown",
    ],
    "timestamp": [
        r"date", r"timestamp", r"sale.?date", r"transaction.?date",
        r"trans.?date", r"order.?date", r"purchase.?date", r"invoice.?date",
        r"invoicedate", r"bill.?date", r"datetime", r"time", r"created.?at",
    ],
    "payment_method": [
        r"payment", r"payment.?method", r"pay.?type", r"payment.?type",
        r"payment.?mode", r"tender", r"tender.?type", r"payment.?channel",
    ],

    # Inventory fields
    "current_stock": [
        r"stock", r"current.?stock", r"quantity.?on.?hand", r"qoh",
        r"in.?stock", r"available", r"inventory", r"on.?hand", r"stock.?qty",
    ],
    "max_stock": [
        r"max.?stock", r"capacity", r"max.?capacity", r"max.?qty",
    ],
    "reorder_point": [
        r"reorder", r"reorder.?point", r"reorder.?level", r"min.?stock",
        r"safety.?stock", r"min.?qty",
    ],
    "last_restock_date": [
        r"last.?restock.?date", r"restock.?date", r"last.?replenishment.?date",
    ],
    "warehouse_location": [
        r"warehouse.?location", r"storage.?location", r"location", r"aisle",
        r"shelf", r"bin",
    ],

    # Supplier fields
    "supplier_id": [
        r"supplier.?id", r"vendor.?id", r"supplier.?code", r"vendor.?code",
    ],
    "contact_email": [
        r"contact.?email", r"supplier.?email", r"vendor.?email",
    ],
    "lead_time_days": [
        r"lead.?time.*", r"delivery.?days", r"delivery.?time",
    ],
    "reliability_score": [
        r"reliability.*", r"rating", r"vendor.?rating", r"supplier.?rating",
        r"performance.?score",
    ],
}


def clean_numeric_series(series, default=0.0):
    """
    Robust numeric conversion: strips currency symbols ($ ₹ € £ Rs INR USD),
    commas, percentages, handles negative numbers in parentheses (12.34) -> -12.34.
    """
    if series is None:
        return pd.Series(dtype=float)
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    s = series.astype(str).str.strip()
    # Handle negative in parentheses: (12.34) -> -12.34
    s = s.str.replace(r'^\((.*)\)$', r'-\1', regex=True)
    # Strip currency symbols and letters: $, ₹, €, £, Rs, INR, USD, commas, spaces
    s = s.str.replace(r'[₹$€£,%\s]|Rs\.?|INR|USD', '', regex=True, flags=re.IGNORECASE)
    # Convert to numeric with fallback
    result = pd.to_numeric(s, errors='coerce')
    if default is not None:
        result = result.fillna(default)
    return result


def normalize_col_name(name):
    """Normalize column name for matching: lowercase, strip all non-alphanumeric chars."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower().strip())


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
    """Normalize a sales DataFrame to our internal schema with robust numeric/date parsing."""
    result = pd.DataFrame()

    # Product identifier: product_id > name > category > synthetic
    if "product_id" in mapping:
        result["product_id"] = df[mapping["product_id"]].astype(str).str.strip()
    elif "name" in mapping:
        result["product_id"] = df[mapping["name"]].astype(str).str.strip()
    elif "category" in mapping:
        result["product_id"] = df[mapping["category"]].astype(str).str.strip()
    else:
        result["product_id"] = [f"P{i:04d}" for i in range(1, len(df) + 1)]

    # Sale ID
    if "sale_id" in mapping:
        result["sale_id"] = df[mapping["sale_id"]].astype(str).str.strip()
    else:
        result["sale_id"] = [f"S{i:06d}" for i in range(1, len(df) + 1)]

    # Basket ID (if not provided, reuse sale_id, or synthetic)
    if "basket_id" in mapping:
        result["basket_id"] = df[mapping["basket_id"]].astype(str).str.strip()
    elif "sale_id" in mapping:
        result["basket_id"] = df[mapping["sale_id"]].astype(str).str.strip()
    else:
        result["basket_id"] = result["sale_id"]

    # Customer ID
    if "customer_id" in mapping:
        result["customer_id"] = df[mapping["customer_id"]].astype(str).str.strip()
    elif "basket_id" in mapping:
        result["customer_id"] = "C-" + df[mapping["basket_id"]].astype(str).str.strip()
    elif "sale_id" in mapping:
        result["customer_id"] = "C-" + df[mapping["sale_id"]].astype(str).str.strip()
    else:
        result["customer_id"] = [f"C{i:05d}" for i in range(1, len(df) + 1)]

    # Quantity (handle negative values/returns cleanly by abs)
    if "quantity" in mapping:
        qty = clean_numeric_series(df[mapping["quantity"]], default=1.0)
        result["quantity"] = qty.abs().clip(lower=1).astype(int)
    else:
        result["quantity"] = 1

    # Discount
    if "discount" in mapping:
        disc = clean_numeric_series(df[mapping["discount"]], default=0.0).abs()
        # Normalize only values > 1 (treating them as percentages like 15 → 0.15)
        disc = disc.where(disc <= 1, disc / 100.0)
        result["discount"] = disc.clip(0, 1)
    else:
        result["discount"] = 0.0

    # Unit price and total price (reconstruct whichever is missing)
    has_price = "price" in mapping
    has_total = "total_price" in mapping

    if has_price:
        result["unit_price"] = clean_numeric_series(df[mapping["price"]], default=0.0).abs().round(2)
    if has_total:
        result["total_price"] = clean_numeric_series(df[mapping["total_price"]], default=0.0).abs().round(2)

    if has_price and not has_total:
        result["total_price"] = (result["unit_price"] * result["quantity"] * (1 - result["discount"])).round(2)
    elif has_total and not has_price:
        result["unit_price"] = (result["total_price"] / result["quantity"].replace(0, 1)).round(2)
    elif not has_price and not has_total:
        result["unit_price"] = 10.0
        result["total_price"] = (result["unit_price"] * result["quantity"]).round(2)

    # Timestamp (flexible parsing + check if separate Time column exists)
    if "timestamp" in mapping:
        date_col = mapping["timestamp"]
        date_series = df[date_col].astype(str).str.strip()

        # Check if a separate Time column exists in original df
        time_cols = [c for c in df.columns if re.search(r"^(time|hour)$", normalize_col_name(c)) and c != date_col]
        if time_cols and date_series.str.len().median() <= 11:
            time_series = df[time_cols[0]].astype(str).str.strip()
            combined = date_series + " " + time_series
            parsed = pd.to_datetime(combined, errors="coerce", format="mixed")
        else:
            parsed = pd.to_datetime(date_series, errors="coerce", format="mixed")

        parsed = parsed.fillna(pd.Timestamp.now())
        result["timestamp"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Spread timestamps sequentially over the last 90 days
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
        result["payment_method"] = df[mapping["payment_method"]].fillna("Unknown").astype(str).str.strip()
    else:
        result["payment_method"] = "Unknown"

    return result


def normalize_products(df, mapping):
    """Normalize a products DataFrame to our internal schema with robust numeric parsing."""
    result = pd.DataFrame()

    if "product_id" in mapping:
        result["product_id"] = df[mapping["product_id"]].astype(str).str.strip()
    elif "name" in mapping:
        result["product_id"] = df[mapping["name"]].astype(str).str.strip()
    else:
        result["product_id"] = [f"P{i:04d}" for i in range(1, len(df) + 1)]

    if "name" in mapping:
        result["name"] = df[mapping["name"]].astype(str).str.strip()
    else:
        result["name"] = result["product_id"]

    result["category"] = df[mapping["category"]].astype(str).str.strip() if "category" in mapping else "General"
    result["price"] = clean_numeric_series(df[mapping["price"]], default=0.0).abs().round(2) if "price" in mapping else 0.0
    result["cost"] = clean_numeric_series(df[mapping["cost"]], default=None).abs().round(2) if "cost" in mapping else None
    result["supplier"] = df[mapping["supplier"]].astype(str).str.strip() if "supplier" in mapping else "Unknown"
    result["shelf_life_days"] = clean_numeric_series(df[mapping["shelf_life_days"]], default=30).astype(int) if "shelf_life_days" in mapping else 30
    result["unit"] = df[mapping["unit"]].astype(str).str.strip() if "unit" in mapping else "piece"

    return result


def normalize_customers(df, mapping):
    """Normalize a customers DataFrame to our internal schema with robust parsing."""
    result = pd.DataFrame()

    if "customer_id" in mapping:
        result["customer_id"] = df[mapping["customer_id"]].astype(str).str.strip()
    else:
        result["customer_id"] = [f"C{i:04d}" for i in range(1, len(df) + 1)]

    # Handle combined name vs separate first/last
    if "first_name" in mapping:
        result["first_name"] = df[mapping["first_name"]].fillna("Unknown").astype(str).str.strip()
    elif "customer_name" in mapping:
        names = df[mapping["customer_name"]].fillna("Unknown").astype(str).str.strip().str.split(" ", n=1, expand=True)
        result["first_name"] = names[0]
    else:
        result["first_name"] = "Customer"

    if "last_name" in mapping:
        result["last_name"] = df[mapping["last_name"]].fillna("").astype(str).str.strip()
    elif "customer_name" in mapping:
        names = df[mapping["customer_name"]].fillna("Unknown").astype(str).str.strip().str.split(" ", n=1, expand=True)
        result["last_name"] = names[1] if 1 in names.columns else ""
    else:
        result["last_name"] = result["customer_id"]

    result["age"] = clean_numeric_series(df[mapping["age"]], default=30).clip(lower=15, upper=100).astype(int) if "age" in mapping else 30
    result["gender"] = df[mapping["gender"]].fillna("Other").astype(str).str.strip() if "gender" in mapping else "Other"
    result["membership_tier"] = df[mapping["membership_tier"]].fillna("Standard").astype(str).str.strip() if "membership_tier" in mapping else "Standard"
    result["email"] = df[mapping["email"]].fillna("").astype(str).str.strip() if "email" in mapping else ""
    result["phone"] = df[mapping["phone"]].fillna("").astype(str).str.strip() if "phone" in mapping else ""
    result["zip_code"] = df[mapping["zip_code"]].fillna("").astype(str).str.strip() if "zip_code" in mapping else ""
    result["loyalty_points"] = 0
    result["preferred_section"] = ""
    result["join_date"] = datetime.now().strftime("%Y-%m-%d")

    return result


def normalize_inventory(df, mapping):
    """Normalize an inventory DataFrame to the database inventory schema."""
    if "product_id" not in mapping:
        raise ValueError("Inventory data requires a product ID column.")

    result = pd.DataFrame()
    result["product_id"] = df[mapping["product_id"]].astype(str).str.strip()
    for field in ("current_stock", "max_stock", "reorder_point"):
        if field in mapping:
            result[field] = clean_numeric_series(df[mapping[field]], default=0).astype(int)
        else:
            result[field] = 0

    if "last_restock_date" in mapping:
        dates = pd.to_datetime(df[mapping["last_restock_date"]], errors="coerce", format="mixed")
        result["last_restock_date"] = dates.dt.strftime("%Y-%m-%d")
    else:
        result["last_restock_date"] = None

    if "warehouse_location" in mapping:
        result["warehouse_location"] = df[mapping["warehouse_location"]].fillna("").astype(str).str.strip()
    else:
        result["warehouse_location"] = ""

    return result


def normalize_suppliers(df, mapping):
    """Normalize a suppliers DataFrame to our internal schema."""
    result = pd.DataFrame()

    if "supplier_id" in mapping:
        result["supplier_id"] = df[mapping["supplier_id"]].astype(str).str.strip()
    else:
        result["supplier_id"] = [f"SUP{i:03d}" for i in range(1, len(df) + 1)]

    if "name" in mapping:
        result["name"] = df[mapping["name"]].astype(str).str.strip()
    else:
        result["name"] = result["supplier_id"]

    result["contact_email"] = df[mapping["contact_email"]].fillna("").astype(str).str.strip() if "contact_email" in mapping else ""
    result["lead_time_days"] = clean_numeric_series(df[mapping["lead_time_days"]], default=7).astype(int) if "lead_time_days" in mapping else 7
    if "reliability_score" in mapping:
        rel = clean_numeric_series(df[mapping["reliability_score"]], default=0.5)
        # Normalize only values > 1 (treating them as percentages like 85 → 0.85)
        rel = rel.where(rel <= 1, rel / 100.0)
        result["reliability_score"] = rel.clip(0, 1).round(2)
    else:
        result["reliability_score"] = 0.5

    return result


def extract_products_from_sales(sales_df, original_df=None, mapping=None):
    """
    Auto-generate products catalog table from sales transactions.
    Preserves actual product names, categories, costs, and suppliers if mapped in the source CSV.
    """
    mapping = mapping or {}
    products = sales_df.groupby("product_id").agg(price=("unit_price", "median")).reset_index()
    products["price"] = products["price"].round(2)

    # Enrich from original CSV if available
    if original_df is not None and not original_df.empty:
        # Determine product key in original_df
        key_col = mapping.get("product_id") or mapping.get("name") or mapping.get("category")
        if key_col and key_col in original_df.columns:
            orig_keys = original_df[key_col].astype(str).str.strip()

            # Name
            if "name" in mapping and mapping["name"] in original_df.columns:
                name_map = dict(zip(orig_keys, original_df[mapping["name"]].astype(str).str.strip()))
                products["name"] = products["product_id"].map(name_map).fillna(products["product_id"])
            else:
                products["name"] = products["product_id"]

            # Category
            if "category" in mapping and mapping["category"] in original_df.columns:
                cat_map = dict(zip(orig_keys, original_df[mapping["category"]].astype(str).str.strip()))
                products["category"] = products["product_id"].map(cat_map).fillna("General")
            else:
                products["category"] = "General"

            # Cost
            if "cost" in mapping and mapping["cost"] in original_df.columns:
                cost_clean = clean_numeric_series(original_df[mapping["cost"]], default=0.0)
                cost_map = dict(zip(orig_keys, cost_clean))
                products["cost"] = products["product_id"].map(cost_map)
                products["cost"] = products["cost"].fillna((products["price"] * 0.55).round(2))
            else:
                products["cost"] = (products["price"] * 0.55).round(2)

            # Supplier
            if "supplier" in mapping and mapping["supplier"] in original_df.columns:
                sup_map = dict(zip(orig_keys, original_df[mapping["supplier"]].astype(str).str.strip()))
                products["supplier"] = products["product_id"].map(sup_map).fillna("Unknown")
            else:
                products["supplier"] = "Unknown"

            # Shelf life days
            if "shelf_life_days" in mapping and mapping["shelf_life_days"] in original_df.columns:
                shelf_clean = clean_numeric_series(original_df[mapping["shelf_life_days"]], default=30).astype(int)
                shelf_map = dict(zip(orig_keys, shelf_clean))
                products["shelf_life_days"] = products["product_id"].map(shelf_map).fillna(30).astype(int)
            else:
                products["shelf_life_days"] = 30

            # Unit
            if "unit" in mapping and mapping["unit"] in original_df.columns:
                unit_map = dict(zip(orig_keys, original_df[mapping["unit"]].astype(str).str.strip()))
                products["unit"] = products["product_id"].map(unit_map).fillna("piece")
            else:
                products["unit"] = "piece"
        else:
            products["name"] = products["product_id"]
            products["category"] = "General"
            products["cost"] = (products["price"] * 0.55).round(2)
            products["supplier"] = "Unknown"
            products["shelf_life_days"] = 30
            products["unit"] = "piece"
    else:
        products["name"] = products["product_id"]
        products["category"] = "General"
        products["cost"] = (products["price"] * 0.55).round(2)
        products["supplier"] = "Unknown"
        products["shelf_life_days"] = 30
        products["unit"] = "piece"

    products["supplier_id"] = None
    return products


def extract_customers_from_sales(sales_df, original_df=None, mapping=None):
    """
    Auto-generate customers table from sales transactions.
    Extracts customer demographics if mapped in source CSV.
    """
    mapping = mapping or {}
    customer_ids = [c for c in sales_df["customer_id"].unique() if c and c != "UNKNOWN"]

    if len(customer_ids) == 0:
        return pd.DataFrame()

    customers = pd.DataFrame({"customer_id": customer_ids})

    if original_df is not None and not original_df.empty:
        if "customer_id" in mapping and mapping["customer_id"] in original_df.columns:
            orig_keys = original_df[mapping["customer_id"]].astype(str).str.strip()
        elif "basket_id" in mapping and mapping["basket_id"] in original_df.columns:
            orig_keys = "C-" + original_df[mapping["basket_id"]].astype(str).str.strip()
        elif "sale_id" in mapping and mapping["sale_id"] in original_df.columns:
            orig_keys = "C-" + original_df[mapping["sale_id"]].astype(str).str.strip()
        else:
            orig_keys = pd.Series([f"C{i:05d}" for i in range(1, len(original_df) + 1)])

        # Name
        if "first_name" in mapping and mapping["first_name"] in original_df.columns:
            fn_map = dict(zip(orig_keys, original_df[mapping["first_name"]].astype(str).str.strip()))
            customers["first_name"] = customers["customer_id"].map(fn_map).fillna("Customer")
        elif "customer_name" in mapping and mapping["customer_name"] in original_df.columns:
            names = original_df[mapping["customer_name"]].astype(str).str.strip().str.split(" ", n=1, expand=True)
            fn_map = dict(zip(orig_keys, names[0]))
            customers["first_name"] = customers["customer_id"].map(fn_map).fillna("Customer")
        else:
            customers["first_name"] = "Customer"

        if "last_name" in mapping and mapping["last_name"] in original_df.columns:
            ln_map = dict(zip(orig_keys, original_df[mapping["last_name"]].astype(str).str.strip()))
            customers["last_name"] = customers["customer_id"].map(ln_map).fillna("")
        elif "customer_name" in mapping and mapping["customer_name"] in original_df.columns:
            names = original_df[mapping["customer_name"]].astype(str).str.strip().str.split(" ", n=1, expand=True)
            ln_map = dict(zip(orig_keys, names[1] if 1 in names.columns else ""))
            customers["last_name"] = customers["customer_id"].map(ln_map).fillna(customers["customer_id"])
        else:
            customers["last_name"] = customers["customer_id"]

        # Gender
        if "gender" in mapping and mapping["gender"] in original_df.columns:
            gen_map = dict(zip(orig_keys, original_df[mapping["gender"]].astype(str).str.strip()))
            customers["gender"] = customers["customer_id"].map(gen_map).fillna("Other")
        else:
            customers["gender"] = "Other"

        # Tier
        if "membership_tier" in mapping and mapping["membership_tier"] in original_df.columns:
            tier_map = dict(zip(orig_keys, original_df[mapping["membership_tier"]].astype(str).str.strip()))
            customers["membership_tier"] = customers["customer_id"].map(tier_map).fillna("Standard")
        else:
            customers["membership_tier"] = "Standard"

        # Age
        if "age" in mapping and mapping["age"] in original_df.columns:
            age_clean = clean_numeric_series(original_df[mapping["age"]], default=30).clip(lower=15, upper=100).astype(int)
            age_map = dict(zip(orig_keys, age_clean))
            customers["age"] = customers["customer_id"].map(age_map).fillna(30).astype(int)
        else:
            customers["age"] = 30

        # Email
        if "email" in mapping and mapping["email"] in original_df.columns:
            em_map = dict(zip(orig_keys, original_df[mapping["email"]].astype(str).str.strip()))
            customers["email"] = customers["customer_id"].map(em_map).fillna("")
        else:
            customers["email"] = ""
    else:
        customers["first_name"] = "Customer"
        customers["last_name"] = customers["customer_id"]
        customers["gender"] = "Other"
        customers["membership_tier"] = "Standard"
        customers["age"] = 30
        customers["email"] = ""

    customers["phone"] = ""
    customers["zip_code"] = ""
    customers["loyalty_points"] = 0
    customers["preferred_section"] = ""
    customers["join_date"] = datetime.now().strftime("%Y-%m-%d")

    return customers


def extract_suppliers_from_products(products_df):
    """Auto-generate suppliers table from products supplier names."""
    if "supplier" not in products_df.columns:
        return pd.DataFrame()

    unique_suppliers = [s for s in products_df["supplier"].unique() if s and s != "Unknown"]
    if not unique_suppliers:
        return pd.DataFrame()

    suppliers = pd.DataFrame({
        "supplier_id": [f"SUP{i:03d}" for i in range(1, len(unique_suppliers) + 1)],
        "name": unique_suppliers,
        "contact_email": [f"{re.sub(r'[^a-z0-9]', '', s.lower())}@supplier.com" for s in unique_suppliers],
        "lead_time_days": 7,
        "reliability_score": 0.85
    })
    return suppliers


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

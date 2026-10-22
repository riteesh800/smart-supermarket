"""
Upload API routes — CSV upload, preview, import, and data management
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import json
import io
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, engine, Base, SessionLocal, DATA_DIR
from auth import require_api_key
from upload_store import (
    generate_upload_id, store_upload, get_upload, remove_upload, clear_all_uploads,
    get_feature_flags as store_get_flags, set_feature_flags as store_set_flags,
    get_mapping_info as store_get_mapping, set_mapping_info as store_set_mapping,
)
from upload_handler import (
    preview_csv, detect_column_mapping, detect_file_type,
    normalize_sales, normalize_products, normalize_customers, normalize_inventory,
    normalize_suppliers,
    extract_products_from_sales, extract_customers_from_sales,
    extract_suppliers_from_products,
    generate_inventory_from_products, compute_feature_flags
)

router = APIRouter(prefix="/api/upload", tags=["upload"])


def get_feature_flags():
    """Get current feature flags, with lazy initialization from DB data."""
    flags = store_get_flags()
    if not flags:
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
            if count and count > 0:
                flags = {
                    "has_data": True, "has_sales": True, "has_products": True,
                    "has_customers": True, "has_cost": True, "has_categories": True,
                    "has_timestamps": True, "has_payment": True, "has_basket": True,
                    "enable_dashboard": True, "enable_inventory": True, "enable_sales": True,
                    "enable_customers": True, "enable_suppliers": True, "enable_forecast": True,
                    "enable_recommendations": True, "enable_pricing": True, "enable_heatmap": True,
                    "enable_anomalies": True, "enable_profit": True, "enable_demographics": True,
                    "enable_retention": True,
                }
            else:
                flags = {"has_data": False}
        except Exception:
            flags = {"has_data": False}
        finally:
            db.close()
        store_set_flags(flags)
    return flags


@router.get("/status")
def get_status():
    """Get current data status and feature flags."""
    flags = get_feature_flags()
    db = SessionLocal()
    try:
        stats = {}
        cols = {}
        has_data = bool(flags and flags.get("has_data"))
        for table in ["products", "customers", "sales", "inventory", "suppliers"]:
            try:
                if has_data:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    stats[table] = count or 0
                else:
                    stats[table] = 0
                col_res = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
                cols[table] = [row[1] for row in col_res] if col_res else []
            except Exception:
                stats[table] = 0
                cols[table] = []
        return {
            "feature_flags": flags,
            "table_counts": stats,
            "mapping_info": store_get_mapping() or {},
            "table_columns": cols,
        }
    finally:
        db.close()


@router.post("/preview")
async def preview_upload(file: UploadFile = File(...)):
    """Upload CSV and get preview + auto-detected column mapping."""
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), nrows=100)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot parse CSV: {str(e)}")

    columns = df.columns.tolist()
    mapping, unmapped = detect_column_mapping(columns)
    file_type = detect_file_type(columns, mapping)

    # Store full content for later import (persistent, with uuid4 ID)
    upload_id = generate_upload_id()
    store_upload(upload_id, content)

    preview_rows = df.head(10).fillna("").to_dict(orient="records")

    # Get total row count
    total_rows = len(pd.read_csv(io.BytesIO(content)))

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "total_rows": total_rows,
        "columns": columns,
        "detected_mapping": mapping,
        "unmapped_columns": unmapped,
        "detected_type": file_type,
        "preview_rows": preview_rows,
    }


def _safe_load_to_table(conn, df, table_name):
    """Load DataFrame into an existing table by deleting rows then appending.
    Preserves the schema/constraints created by Base.metadata.create_all()."""
    conn.execute(text(f"DELETE FROM {table_name}"))
    df.to_sql(table_name, conn, if_exists="append", index=False)


@router.post("/import")
async def import_data(
    upload_id: str = Form(...),
    file_type: str = Form(...),
    mapping_json: str = Form(...)
):
    """Import CSV with confirmed column mapping.
    Uses a single transaction so partial failures roll back entirely."""
    content = get_upload(upload_id)
    if content is None:
        raise HTTPException(status_code=400, detail="Upload expired or not found. Please re-upload.")

    mapping = json.loads(mapping_json)

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot parse CSV: {str(e)}")

    mapping_info = store_get_mapping()

    # Wrap entire import in a single transaction
    try:
        with engine.begin() as conn:
            if file_type == "sales":
                # Validate: require at least one product-identifying column (product_id, name, or category)
                if "product_id" not in mapping and "name" not in mapping and "category" not in mapping:
                    raise HTTPException(
                        status_code=400,
                        detail="Sales data requires at least one product-identifying column mapped (product_id, name, or category)."
                    )

                normalized = normalize_sales(df, mapping)
                _safe_load_to_table(conn, normalized, "sales")

                # Auto-extract and synchronize products if products table is empty or doesn't match the new sales
                products_count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
                existing_pids = set(conn.execute(text("SELECT product_id FROM products")).scalars().all())
                sales_pids = set(normalized["product_id"].unique())
                overlap = len(existing_pids & sales_pids)
                should_sync_products = (products_count == 0) or (overlap < len(sales_pids) * 0.5)

                if should_sync_products:
                    products = extract_products_from_sales(normalized, df, mapping)
                    _safe_load_to_table(conn, products, "products")

                    # Auto-generate matching inventory
                    inventory = generate_inventory_from_products(products)
                    _safe_load_to_table(conn, inventory, "inventory")

                    # If supplier names exist in products, extract suppliers
                    suppliers = extract_suppliers_from_products(products)
                    if not suppliers.empty:
                        _safe_load_to_table(conn, suppliers, "suppliers")
                        name_to_id = dict(zip(suppliers["name"], suppliers["supplier_id"]))
                        products["supplier_id"] = products["supplier"].map(name_to_id)
                        _safe_load_to_table(conn, products, "products")
                        mapping_info["suppliers"] = {"mapping": {"supplier_id": "auto", "name": "auto"}, "rows": len(suppliers)}

                    mapping_info["products"] = {"mapping": {"product_id": "auto", "name": "auto", "category": "auto"}, "rows": len(products)}
                    mapping_info["inventory"] = {"mapping": {"product_id": "auto"}, "rows": len(inventory)}

                # Auto-extract and synchronize customers if empty or doesn't match the new sales
                customers_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0
                existing_cids = set(conn.execute(text("SELECT customer_id FROM customers")).scalars().all())
                sales_cids = set(normalized["customer_id"].unique()) - {"UNKNOWN"}
                cust_overlap = len(existing_cids & sales_cids)
                should_sync_customers = (customers_count == 0) or (len(sales_cids) > 0 and cust_overlap < len(sales_cids) * 0.5)

                if should_sync_customers and len(sales_cids) > 0:
                    customers = extract_customers_from_sales(normalized, df, mapping)
                    if not customers.empty:
                        _safe_load_to_table(conn, customers, "customers")
                        mapping_info["customers"] = {"mapping": {"customer_id": "auto"}, "rows": len(customers)}

                mapping_info["sales"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "products":
                normalized = normalize_products(df, mapping)

                # Map supplier name -> supplier_id for FK linkage
                try:
                    sup_df = pd.read_sql("SELECT supplier_id, name FROM suppliers", conn)
                    if not sup_df.empty:
                        name_to_id = dict(zip(sup_df["name"], sup_df["supplier_id"]))
                        normalized["supplier_id"] = normalized["supplier"].map(name_to_id)
                except Exception:
                    pass

                _safe_load_to_table(conn, normalized, "products")

                # Auto-generate inventory
                inventory = generate_inventory_from_products(normalized)
                _safe_load_to_table(conn, inventory, "inventory")

                mapping_info["products"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "customers":
                normalized = normalize_customers(df, mapping)
                _safe_load_to_table(conn, normalized, "customers")

                mapping_info["customers"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "inventory":
                if "product_id" not in mapping:
                    raise HTTPException(
                        status_code=400,
                        detail="Inventory data requires a product ID column. Please map a column to 'product_id'."
                    )
                normalized = normalize_inventory(df, mapping)

                # Inventory screens join from products, so add minimal product
                # records for inventory IDs that do not have a catalog entry yet.
                existing_product_ids = set(
                    conn.execute(text("SELECT product_id FROM products")).scalars().all()
                )
                missing_product_ids = [
                    product_id for product_id in normalized["product_id"].unique()
                    if product_id not in existing_product_ids
                ]
                if missing_product_ids:
                    placeholders = pd.DataFrame({
                        "product_id": missing_product_ids,
                        "name": missing_product_ids,
                        "category": "General",
                        "price": 0,
                        "cost": None,
                        "supplier": "Unknown",
                        "shelf_life_days": 30,
                        "unit": "piece",
                    })
                    placeholders.to_sql("products", conn, if_exists="append", index=False)

                _safe_load_to_table(conn, normalized, "inventory")

                mapping_info["inventory"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "suppliers":
                normalized = normalize_suppliers(df, mapping)

                # Clear FK references in products before replacing suppliers
                conn.execute(text("UPDATE products SET supplier_id = NULL"))
                _safe_load_to_table(conn, normalized, "suppliers")

                # Re-link all products to the new suppliers
                conn.execute(text("""
                    UPDATE products
                    SET supplier_id = (
                        SELECT s.supplier_id FROM suppliers s
                        WHERE s.name = products.supplier OR s.supplier_id = products.supplier
                        LIMIT 1
                    )
                    WHERE supplier IS NOT NULL
                """))

                mapping_info["suppliers"] = {"mapping": mapping, "rows": len(normalized)}

            else:
                raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")

        # Update persistent state (outside transaction — these are metadata)
        remove_upload(upload_id)
        store_set_mapping(mapping_info)
        flags = compute_feature_flags(mapping_info)
        store_set_flags(flags)

        # Train ML models if we have enough data
        ml_status = None
        db = SessionLocal()
        try:
            sales_count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar() or 0
        finally:
            db.close()

        if sales_count >= 10:
            try:
                ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models")
                result = subprocess.run(
                    [sys.executable, os.path.join(ml_dir, "train_all.py")],
                    capture_output=True, text=True, timeout=120, cwd=ml_dir
                )
                ml_status = "trained" if result.returncode == 0 else f"error: {result.stderr[:200]}"
            except Exception as e:
                ml_status = f"skipped: {str(e)}"

        return {
            "status": "success",
            "file_type": file_type,
            "rows_imported": len(df),
            "feature_flags": flags,
            "ml_status": ml_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


def perform_reset_data():
    """Clear all data and reset to empty state."""
    db = SessionLocal()
    try:
        for table in ["sales", "products", "customers", "inventory", "suppliers"]:
            db.execute(text(f"DELETE FROM {table}"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
    finally:
        db.close()

    # Clear saved ML models from disk
    try:
        ml_saved_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "ml_models", "saved"
        )
        if os.path.exists(ml_saved_dir):
            for f in os.listdir(ml_saved_dir):
                if f.endswith(".joblib"):
                    try:
                        os.remove(os.path.join(ml_saved_dir, f))
                    except Exception:
                        pass
    except Exception:
        pass

    store_set_flags({"has_data": False})
    store_set_mapping({})
    clear_all_uploads()
    return {"status": "reset", "message": "All data cleared and models reset"}


def perform_load_demo():
    """Load the built-in demo dataset and train ML models."""
    data_dir = DATA_DIR

    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM sales"))
            conn.execute(text("DELETE FROM inventory"))
            conn.execute(text("DELETE FROM products"))
            conn.execute(text("DELETE FROM customers"))
            conn.execute(text("DELETE FROM suppliers"))

            sup_path = os.path.join(data_dir, "suppliers.csv")
            name_to_id = {}
            if os.path.exists(sup_path):
                sup_df = pd.read_csv(sup_path)
                _safe_load_to_table(conn, sup_df, "suppliers")
                name_to_id = dict(zip(sup_df["name"], sup_df["supplier_id"]))

            for filename, table in [("products.csv", "products"), ("customers.csv", "customers"),
                                     ("sales.csv", "sales"), ("inventory.csv", "inventory")]:
                path = os.path.join(data_dir, filename)
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    if table == "products" and name_to_id and "supplier" in df.columns:
                        df["supplier_id"] = df["supplier"].map(name_to_id)
                    _safe_load_to_table(conn, df, table)

        flags = {
            "has_data": True, "has_sales": True, "has_products": True,
            "has_customers": True, "has_cost": True, "has_categories": True,
            "has_timestamps": True, "has_payment": True, "has_basket": True,
            "enable_dashboard": True, "enable_inventory": True, "enable_sales": True,
            "enable_customers": True, "enable_suppliers": True, "enable_forecast": True,
            "enable_recommendations": True, "enable_pricing": True, "enable_heatmap": True,
            "enable_anomalies": True, "enable_profit": True, "enable_demographics": True,
            "enable_retention": True,
        }
        store_set_flags(flags)
        store_set_mapping({"sales": {"mapping": {}, "rows": 0}, "products": {"mapping": {}, "rows": 0}, "customers": {"mapping": {}, "rows": 0}})

        ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models")
        try:
            subprocess.run(
                [sys.executable, os.path.join(ml_dir, "train_all.py")],
                capture_output=True, text=True, timeout=120, cwd=ml_dir
            )
        except Exception:
            pass

        return {"status": "success", "message": "Demo data loaded", "feature_flags": flags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")


@router.post("/reset")
def reset_data(_api_key: str = Depends(require_api_key)):
    """Clear all data and reset to empty state. Requires API key."""
    return perform_reset_data()


@router.post("/load-demo")
def load_demo_data(_api_key: str = Depends(require_api_key)):
    """Load the built-in demo dataset. Requires API key."""
    return perform_load_demo()


@router.get("/sample-datasets")
def get_sample_datasets():
    """Return all 5 sample CSV datasets with metadata and preview rows."""
    data_dir = DATA_DIR
    files_meta = [
        {
            "id": "sales",
            "filename": "sales.csv",
            "name": "Sales Transactions",
            "icon": "🛍️",
            "description": "Retail checkout transactions containing baskets, dates, quantities, unit prices, discounts, and payment methods.",
            "category": "Transactions",
        },
        {
            "id": "products",
            "filename": "products.csv",
            "name": "Products Catalog",
            "icon": "📦",
            "description": "Product catalog with categories, retail prices, wholesale unit costs, shelf-life days, and supplier names.",
            "category": "Catalog",
        },
        {
            "id": "customers",
            "filename": "customers.csv",
            "name": "Customer Profiles",
            "icon": "👥",
            "description": "Customer demographics with full names, age, gender, loyalty membership tiers, and email contacts.",
            "category": "Customers",
        },
        {
            "id": "inventory",
            "filename": "inventory.csv",
            "name": "Inventory Levels",
            "icon": "📋",
            "description": "Warehouse stock levels, safety reorder thresholds, max capacities, and warehouse shelf locations.",
            "category": "Inventory",
        },
        {
            "id": "suppliers",
            "filename": "suppliers.csv",
            "name": "Suppliers & Logistics",
            "icon": "🚚",
            "description": "Vendor directory with lead time metrics, supplier contact emails, and reliability performance scores.",
            "category": "Logistics",
        },
    ]

    results = []
    for item in files_meta:
        path = os.path.join(data_dir, item["filename"])
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            size_formatted = f"{file_size / (1024 * 1024):.2f} MB" if file_size >= 1024 * 1024 else f"{file_size / 1024:.1f} KB"
            df = pd.read_csv(path, nrows=15)
            # Efficient line count
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                total_rows = max(0, sum(1 for _ in f) - 1)
            
            results.append({
                **item,
                "total_rows": total_rows,
                "size_bytes": file_size,
                "size_formatted": size_formatted,
                "columns": df.columns.tolist(),
                "preview_rows": df.fillna("").to_dict(orient="records"),
                "download_url": f"/api/upload/sample-datasets/{item['filename']}/download",
            })
    return results


@router.get("/sample-datasets/{filename}/download")
def download_sample_dataset(filename: str):
    """Download one of the 5 sample CSV datasets."""
    allowed = {"sales.csv", "products.csv", "customers.csv", "inventory.csv", "suppliers.csv"}
    if filename not in allowed:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample dataset file not found on disk")
    
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

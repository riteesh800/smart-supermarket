"""
Upload API routes — CSV upload, preview, import, and data management
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
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
        for table in ["products", "customers", "sales", "inventory", "suppliers"]:
            try:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                stats[table] = count or 0
            except Exception:
                stats[table] = 0
        return {"feature_flags": flags, "table_counts": stats}
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

    remove_upload(upload_id)
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
                # Validate: require at least one product identifier
                if "product_id" not in mapping and "name" not in mapping:
                    raise HTTPException(
                        status_code=400,
                        detail="Sales data requires at least one product-identifying column mapped (product_id or name). "
                               "Please map a column to 'product_id' or 'name' in the column mapping."
                    )

                normalized = normalize_sales(df, mapping)
                _safe_load_to_table(conn, normalized, "sales")

                # Auto-extract products if not already loaded
                products_count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
                if products_count == 0:
                    products = extract_products_from_sales(normalized)
                    if "name" in mapping:
                        name_map = dict(zip(df[mapping.get("product_id", mapping.get("name", ""))].astype(str),
                                           df[mapping["name"]].astype(str)))
                        products["name"] = products["product_id"].map(name_map).fillna(products["product_id"])
                    if "category" in mapping:
                        cat_map = dict(zip(df[mapping.get("product_id", mapping.get("name", ""))].astype(str),
                                          df[mapping["category"]].astype(str)))
                        products["category"] = products["product_id"].map(cat_map).fillna("General")
                    _safe_load_to_table(conn, products, "products")

                    # Auto-generate inventory
                    inventory = generate_inventory_from_products(products)
                    _safe_load_to_table(conn, inventory, "inventory")

                # Auto-extract customers if not already loaded
                customers_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0
                if customers_count == 0 and "customer_id" in mapping:
                    customers = extract_customers_from_sales(normalized)
                    if len(customers) > 0:
                        _safe_load_to_table(conn, customers, "customers")

                mapping_info["sales"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "products":
                normalized = normalize_products(df, mapping)
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
                _safe_load_to_table(conn, normalized, "suppliers")

                mapping_info["suppliers"] = {"mapping": mapping, "rows": len(normalized)}

            else:
                raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")

        # Update persistent state (outside transaction — these are metadata)
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


@router.post("/reset")
def reset_data(_api_key: str = Depends(require_api_key)):
    """Clear all data and reset to empty state. Requires API key."""
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


@router.post("/load-demo")
def load_demo_data(_api_key: str = Depends(require_api_key)):
    """Load the built-in demo dataset. Requires API key."""
    data_dir = DATA_DIR

    try:
        # Use a single transaction for all tables
        with engine.begin() as conn:
            for filename, table in [("products.csv", "products"), ("customers.csv", "customers"),
                                     ("sales.csv", "sales"), ("inventory.csv", "inventory"),
                                     ("suppliers.csv", "suppliers")]:
                path = os.path.join(data_dir, filename)
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    _safe_load_to_table(conn, df, table)

        # Set full feature flags
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

        # Train ML
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

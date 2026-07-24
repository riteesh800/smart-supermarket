"""
Upload API routes — CSV upload, preview, import, and data management
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends
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
from upload_handler import (
    preview_csv, detect_column_mapping, detect_file_type,
    normalize_sales, normalize_products, normalize_customers,
    extract_products_from_sales, extract_customers_from_sales,
    generate_inventory_from_products, compute_feature_flags
)

router = APIRouter(prefix="/api/upload", tags=["upload"])

# In-memory store for pending uploads (preview stage)
_pending_uploads = {}

# Feature flags (persistent in memory, saved to DB)
_feature_flags = {}
_mapping_info = {}


def get_feature_flags():
    """Get current feature flags."""
    global _feature_flags
    if not _feature_flags:
        # Check if data exists in DB
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar()
            if count and count > 0:
                # Data exists (e.g. from generate_data.py), assume full features
                _feature_flags = {
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
                _feature_flags = {"has_data": False}
        except Exception:
            _feature_flags = {"has_data": False}
        finally:
            db.close()
    return _feature_flags


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
        return JSONResponse({"error": f"Cannot parse CSV: {str(e)}"}, status_code=400)

    columns = df.columns.tolist()
    mapping, unmapped = detect_column_mapping(columns)
    file_type = detect_file_type(columns, mapping)

    # Store full content for later import
    upload_id = f"upload_{hash(content) % 10**8}"
    _pending_uploads[upload_id] = content

    preview_rows = df.head(10).fillna("").to_dict(orient="records")

    return {
        "upload_id": upload_id,
        "filename": file.filename,
        "total_rows": len(pd.read_csv(io.BytesIO(content))),
        "columns": columns,
        "detected_mapping": mapping,
        "unmapped_columns": unmapped,
        "detected_type": file_type,
        "preview_rows": preview_rows,
    }


@router.post("/import")
async def import_data(
    upload_id: str = Form(...),
    file_type: str = Form(...),
    mapping_json: str = Form(...)
):
    """Import CSV with confirmed column mapping."""
    global _feature_flags, _mapping_info

    if upload_id not in _pending_uploads:
        return JSONResponse({"error": "Upload expired. Please re-upload."}, status_code=400)

    content = _pending_uploads.pop(upload_id)
    mapping = json.loads(mapping_json)

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        return JSONResponse({"error": f"Cannot parse CSV: {str(e)}"}, status_code=400)

    db = SessionLocal()
    try:
        if file_type == "sales":
            normalized = normalize_sales(df, mapping)
            normalized.to_sql("sales", engine, if_exists="replace", index=False)

            # Auto-extract products if not already loaded
            products_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
            if products_count == 0:
                products = extract_products_from_sales(normalized)
                # Try to enrich with product names from original data
                if "name" in mapping:
                    name_map = dict(zip(df[mapping.get("product_id", mapping.get("name", ""))].astype(str),
                                       df[mapping["name"]].astype(str)))
                    products["name"] = products["product_id"].map(name_map).fillna(products["product_id"])
                if "category" in mapping:
                    cat_map = dict(zip(df[mapping.get("product_id", mapping.get("name", ""))].astype(str),
                                      df[mapping["category"]].astype(str)))
                    products["category"] = products["product_id"].map(cat_map).fillna("General")
                products.to_sql("products", engine, if_exists="replace", index=False)

                # Auto-generate inventory
                inventory = generate_inventory_from_products(products)
                inventory.to_sql("inventory", engine, if_exists="replace", index=False)

            # Auto-extract customers if not already loaded
            customers_count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0
            if customers_count == 0 and "customer_id" in mapping:
                customers = extract_customers_from_sales(normalized)
                if len(customers) > 0:
                    customers.to_sql("customers", engine, if_exists="replace", index=False)

            _mapping_info["sales"] = {"mapping": mapping, "rows": len(normalized)}

        elif file_type == "products":
            normalized = normalize_products(df, mapping)
            normalized.to_sql("products", engine, if_exists="replace", index=False)

            # Auto-generate inventory
            inventory = generate_inventory_from_products(normalized)
            inventory.to_sql("inventory", engine, if_exists="replace", index=False)

            _mapping_info["products"] = {"mapping": mapping, "rows": len(normalized)}

        elif file_type == "customers":
            normalized = normalize_customers(df, mapping)
            normalized.to_sql("customers", engine, if_exists="replace", index=False)

            _mapping_info["customers"] = {"mapping": mapping, "rows": len(normalized)}

        else:
            return JSONResponse({"error": f"Unknown file type: {file_type}"}, status_code=400)

        # Update feature flags
        _feature_flags = compute_feature_flags(_mapping_info)

        # Train ML models if we have enough data
        ml_status = None
        sales_count = db.execute(text("SELECT COUNT(*) FROM sales")).scalar() or 0
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
            "feature_flags": _feature_flags,
            "ml_status": ml_status,
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/reset")
def reset_data():
    """Clear all data and reset to empty state."""
    global _feature_flags, _mapping_info, _pending_uploads

    db = SessionLocal()
    try:
        for table in ["sales", "products", "customers", "inventory", "suppliers"]:
            db.execute(text(f"DELETE FROM {table}"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
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

    _feature_flags = {"has_data": False}
    _mapping_info = {}
    _pending_uploads = {}

    return {"status": "reset", "message": "All data cleared and models reset"}



@router.post("/load-demo")
def load_demo_data():
    """Load the built-in demo dataset."""
    global _feature_flags, _mapping_info

    data_dir = DATA_DIR

    try:
        for filename, table in [("products.csv", "products"), ("customers.csv", "customers"),
                                 ("sales.csv", "sales"), ("inventory.csv", "inventory"),
                                 ("suppliers.csv", "suppliers")]:
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                df = pd.read_csv(path)
                df.to_sql(table, engine, if_exists="replace", index=False)

        # Set full feature flags
        _feature_flags = {
            "has_data": True, "has_sales": True, "has_products": True,
            "has_customers": True, "has_cost": True, "has_categories": True,
            "has_timestamps": True, "has_payment": True, "has_basket": True,
            "enable_dashboard": True, "enable_inventory": True, "enable_sales": True,
            "enable_customers": True, "enable_suppliers": True, "enable_forecast": True,
            "enable_recommendations": True, "enable_pricing": True, "enable_heatmap": True,
            "enable_anomalies": True, "enable_profit": True, "enable_demographics": True,
            "enable_retention": True,
        }
        _mapping_info = {"sales": {"mapping": {}, "rows": 0}, "products": {"mapping": {}, "rows": 0}, "customers": {"mapping": {}, "rows": 0}}

        # Train ML
        ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models")
        try:
            subprocess.run(
                [sys.executable, os.path.join(ml_dir, "train_all.py")],
                capture_output=True, text=True, timeout=120, cwd=ml_dir
            )
        except Exception:
            pass

        return {"status": "success", "message": "Demo data loaded", "feature_flags": _feature_flags}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

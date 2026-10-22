"""
Upload API routes — CSV upload, preview, import, and data management
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks, Header
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import json
import io
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, engine, Base, SessionLocal, DATA_DIR, User
from auth import require_api_key, get_current_user, require_current_user, API_KEY
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
from typing import Optional

router = APIRouter(prefix="/api/upload", tags=["upload"])


def get_feature_flags(user_id: Optional[str] = None):
    """Get current feature flags for a user, with lazy initialization from DB data."""
    if not user_id:
        return {"has_data": False}

    flags = store_get_flags(user_id=user_id)
    if not flags or not flags.get("has_data"):
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM sales WHERE user_id = :uid"), {"uid": user_id}).scalar()
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
        store_set_flags(flags, user_id=user_id)
    return flags


@router.get("/status")
def get_status(current_user: Optional[User] = Depends(get_current_user)):
    """Get current data status and feature flags for the authenticated user."""
    if not current_user:
        return {
            "feature_flags": {"has_data": False},
            "table_counts": {"products": 0, "customers": 0, "sales": 0, "inventory": 0, "suppliers": 0},
            "mapping_info": {},
            "table_columns": {},
            "user_id": None,
        }

    uid = current_user.id
    flags = get_feature_flags(user_id=uid)
    db = SessionLocal()
    try:
        stats = {}
        cols = {}
        has_data = bool(flags and flags.get("has_data"))
        for table in ["products", "customers", "sales", "inventory", "suppliers"]:
            try:
                if has_data:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE user_id = :uid"), {"uid": uid}).scalar()
                    stats[table] = count or 0
                else:
                    stats[table] = 0
                col_res = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
                cols[table] = [row[1] for row in col_res if row[1] != "user_id"] if col_res else []
            except Exception:
                stats[table] = 0
                cols[table] = []
        return {
            "feature_flags": flags,
            "table_counts": stats,
            "mapping_info": store_get_mapping(user_id=uid) or {},
            "table_columns": cols,
            "user_id": uid,
        }
    finally:
        db.close()


@router.post("/preview")
async def preview_upload(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Upload CSV and get preview + auto-detected column mapping."""
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), nrows=100)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot parse CSV: {str(e)}")

    columns = df.columns.tolist()
    mapping, unmapped = detect_column_mapping(columns)
    file_type = detect_file_type(columns, mapping)

    # Store full content for later import (persistent, with uuid4 ID and user ownership)
    upload_id = generate_upload_id()
    uid = current_user.id if current_user else None
    store_upload(upload_id, content, user_id=uid)

    preview_rows = df.head(10).fillna("").to_dict(orient="records")
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


def _safe_load_to_table(conn, df, table_name, user_id=""):
    """Load DataFrame into an existing table scoped by user_id.
    Deletes existing rows for this user then appends."""
    if user_id:
        conn.execute(text(f"DELETE FROM {table_name} WHERE user_id = :uid"), {"uid": user_id})
        df = df.copy()
        df["user_id"] = user_id
    else:
        conn.execute(text(f"DELETE FROM {table_name}"))
    df.to_sql(table_name, conn, if_exists="append", index=False)


@router.post("/import")
async def import_data(
    upload_id: str = Form(...),
    file_type: str = Form(...),
    mapping_json: str = Form(...),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Import CSV with confirmed column mapping into user's isolated data space."""
    uid = current_user.id if current_user else "default_owner"
    content = get_upload(upload_id, user_id=uid)
    if content is None:
        raise HTTPException(status_code=400, detail="Upload expired or not found. Please re-upload.")

    mapping = json.loads(mapping_json)

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot parse CSV: {str(e)}")

    mapping_info = store_get_mapping(user_id=uid)

    # Wrap entire import in a single transaction
    try:
        with engine.begin() as conn:
            if file_type == "sales":
                if "product_id" not in mapping and "name" not in mapping and "category" not in mapping:
                    raise HTTPException(
                        status_code=400,
                        detail="Sales data requires at least one product-identifying column mapped (product_id, name, or category)."
                    )

                normalized = normalize_sales(df, mapping)
                _safe_load_to_table(conn, normalized, "sales", user_id=uid)

                # Auto-extract and synchronize products for this user
                products_count = conn.execute(text("SELECT COUNT(*) FROM products WHERE user_id = :uid"), {"uid": uid}).scalar() or 0
                existing_pids = set(conn.execute(text("SELECT product_id FROM products WHERE user_id = :uid"), {"uid": uid}).scalars().all())
                sales_pids = set(normalized["product_id"].unique())
                overlap = len(existing_pids & sales_pids)
                should_sync_products = (products_count == 0) or (overlap < len(sales_pids) * 0.5)

                if should_sync_products:
                    products = extract_products_from_sales(normalized, df, mapping)
                    _safe_load_to_table(conn, products, "products", user_id=uid)

                    inventory = generate_inventory_from_products(products)
                    _safe_load_to_table(conn, inventory, "inventory", user_id=uid)

                    suppliers = extract_suppliers_from_products(products)
                    if not suppliers.empty:
                        _safe_load_to_table(conn, suppliers, "suppliers", user_id=uid)
                        name_to_id = dict(zip(suppliers["name"], suppliers["supplier_id"]))
                        products["supplier_id"] = products["supplier"].map(name_to_id)
                        _safe_load_to_table(conn, products, "products", user_id=uid)
                        mapping_info["suppliers"] = {"mapping": {"supplier_id": "auto", "name": "auto"}, "rows": len(suppliers)}

                    mapping_info["products"] = {"mapping": {"product_id": "auto", "name": "auto", "category": "auto"}, "rows": len(products)}
                    mapping_info["inventory"] = {"mapping": {"product_id": "auto"}, "rows": len(inventory)}

                customers_count = conn.execute(text("SELECT COUNT(*) FROM customers WHERE user_id = :uid"), {"uid": uid}).scalar() or 0
                existing_cids = set(conn.execute(text("SELECT customer_id FROM customers WHERE user_id = :uid"), {"uid": uid}).scalars().all())
                sales_cids = set(normalized["customer_id"].unique()) - {"UNKNOWN"}
                cust_overlap = len(existing_cids & sales_cids)
                should_sync_customers = (customers_count == 0) or (len(sales_cids) > 0 and cust_overlap < len(sales_cids) * 0.5)

                if should_sync_customers and len(sales_cids) > 0:
                    customers = extract_customers_from_sales(normalized, df, mapping)
                    if not customers.empty:
                        _safe_load_to_table(conn, customers, "customers", user_id=uid)
                        mapping_info["customers"] = {"mapping": {"customer_id": "auto"}, "rows": len(customers)}

                mapping_info["sales"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "products":
                normalized = normalize_products(df, mapping)
                try:
                    sup_df = pd.read_sql_query(text("SELECT supplier_id, name FROM suppliers WHERE user_id = :uid"), conn, params={"uid": uid})
                    if not sup_df.empty:
                        name_to_id = dict(zip(sup_df["name"], sup_df["supplier_id"]))
                        normalized["supplier_id"] = normalized["supplier"].map(name_to_id)
                except Exception:
                    pass

                _safe_load_to_table(conn, normalized, "products", user_id=uid)
                inventory = generate_inventory_from_products(normalized)
                _safe_load_to_table(conn, inventory, "inventory", user_id=uid)
                mapping_info["products"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "customers":
                normalized = normalize_customers(df, mapping)
                _safe_load_to_table(conn, normalized, "customers", user_id=uid)
                mapping_info["customers"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "inventory":
                if "product_id" not in mapping:
                    raise HTTPException(
                        status_code=400,
                        detail="Inventory data requires a product ID column. Please map a column to 'product_id'."
                    )
                normalized = normalize_inventory(df, mapping)
                existing_product_ids = set(
                    conn.execute(text("SELECT product_id FROM products WHERE user_id = :uid"), {"uid": uid}).scalars().all()
                )
                missing_product_ids = [
                    product_id for product_id in normalized["product_id"].unique()
                    if product_id not in existing_product_ids
                ]
                if missing_product_ids:
                    placeholders = pd.DataFrame({
                        "user_id": uid,
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

                _safe_load_to_table(conn, normalized, "inventory", user_id=uid)
                mapping_info["inventory"] = {"mapping": mapping, "rows": len(normalized)}

            elif file_type == "suppliers":
                normalized = normalize_suppliers(df, mapping)
                conn.execute(text("UPDATE products SET supplier_id = NULL WHERE user_id = :uid"), {"uid": uid})
                _safe_load_to_table(conn, normalized, "suppliers", user_id=uid)
                conn.execute(text("""
                    UPDATE products
                    SET supplier_id = (
                        SELECT s.supplier_id FROM suppliers s
                        WHERE (s.name = products.supplier OR s.supplier_id = products.supplier)
                          AND s.user_id = products.user_id
                        LIMIT 1
                    )
                    WHERE user_id = :uid AND supplier IS NOT NULL
                """), {"uid": uid})
                mapping_info["suppliers"] = {"mapping": mapping, "rows": len(normalized)}

            else:
                raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")

        # Update persistent user state
        remove_upload(upload_id)
        store_set_mapping(mapping_info, user_id=uid)
        flags = compute_feature_flags(mapping_info)
        store_set_flags(flags, user_id=uid)

        # Train ML models specifically for this user
        ml_status = None
        db = SessionLocal()
        try:
            sales_count = db.execute(text("SELECT COUNT(*) FROM sales WHERE user_id = :uid"), {"uid": uid}).scalar() or 0
        finally:
            db.close()

        if sales_count >= 10:
            try:
                ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models")
                result = subprocess.run(
                    [sys.executable, os.path.join(ml_dir, "train_all.py"), "--user-id", uid],
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


def perform_reset_data(user_id: Optional[str] = None, db: Optional[Session] = None):
    """Clear data and reset to empty state (strictly isolated to user_id if provided)."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        for table in ["sales", "products", "customers", "inventory", "suppliers"]:
            if user_id:
                db.execute(text(f"DELETE FROM {table} WHERE user_id = :uid"), {"uid": str(user_id)})
            else:
                db.execute(text(f"DELETE FROM {table}"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")
    finally:
        if close_db:
            db.close()

    # Clear saved ML models for this user
    try:
        base_ml_saved = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "ml_models", "saved"
        )
        if user_id:
            user_saved = os.path.join(base_ml_saved, str(user_id))
            if os.path.exists(user_saved):
                import shutil
                shutil.rmtree(user_saved, ignore_errors=True)
        else:
            if os.path.exists(base_ml_saved):
                for f in os.listdir(base_ml_saved):
                    full_p = os.path.join(base_ml_saved, f)
                    if os.path.isfile(full_p) and f.endswith(".joblib"):
                        try:
                            os.remove(full_p)
                        except Exception:
                            pass
    except Exception:
        pass

    store_set_flags({"has_data": False}, user_id=user_id)
    store_set_mapping({}, user_id=user_id)
    clear_all_uploads(user_id=user_id)
    return {"status": "reset", "message": "All data cleared and models reset for account"}


def perform_load_demo(user_id: Optional[str] = None, db: Optional[Session] = None):
    """Load the built-in demo dataset and train ML models for a user."""
    data_dir = DATA_DIR
    uid = user_id or "default_owner"
    target_engine = db.get_bind() if db else engine

    try:
        with target_engine.begin() as conn:
            conn.execute(text("DELETE FROM sales WHERE user_id = :uid"), {"uid": uid})
            conn.execute(text("DELETE FROM inventory WHERE user_id = :uid"), {"uid": uid})
            conn.execute(text("DELETE FROM products WHERE user_id = :uid"), {"uid": uid})
            conn.execute(text("DELETE FROM customers WHERE user_id = :uid"), {"uid": uid})
            conn.execute(text("DELETE FROM suppliers WHERE user_id = :uid"), {"uid": uid})

            sup_path = os.path.join(data_dir, "suppliers.csv")
            name_to_id = {}
            if os.path.exists(sup_path):
                sup_df = pd.read_csv(sup_path)
                _safe_load_to_table(conn, sup_df, "suppliers", user_id=uid)
                name_to_id = dict(zip(sup_df["name"], sup_df["supplier_id"]))

            for filename, table in [("products.csv", "products"), ("customers.csv", "customers"),
                                     ("sales.csv", "sales"), ("inventory.csv", "inventory")]:
                path = os.path.join(data_dir, filename)
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    if table == "products" and name_to_id and "supplier" in df.columns:
                        df["supplier_id"] = df["supplier"].map(name_to_id)
                    _safe_load_to_table(conn, df, table, user_id=uid)

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
        store_set_flags(flags, user_id=uid)
        store_set_mapping({"sales": {"mapping": {}, "rows": 0}, "products": {"mapping": {}, "rows": 0}, "customers": {"mapping": {}, "rows": 0}}, user_id=uid)

        ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models")
        try:
            subprocess.run(
                [sys.executable, os.path.join(ml_dir, "train_all.py"), "--user-id", uid],
                capture_output=True, text=True, timeout=120, cwd=ml_dir
            )
        except Exception:
            pass

        return {"status": "success", "message": "Demo data loaded", "feature_flags": flags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo data: {str(e)}")


@router.post("/reset")
def reset_data(
    current_user: Optional[User] = Depends(get_current_user),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Clear data and reset to empty state. Strictly isolated to current user."""
    if current_user:
        return perform_reset_data(user_id=current_user.id, db=db)
    if x_api_key and x_api_key == API_KEY:
        return perform_reset_data(user_id=None, db=db)
    raise HTTPException(status_code=401, detail="Please sign in to clear your data.")


@router.post("/load-demo")
def load_demo_data(
    current_user: Optional[User] = Depends(get_current_user),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """Load the built-in demo dataset for current user."""
    if current_user:
        return perform_load_demo(user_id=current_user.id, db=db)
    if x_api_key and x_api_key == API_KEY:
        return perform_load_demo(user_id=None, db=db)
    raise HTTPException(status_code=401, detail="Please sign in to load demo data.")


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

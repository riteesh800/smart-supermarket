"""
Customer API routes — Strictly Isolated Per User
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys, os, io, csv
import joblib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db, User
from auth import get_current_user, require_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"])

ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml_models", "saved")


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    age: Optional[int] = 30
    gender: Optional[str] = "Other"
    membership_tier: Optional[str] = "Bronze"
    email: Optional[str] = None


@router.get("")
def get_customers(
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    tier: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated customer list for authenticated user with optional search/filter."""
    if not current_user:
        return {"items": [], "total": 0, "page": 1, "pages": 1}

    uid = current_user.id
    query = "SELECT * FROM customers WHERE user_id = :uid"
    params = {"uid": uid}

    page = max(1, page)
    limit = max(1, min(limit, 500))

    if search:
        query += " AND (first_name LIKE :search OR last_name LIKE :search OR customer_id LIKE :search OR email LIKE :search)"
        params["search"] = f"%{search}%"
    if tier:
        query += " AND membership_tier = :tier"
        params["tier"] = tier

    count_sql = "SELECT COUNT(*) FROM customers WHERE user_id = :uid"
    if search:
        count_sql += " AND (first_name LIKE :search OR last_name LIKE :search OR customer_id LIKE :search OR email LIKE :search)"
    if tier:
        count_sql += " AND membership_tier = :tier"
    total = db.execute(text(count_sql), params).scalar() or 0

    query += " ORDER BY customer_id LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = (page - 1) * limit

    result = db.execute(text(query), params)
    rows = result.fetchall()
    columns = result.keys()
    items = [dict(zip(columns, row)) for row in rows]

    pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
    return {"items": items, "total": total, "page": page, "pages": pages}


@router.get("/export")
def export_customers_csv(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all customers for authenticated user as CSV download."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please sign in to export your customer data.")

    result = db.execute(text("""
        SELECT c.customer_id, c.first_name, c.last_name, c.age, c.gender,
               c.membership_tier, c.email, c.phone, c.zip_code,
               c.loyalty_points, c.preferred_section, c.join_date
        FROM customers c
        WHERE c.user_id = :uid
        ORDER BY c.customer_id
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = list(result.keys())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers_export.csv"}
    )


@router.get("/segments")
def get_segments(current_user: Optional[User] = Depends(get_current_user)):
    """Get customer segmentation results for authenticated user."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Please sign in to view customer segmentation.")

    model_path = os.path.join(ML_DIR, current_user.id, "customer_segments.joblib")
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Segmentation model not trained yet. Load data and retrain models first.")
    data = joblib.load(model_path)
    return {
        "segment_counts": data["segment_counts"],
        "cluster_summary": data["cluster_summary"],
        "top_customers": data["top_customers"],
        "total_customers": len(data["segmented_data"])
    }


@router.get("/segments/all")
def get_all_segmented(current_user: Optional[User] = Depends(get_current_user)):
    """Get all customers with segment data for authenticated user."""
    if not current_user:
        return []

    model_path = os.path.join(ML_DIR, current_user.id, "customer_segments.joblib")
    if not os.path.exists(model_path):
        return []
    data = joblib.load(model_path)
    customers = []
    for c in data.get("segmented_data", []):
        customers.append({
            "customer_id": c["customer_id"],
            "name": f"{c.get('first_name', '')} {c.get('last_name', '')}",
            "segment": c.get("segment", "Unknown"),
            "recency": c.get("recency", 0),
            "frequency": c.get("frequency", 0),
            "monetary": round(float(c.get("monetary") or 0), 2),
            "membership_tier": c.get("membership_tier", "Standard")
        })
    return customers


@router.get("/top")
def get_top_customers(current_user: Optional[User] = Depends(get_current_user)):
    """Get top high-value customers for authenticated user."""
    if not current_user:
        return []

    model_path = os.path.join(ML_DIR, current_user.id, "customer_segments.joblib")
    if not os.path.exists(model_path):
        return []
    data = joblib.load(model_path)
    return data.get("top_customers", [])


@router.get("/demographics")
def get_demographics(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer demographic breakdowns for authenticated user."""
    if not current_user:
        return {
            "age_distribution": [],
            "gender_distribution": [],
            "tier_distribution": [],
            "section_preferences": [],
        }

    uid = current_user.id
    age = db.execute(text("""
        SELECT age_group, COUNT(*) as count
        FROM (
            SELECT
                CASE
                    WHEN age IS NULL THEN 'Unknown'
                    WHEN age < 25 THEN '18-24'
                    WHEN age < 35 THEN '25-34'
                    WHEN age < 45 THEN '35-44'
                    WHEN age < 55 THEN '45-54'
                    WHEN age < 65 THEN '55-64'
                    ELSE '65+'
                END as age_group
            FROM customers
            WHERE user_id = :uid
        ) sub
        GROUP BY age_group
        ORDER BY
            CASE
                WHEN age_group = '18-24' THEN 1
                WHEN age_group = '25-34' THEN 2
                WHEN age_group = '35-44' THEN 3
                WHEN age_group = '45-54' THEN 4
                WHEN age_group = '55-64' THEN 5
                WHEN age_group = '65+' THEN 6
                ELSE 7
            END
    """), {"uid": uid})
    age_data = [dict(zip(["age_group", "count"], row)) for row in age.fetchall()]

    gender = db.execute(text("""
        SELECT gender, COUNT(*) as count FROM customers WHERE user_id = :uid GROUP BY gender ORDER BY count DESC
    """), {"uid": uid})
    gender_data = [dict(zip(["gender", "count"], row)) for row in gender.fetchall()]

    tier = db.execute(text("""
        SELECT membership_tier, COUNT(*) as count FROM customers WHERE user_id = :uid GROUP BY membership_tier
        ORDER BY CASE membership_tier WHEN 'Platinum' THEN 1 WHEN 'Gold' THEN 2 WHEN 'Silver' THEN 3 ELSE 4 END
    """), {"uid": uid})
    tier_data = [dict(zip(["tier", "count"], row)) for row in tier.fetchall()]

    sections = db.execute(text("""
        SELECT preferred_section, COUNT(*) as count FROM customers
        WHERE user_id = :uid AND preferred_section IS NOT NULL
        GROUP BY preferred_section ORDER BY count DESC
    """), {"uid": uid})
    section_data = [dict(zip(["section", "count"], row)) for row in sections.fetchall()]

    return {
        "age_distribution": age_data,
        "gender_distribution": gender_data,
        "tier_distribution": tier_data,
        "section_preferences": section_data,
    }


@router.get("/retention")
def get_retention(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly active customer counts for authenticated user."""
    if not current_user:
        return []

    result = db.execute(text("""
        SELECT SUBSTR(s.timestamp, 1, 7) as month,
               COUNT(DISTINCT s.customer_id) as active_customers,
               COUNT(DISTINCT s.basket_id) as total_baskets,
               SUM(s.total_price) as total_spend
        FROM sales s
        WHERE s.user_id = :uid
        GROUP BY month
        ORDER BY month
    """), {"uid": current_user.id})
    rows = result.fetchall()
    columns = result.keys()
    return [dict(zip(columns, row)) for row in rows]


@router.post("")
def add_customer(
    customer: CustomerCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Add a new customer for authenticated user."""
    uid = current_user.id
    existing_ids = set(db.execute(text("SELECT customer_id FROM customers WHERE user_id = :uid"), {"uid": uid}).scalars().all())
    c_nums = [int(cid[1:]) for cid in existing_ids if cid.startswith("C") and cid[1:].isdigit()]
    if c_nums:
        next_num = max(c_nums) + 1
    else:
        nums = [int(cid) for cid in existing_ids if cid.isdigit()]
        next_num = max(nums) + 1 if nums else len(existing_ids) + 1
    new_id = f"C{next_num:04d}"
    while new_id in existing_ids:
        next_num += 1
        new_id = f"C{next_num:04d}"

    email = customer.email or f"customer{next_num}@email.com"
    today_str = datetime.now().strftime("%Y-%m-%d")

    db.execute(text("""
        INSERT INTO customers (user_id, customer_id, first_name, last_name, age, gender, membership_tier, email, join_date)
        VALUES (:uid, :cid, :fname, :lname, :age, :gender, :tier, :email, :join_date)
    """), {
        "uid": uid,
        "cid": new_id, "fname": customer.first_name, "lname": customer.last_name,
        "age": customer.age, "gender": customer.gender, "tier": customer.membership_tier,
        "email": email, "join_date": today_str
    })
    db.commit()
    return {"message": "Customer added", "customer_id": new_id}

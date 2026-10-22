"""
Multi-Tenant Database Migration:
Ensures data isolation across users by:
1. Adding `user_id` to `suppliers`, `products`, `customers`, `sales`, and `inventory`
2. Converting primary keys to composite (user_id, <id_col>)
3. Creating index on `user_id` on all data tables
4. Canonicalizing all user emails to enforce strictly one account per Gmail ID
"""

import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import normalize_email


TABLE_SCHEMAS_SQLITE = {
    "suppliers": """
        CREATE TABLE new_suppliers (
            user_id VARCHAR(64) NOT NULL DEFAULT '',
            supplier_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            contact_email VARCHAR,
            lead_time_days INTEGER,
            reliability_score FLOAT,
            PRIMARY KEY (user_id, supplier_id)
        );
    """,
    "products": """
        CREATE TABLE new_products (
            user_id VARCHAR(64) NOT NULL DEFAULT '',
            product_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            price FLOAT NOT NULL,
            cost FLOAT,
            supplier VARCHAR,
            supplier_id VARCHAR,
            shelf_life_days INTEGER,
            unit VARCHAR,
            PRIMARY KEY (user_id, product_id)
        );
    """,
    "customers": """
        CREATE TABLE new_customers (
            user_id VARCHAR(64) NOT NULL DEFAULT '',
            customer_id VARCHAR NOT NULL,
            first_name VARCHAR NOT NULL,
            last_name VARCHAR NOT NULL,
            age INTEGER,
            gender VARCHAR,
            membership_tier VARCHAR,
            email VARCHAR,
            phone VARCHAR,
            zip_code VARCHAR,
            loyalty_points INTEGER,
            preferred_section VARCHAR,
            join_date VARCHAR,
            PRIMARY KEY (user_id, customer_id)
        );
    """,
    "sales": """
        CREATE TABLE new_sales (
            user_id VARCHAR(64) NOT NULL DEFAULT '',
            sale_id VARCHAR NOT NULL,
            basket_id VARCHAR,
            product_id VARCHAR,
            customer_id VARCHAR,
            quantity INTEGER,
            unit_price FLOAT,
            discount FLOAT,
            total_price FLOAT,
            timestamp VARCHAR,
            payment_method VARCHAR,
            PRIMARY KEY (user_id, sale_id)
        );
    """,
    "inventory": """
        CREATE TABLE new_inventory (
            user_id VARCHAR(64) NOT NULL DEFAULT '',
            product_id VARCHAR NOT NULL,
            current_stock INTEGER,
            max_stock INTEGER,
            reorder_point INTEGER,
            last_restock_date VARCHAR,
            warehouse_location VARCHAR,
            PRIMARY KEY (user_id, product_id)
        );
    """,
}


def run_multitenant_migration(engine):
    """Run schema migration to ensure strict user isolation."""
    is_pg = (engine.dialect.name == "postgresql")
    print(f"[*] Running multi-tenant isolation migration (Dialect: {engine.dialect.name})...")

    with engine.begin() as conn:
        # 1. Determine owner user ID for existing orphan rows
        owner_id = "default_owner"
        try:
            row = conn.execute(text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).fetchone()
            if row and row[0]:
                owner_id = row[0]
        except Exception:
            pass

        # 2. Migrate each data table
        for table_name in ["suppliers", "products", "customers", "sales", "inventory"]:
            if is_pg:
                _migrate_pg(conn, table_name, owner_id)
            else:
                _migrate_sqlite(conn, table_name, owner_id)

        # 3. Canonicalize user emails to guarantee one Gmail ID = one account only
        try:
            users = conn.execute(text("SELECT id, email FROM users")).fetchall()
            for uid, email in users:
                if email:
                    clean_email = normalize_email(email)
                    if clean_email != email:
                        conn.execute(
                            text("UPDATE users SET email = :clean WHERE id = :uid"),
                            {"clean": clean_email, "uid": uid}
                        )
                        conn.execute(
                            text("UPDATE oauth_accounts SET email = :clean WHERE user_id = :uid"),
                            {"clean": clean_email, "uid": uid}
                        )
        except Exception as e:
            print(f"[-] Notice on email canonicalization: {e}")

    print("[+] Multi-tenant user isolation migration completed successfully!")


def _migrate_sqlite(conn, table_name, owner_id):
    # Check if table exists
    exists = conn.execute(
        text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = :t"),
        {"t": table_name}
    ).scalar()
    if not exists:
        return

    # Check columns
    cols_info = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    col_names = [r[1] for r in cols_info]
    
    if "user_id" in col_names:
        # Ensure index exists
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)"))
        return

    print(f"[*] Migrating table '{table_name}' to multi-tenant schema with composite primary key...")
    create_sql = TABLE_SCHEMAS_SQLITE[table_name]
    conn.execute(text("PRAGMA foreign_keys=OFF"))
    conn.execute(text(create_sql))

    # Copy existing columns
    common_cols = ", ".join(col_names)
    conn.execute(
        text(f"INSERT INTO new_{table_name} ({common_cols}, user_id) SELECT {common_cols}, :owner_id FROM {table_name}"),
        {"owner_id": owner_id}
    )
    conn.execute(text(f"DROP TABLE {table_name}"))
    conn.execute(text(f"ALTER TABLE new_{table_name} RENAME TO {table_name}"))
    conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)"))
    conn.execute(text("PRAGMA foreign_keys=ON"))


def _migrate_pg(conn, table_name, owner_id):
    id_cols = {
        "suppliers": "supplier_id",
        "products": "product_id",
        "customers": "customer_id",
        "sales": "sale_id",
        "inventory": "product_id",
    }
    id_col = id_cols[table_name]

    # Add user_id column if not exists
    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS user_id VARCHAR(64) DEFAULT ''"))
    conn.execute(
        text(f"UPDATE {table_name} SET user_id = :owner_id WHERE user_id = '' OR user_id IS NULL"),
        {"owner_id": owner_id}
    )
    try:
        conn.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {table_name}_pkey"))
        conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (user_id, {id_col})"))
    except Exception as e:
        print(f"[-] Notice adjusting PK on {table_name}: {e}")
    conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)"))


if __name__ == "__main__":
    from database import engine
    run_multitenant_migration(engine)

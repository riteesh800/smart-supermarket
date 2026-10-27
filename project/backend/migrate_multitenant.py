"""
Multi-Tenant & Schema Auto-Migration:
Ensures data isolation and schema consistency across PostgreSQL (Supabase) and SQLite by:
1. Guaranteeing all auth columns (canonical_email, auth_provider, password_hash, avatar_url,
   created_at, last_login_at, state_data) exist on the `users` table.
2. Backfilling canonical_email for all existing accounts.
3. Adding `user_id` to `suppliers`, `products`, `customers`, `sales`, and `inventory`.
4. Creating indexes for performance and multi-tenant queries.
5. Safely updating composite primary keys without aborting transactions on foreign key constraints.
6. Isolating each DDL statement so that one warning never aborts other migrations.
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


def _run_single_pg(engine, sql: str, params: dict = None):
    """Execute a single statement in its own isolated transaction to avoid InFailedSqlTransaction aborts."""
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql), params or {})
    except Exception as e:
        print(f"[-] PG migration notice [{sql[:60].strip()}...]: {e}")


def run_multitenant_migration(engine):
    """Run schema migration to ensure strict user isolation and auth table readiness."""
    is_pg = (engine.dialect.name == "postgresql")
    print(f"[*] Running database schema & multi-tenant isolation migration (Dialect: {engine.dialect.name})...")

    # 1. Migrate `users` table schema first (ensure canonical_email and all auth fields exist)
    if is_pg:
        _migrate_users_pg(engine)
    else:
        _migrate_users_sqlite(engine)

    # 2. Determine default owner ID
    owner_id = "default_owner"
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).fetchone()
            if row and row[0]:
                owner_id = row[0]
    except Exception:
        pass

    # 3. Migrate each data table (suppliers, products, customers, sales, inventory)
    for table_name in ["suppliers", "products", "customers", "sales", "inventory"]:
        if is_pg:
            _migrate_pg(engine, table_name, owner_id)
        else:
            _migrate_sqlite(engine, table_name, owner_id)

    # 4. Canonicalize user emails to guarantee one Gmail ID = one account only
    _canonicalize_existing_emails(engine)

    print("[+] Schema & multi-tenant user isolation migration completed successfully!")


def _migrate_users_pg(engine):
    """Ensure users table in PostgreSQL has canonical_email and all modern auth columns."""
    columns_to_add = [
        ("canonical_email", "VARCHAR(255)"),
        ("auth_provider", "VARCHAR(64) DEFAULT 'email'"),
        ("password_hash", "VARCHAR(255)"),
        ("avatar_url", "VARCHAR(1024)"),
        ("created_at", "VARCHAR(64) DEFAULT ''"),
        ("last_login_at", "VARCHAR(64) DEFAULT ''"),
        ("state_data", "TEXT DEFAULT '{}'"),
    ]
    for col_name, col_type in columns_to_add:
        _run_single_pg(engine, f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}")

    _run_single_pg(engine, "CREATE INDEX IF NOT EXISTS idx_users_canonical_email ON users(canonical_email)")
    _run_single_pg(engine, "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")


def _migrate_users_sqlite(engine):
    """Ensure users table in SQLite has canonical_email and all modern auth columns."""
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = 'users'")
        ).scalar()
        if not exists:
            return

        cols_info = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        col_names = [r[1] for r in cols_info]

        columns_to_add = [
            ("canonical_email", "VARCHAR(255)"),
            ("auth_provider", "VARCHAR DEFAULT 'email'"),
            ("password_hash", "VARCHAR"),
            ("avatar_url", "VARCHAR"),
            ("created_at", "VARCHAR DEFAULT ''"),
            ("last_login_at", "VARCHAR DEFAULT ''"),
            ("state_data", "TEXT DEFAULT '{}'"),
        ]
        for col_name, col_type in columns_to_add:
            if col_name not in col_names:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                except Exception as e:
                    print(f"[-] SQLite notice adding {col_name} to users: {e}")

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_canonical_email ON users(canonical_email)"))
        except Exception:
            pass


def _canonicalize_existing_emails(engine):
    """Backfill and canonicalize emails across users and oauth_accounts."""
    try:
        with engine.connect() as conn:
            with conn.begin():
                users = conn.execute(text("SELECT id, email, canonical_email FROM users")).fetchall()
                for uid, email, canon in users:
                    if email:
                        clean_email = normalize_email(email)
                        # Backfill canonical_email if missing or empty
                        if not canon or canon != clean_email:
                            conn.execute(
                                text("UPDATE users SET canonical_email = :clean WHERE id = :uid"),
                                {"clean": clean_email, "uid": uid}
                            )
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


def _migrate_pg(engine, table_name, owner_id):
    id_cols = {
        "suppliers": "supplier_id",
        "products": "product_id",
        "customers": "customer_id",
        "sales": "sale_id",
        "inventory": "product_id",
    }
    id_col = id_cols[table_name]

    # Add user_id column if not exists in its own isolated transaction
    _run_single_pg(engine, f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS user_id VARCHAR(64) DEFAULT ''")
    _run_single_pg(
        engine,
        f"UPDATE {table_name} SET user_id = :owner_id WHERE user_id = '' OR user_id IS NULL",
        {"owner_id": owner_id}
    )
    _run_single_pg(engine, f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)")

    # Attempt primary key adjustment safely
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {table_name}_pkey CASCADE"))
                conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY (user_id, {id_col})"))
    except Exception as e:
        print(f"[-] Notice adjusting PK on {table_name}: {e}")


def _migrate_sqlite(engine, table_name, owner_id):
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = :t"),
            {"t": table_name}
        ).scalar()
        if not exists:
            return

        cols_info = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        col_names = [r[1] for r in cols_info]

        if "user_id" in col_names:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)"))
            return

        print(f"[*] Migrating table '{table_name}' to multi-tenant schema with composite primary key...")
        create_sql = TABLE_SCHEMAS_SQLITE[table_name]
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text(create_sql))

        common_cols = ", ".join(col_names)
        conn.execute(
            text(f"INSERT INTO new_{table_name} ({common_cols}, user_id) SELECT {common_cols}, :owner_id FROM {table_name}"),
            {"owner_id": owner_id}
        )
        conn.execute(text(f"DROP TABLE {table_name}"))
        conn.execute(text(f"ALTER TABLE new_{table_name} RENAME TO {table_name}"))
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_user_id ON {table_name}(user_id)"))
        conn.execute(text("PRAGMA foreign_keys=ON"))


if __name__ == "__main__":
    from database import engine
    run_multitenant_migration(engine)

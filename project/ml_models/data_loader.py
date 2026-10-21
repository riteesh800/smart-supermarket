"""
Shared Data Loader for ML Models.
Connects dynamically to PostgreSQL (Supabase / DATABASE_URL), local SQLite, or CSV fallback.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_table(table_name: str, base_dir: str = None) -> pd.DataFrame:
    """Load a table from PostgreSQL (Supabase), SQLite, or fallback CSV."""
    if base_dir is None:
        base_dir = BASE_DIR

    # 1. Try PostgreSQL (e.g. Supabase via DATABASE_URL)
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        clean = db_url.strip()
        if clean.startswith("postgres://"):
            clean = clean.replace("postgres://", "postgresql://", 1)

        candidates = []
        if not clean.startswith("postgresql+"):
            candidates.append(clean.replace("postgresql://", "postgresql+psycopg2://", 1))
            candidates.append(clean.replace("postgresql://", "postgresql+psycopg://", 1))
        candidates.append(clean)

        for target in candidates:
            try:
                engine = create_engine(target, pool_pre_ping=True)
                with engine.connect() as conn:
                    df = pd.read_sql_query(text(f"SELECT * FROM {table_name}"), conn)
                    if not df.empty:
                        return df
                break
            except Exception as e:
                pass


    # 2. Try SQLite
    db_path = os.path.join(os.path.dirname(base_dir), "backend", "supermarket.db")
    if os.path.exists(db_path):
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone()[0] > 0:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                if len(df) > 0:
                    conn.close()
                    return df
            conn.close()
        except Exception as e:
            print(f"Notice: Could not load '{table_name}' from SQLite ({e}). Falling back...")

    # 3. Fallback to CSV
    data_dir = os.path.join(os.path.dirname(base_dir), "data")
    csv_path = os.path.join(data_dir, f"{table_name}.csv")
    if os.path.exists(csv_path):
        try:
            return pd.read_csv(csv_path)
        except Exception as e:
            print(f"Notice: Could not read CSV fallback '{csv_path}': {e}")

    return pd.DataFrame()

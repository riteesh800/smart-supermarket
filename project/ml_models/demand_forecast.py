"""
Demand Forecasting using Exponential Smoothing (Holt-Winters) + SARIMAX fallback
Predicts future demand per product category with trend and weekly seasonality
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
import joblib
import os
import sqlite3
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
SAVE_DIR = os.path.join(BASE_DIR, "saved")
os.makedirs(SAVE_DIR, exist_ok=True)


def load_table(table_name):
    db_path = os.path.join(os.path.dirname(BASE_DIR), "backend", "supermarket.db")
    if os.path.exists(db_path):
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
            print(f"Error loading {table_name} from database: {e}")
    # Fallback to CSV
    csv_path = os.path.join(DATA_DIR, f"{table_name}.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()


def load_sales():
    sales = load_table("sales")
    products = load_table("products")

    if sales.empty or "product_id" not in sales.columns:
        return pd.DataFrame(columns=["product_id", "category", "timestamp", "quantity", "total_price", "date"])

    # Cast product_id to string to avoid merge mismatch type issues
    sales["product_id"] = sales["product_id"].astype(str)

    if products.empty or "product_id" not in products.columns or "category" not in products.columns:
        # Default category to 'General' if no category information is available
        sales["category"] = "General"
        merged = sales
    else:
        products = products.copy()
        products["product_id"] = products["product_id"].astype(str)
        merged = sales.merge(products[["product_id", "category"]], on="product_id", how="left")
        merged["category"] = merged["category"].fillna("General")

    merged["date"] = pd.to_datetime(merged["timestamp"]).dt.date
    # Ensure quantity is numeric
    if "quantity" in merged.columns:
        merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce").fillna(0)
    return merged


def build_daily_demand(sales_df, category):
    cat_sales = sales_df[sales_df["category"] == category].copy()
    if cat_sales.empty:
        # Return a dummy dataframe with 30 days of 0s
        dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=30, freq="D")
        daily = pd.DataFrame({"quantity": [0.0] * 30}, index=dates)
        daily.index.name = "date"
        daily.index.freq = "D"
        return daily

    if "date" not in cat_sales.columns:
        if "timestamp" in cat_sales.columns:
            cat_sales["date"] = pd.to_datetime(cat_sales["timestamp"]).dt.strftime("%Y-%m-%d")
        else:
            cat_sales["date"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    daily = cat_sales.groupby("date")["quantity"].sum().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.set_index("date").sort_index()

    min_date = daily.index.min()
    max_date = daily.index.max()
    if pd.isnull(min_date) or pd.isnull(max_date):
        # Fallback to dummy
        dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=30, freq="D")
        daily = pd.DataFrame({"quantity": [0.0] * 30}, index=dates)
        daily.index.name = "date"
        daily.index.freq = "D"
        return daily

    # Fill missing dates with 0
    full_range = pd.date_range(min_date, max_date, freq="D")
    daily = daily.reindex(full_range, fill_value=0)
    daily.index.name = "date"
    daily.index.freq = "D"
    return daily



def train_holt_winters(daily_demand, seasonal_periods=7):
    """Holt-Winters with weekly seasonality — captures real patterns."""
    n = len(daily_demand)

    # Need at least 2 full seasonal cycles for multiplicative
    if n >= seasonal_periods * 2:
        # Ensure no zeros for multiplicative (add small offset)
        vals = daily_demand["quantity"].copy()
        vals = vals.clip(lower=0.1)

        try:
            model = ExponentialSmoothing(
                vals,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
            fitted = model.fit(optimized=True)
            return fitted, "holt_winters"
        except Exception:
            pass

    # Fallback: additive trend only (no seasonality)
    try:
        model = ExponentialSmoothing(
            daily_demand["quantity"].clip(lower=0),
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)
        return fitted, "holt_linear"
    except Exception:
        return None, None


def train_sarimax(daily_demand):
    """SARIMAX with weekly seasonality as fallback."""
    try:
        model = SARIMAX(
            daily_demand["quantity"],
            order=(1, 1, 1),
            seasonal_order=(1, 0, 1, 7),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted = model.fit(disp=False, maxiter=100)
        return fitted, "sarimax"
    except Exception:
        return None, None


def forecast_model(fitted_model, model_type, steps=30, start_date=None):
    """Generate forecast from fitted model continuous from historical data end date."""
    fc = fitted_model.forecast(steps=steps)
    if start_date is None:
        start_date = pd.Timestamp.now().normalize()
    future_dates = pd.date_range(
        start=start_date,
        periods=steps,
        freq="D"
    )
    predicted = np.maximum(np.array(fc).flatten(), 0).round(1)

    forecast_df = pd.DataFrame({
        "date": future_dates.strftime("%Y-%m-%d"),
        "predicted_demand": predicted
    })
    return forecast_df


def fallback_seasonal_naive(daily_demand, steps=30, start_date=None):
    """Seasonal naive: repeat last week's pattern. Much better than flat average."""
    vals = daily_demand["quantity"].values
    period = 7
    last_week = vals[-period:] if len(vals) >= period else vals

    predicted = []
    for i in range(steps):
        predicted.append(float(max(0, last_week[i % len(last_week)])))

    # Add some random noise proportional to the data variance to look realistic
    std = float(np.std(vals[-30:])) if len(vals) >= 30 else float(np.std(vals))
    noise = np.random.normal(0, std * 0.15, steps) if std > 0 else np.zeros(steps)
    predicted = np.maximum(np.round(np.array(predicted) + noise, 1), 0)

    if start_date is None:
        max_d = daily_demand.index.max() if not daily_demand.empty else None
        start_date = (max_d + pd.Timedelta(days=1)).normalize() if max_d is not None and not pd.isnull(max_d) else pd.Timestamp.now().normalize()

    future_dates = pd.date_range(start=start_date, periods=steps, freq="D")
    return pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in future_dates],
        "predicted_demand": predicted.tolist()
    })


def train_all_categories():
    sales = load_sales()
    if sales.empty or "category" not in sales.columns:
        print("  No sales data available for demand forecasting.")
        results = {}
        joblib.dump(results, os.path.join(SAVE_DIR, "demand_forecasts.joblib"))
        return results

    categories = [c for c in sales["category"].unique() if pd.notnull(c)]
    results = {}

    for cat in categories:
        daily = build_daily_demand(sales, cat)
        n_days = len(daily)
        print(f"  Training forecast for {cat} ({n_days} days of data)...")

        max_d = daily.index.max() if not daily.empty else None
        cat_start_date = (max_d + pd.Timedelta(days=1)).normalize() if max_d is not None and not pd.isnull(max_d) else pd.Timestamp.now().normalize()

        fc_df = None
        model_used = "none"

        # Strategy 1: Holt-Winters (best for weekly patterns)
        if n_days >= 14:
            fitted, mtype = train_holt_winters(daily)
            if fitted is not None:
                try:
                    fc_df = forecast_model(fitted, mtype, steps=30, start_date=cat_start_date)
                    model_used = mtype
                    print(f"    [OK] {mtype} succeeded")
                except Exception as e:
                    print(f"    [FAIL] {mtype} forecast failed: {e}")

        # Strategy 2: SARIMAX fallback
        if fc_df is None and n_days >= 14:
            fitted, mtype = train_sarimax(daily)
            if fitted is not None:
                try:
                    fc_df = forecast_model(fitted, mtype, steps=30, start_date=cat_start_date)
                    model_used = mtype
                    print(f"    [OK] {mtype} succeeded")
                except Exception as e:
                    print(f"    [FAIL] {mtype} forecast failed: {e}")

        # Strategy 3: Seasonal naive (repeat last week's pattern)
        if fc_df is None:
            fc_df = fallback_seasonal_naive(daily, steps=30, start_date=cat_start_date)
            model_used = "seasonal_naive"
            print(f"    -> Using seasonal naive fallback")

        results[cat] = {
            "forecast": fc_df.to_dict(orient="records"),
            "historical": daily.reset_index().assign(
                date=lambda x: x["date"].dt.strftime("%Y-%m-%d")
            ).to_dict(orient="records"),
            "model": model_used,
        }

    joblib.dump(results, os.path.join(SAVE_DIR, "demand_forecasts.joblib"))
    print(f"  Saved forecasts for {len(results)} categories")
    return results


if __name__ == "__main__":
    print("Training demand forecasting models...")
    train_all_categories()
    print("Done!")

# 🏪 SmartMart AI — Smart Supermarket Intelligence System

AI-Driven Inventory Management, Demand Forecasting & Customer Intelligence.

## Tech Stack

- **Backend:** Python, FastAPI, SQLite, SQLAlchemy
- **ML:** scikit-learn, statsmodels (ARIMA), pandas, numpy
- **Frontend:** React (Vite), Recharts
- **Database:** SQLite

## Project Structure

```
project/
├── data/                    # Generated datasets (CSV)
│   └── generate_data.py     # Synthetic data generator
├── ml_models/               # Machine learning models
│   ├── demand_forecast.py   # ARIMA time series
│   ├── customer_segmentation.py  # K-Means + RFM
│   ├── recommender.py       # Association rules
│   ├── anomaly_detection.py # Isolation Forest
│   ├── dynamic_pricing.py   # Price optimization
│   ├── train_all.py         # Train all models
│   └── saved/               # Saved model files
├── backend/                 # FastAPI REST API
│   ├── main.py
│   ├── database.py
│   └── routes/
├── frontend/                # React dashboard
│   └── src/
│       ├── components/      # Dashboard panels
│       └── services/        # API client
└── README.md
```

## Quick Start

### 1. Generate Data
```bash
python data/generate_data.py
```

### 2. Train ML Models
```bash
pip install pandas numpy scikit-learn statsmodels joblib fastapi uvicorn
python ml_models/train_all.py
```

### 3. Start Backend (port 8000)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Start Frontend (port 5173)
```bash
cd frontend
npm install
npm run dev
```

### 5. Open Dashboard
Go to http://localhost:5173

## Features

### ML Models
- **Demand Forecasting** — ARIMA per category, 30-day predictions
- **Customer Segmentation** — RFM + K-Means (Champions/Loyal/At-Risk/Lost)
- **Recommendations** — Association rule mining (co-purchase patterns)
- **Anomaly Detection** — Isolation Forest on daily sales
- **Dynamic Pricing** — Stock/demand-based price suggestions

### Dashboard Panels
- 📊 Overview — KPIs, revenue chart, alerts
- 📦 Inventory — Stock levels, low-stock alerts, add products
- 🛍️ Sales — Revenue trends, best sellers, category breakdown
- 👥 Customers — Segments, RFM scatter, top customers, add customers
- 📈 Forecast — Predicted vs actual demand per category
- 🤖 Recommendations — Product suggestions, pricing intelligence
- ⚠️ Anomalies — Detected sales pattern anomalies

### API Endpoints
- `GET /api/dashboard/summary` — KPI summary
- `GET /api/inventory` — Stock levels
- `GET /api/inventory/low-stock` — Low stock alerts
- `POST /api/inventory` — Add product
- `GET /api/sales/revenue` — Revenue data
- `GET /api/sales/best-sellers` — Top products
- `GET /api/customers/segments` — Customer segments
- `POST /api/customers` — Add customer
- `GET /api/forecast` — Demand forecasts
- `GET /api/recommendations` — Product recommendations
- `GET /api/anomalies` — Detected anomalies
- `GET /api/pricing` — Dynamic pricing

## Dataset
- 52 products across 8 categories
- 500 customers with demographics
- 15,000 sales transactions (12 months, seasonal patterns)
- Inventory records with stock levels

# 🏪 SmartMart AI — Enterprise Smart Supermarket Intelligence & Inventory System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Recharts](https://img.shields.io/badge/Recharts-3.8-22b5bf.svg)](https://recharts.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![statsmodels](https://img.shields.io/badge/statsmodels-0.14%2B-blueviolet.svg)](https://www.statsmodels.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Version 3.0.0 — Portable Enterprise Edition**  
> An end-to-end, full-stack supermarket intelligence platform combining **5 Machine Learning engines**, a high-performance **FastAPI backend**, an interactive **React 19 dashboard**, an intelligent **data-aware conversational chatbot (SmartBot v2)**, and a **universal CSV importer** capable of adapting to any retail or supermarket dataset in real time.

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [Key Architectural Highlights](#-key-architectural-highlights)
- [System Architecture](#-system-architecture)
- [Project Directory Structure](#-project-directory-structure)
- [Machine Learning Engines & AI Modules](#-machine-learning-engines--ai-modules)
  - [1. Demand Forecasting (Holt-Winters & SARIMAX)](#1-demand-forecasting-holt-winters--sarimax)
  - [2. Customer Segmentation (RFM + K-Means)](#2-customer-segmentation-rfm--k-means)
  - [3. Product Recommendations (Apriori Association Rules)](#3-product-recommendations-apriori-association-rules)
  - [4. Sales Anomaly Detection (Isolation Forest)](#4-sales-anomaly-detection-isolation-forest)
  - [5. Dynamic Pricing Engine (Demand Velocity & Stock Health)](#5-dynamic-pricing-engine-demand-velocity--stock-health)
- [SmartBot v2 — Conversational AI Assistant](#-smartbot-v2--conversational-ai-assistant)
- [Universal Portable Data Importer & Schema Engine](#-universal-portable-data-importer--schema-engine)
- [Frontend Dashboard Panels](#-frontend-dashboard-panels)
- [Backend REST API Reference](#-backend-rest-api-reference)
- [Built-In Indian Supermarket Dataset](#-built-in-indian-supermarket-dataset)
- [Complete Local Setup & Execution Guide](#-complete-local-setup--execution-guide)
  - [Prerequisites](#prerequisites)
  - [Step 1: Clone Repository](#step-1-clone-repository)
  - [Step 2: Backend Environment & Dependencies](#step-2-backend-environment--dependencies)
  - [Step 3: Generate Dataset](#step-3-generate-dataset)
  - [Step 4: Train Machine Learning Models](#step-4-train-machine-learning-models)
  - [Step 5: Launch FastAPI Backend Server](#step-5-launch-fastapi-backend-server)
  - [Step 6: Frontend Installation & Launch](#step-6-frontend-installation--launch)
  - [Step 7: Launch Application](#step-7-launch-application)
- [Testing & Validation](#-testing--validation)
- [Environment Variables & Security](#-environment-variables--security)
- [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Executive Summary

Traditional supermarket management systems rely on static spreadsheets, lagging monthly reports, and manual stock audits. **SmartMart AI** transforms supermarket operations into an automated, data-driven intelligence workflow:

1. **Predicts What Customers Will Buy:** Uses statistical time-series models with weekly seasonality to forecast product category demand up to 30 days into the future.
2. **Optimizes Inventory & Prevents Stockouts:** Continuously tracks warehouse stock thresholds against real-time consumption velocity, alerting managers before shelves run empty.
3. **Maximizes Profit Margins with Dynamic Pricing:** Recommends tactical price adjustments (+5% to +15% markups for low-stock high-velocity goods, and -5% to -20% clearance markdowns for overstocked or expiring perishable products).
4. **Discovers Hidden Cross-Selling Bundles:** Analyzes 50,000+ checkout baskets with market basket association rule mining (lift, confidence, support) to determine optimal shelf placements and combo offers.
5. **Clusters Shoppers with RFM & Machine Learning:** Segments shoppers into Champions, Loyal Customers, Potential, At-Risk, and Lost groups to drive tailored retention campaigns.
6. **Detects Fraud & Revenue Anomalies:** Employs unsupervised Isolation Forests to flag abnormal daily revenue spikes and drops against a 7-day rolling window.
7. **Empowers Managers via Conversational AI:** Includes **SmartBot v2**, an in-app NLP assistant with context memory, temporal query filters ("last month", "yesterday", "in March"), fuzzy entity search, and in-chat chart generation.
8. **Runs on ANY Supermarket Dataset:** Incorporates regex-based column normalization and automatic schema synthesis. If you only provide raw sales transactions, SmartMart automatically reverse-engineers the products catalog, customers list, and warehouse stock levels.

---

## 🚀 Key Architectural Highlights

| Feature | Description |
|---|---|
| **Universal CSV Importer** | Auto-detects 20+ common column aliases across Sales, Products, Customers, Inventory, and Suppliers using compiled regex patterns. Cleans multi-currency symbols (`₹`, `$`, `€`, `£`, `Rs`, `INR`, `USD`), commas, percentages, and parenthesized negatives. |
| **Dynamic Feature Flags** | Automatically enables or disables dashboard modules based on the uploaded data. Locked sidebar items display interactive popovers detailing required CSV columns. |
| **Entity Auto-Synthesis** | When uploading transaction data alone, SmartMart auto-extracts distinct products and customers, calculates wholesale cost baselines, and generates realistic warehouse inventory distributions. |
| **Hybrid Time-Series Forecasting** | Combines Holt-Winters Exponential Smoothing (additive trend + weekly cycle) with SARIMAX `(1,1,1)x(1,0,1,7)` fallback and seasonal naive fallback. |
| **In-Chat Mini Visualizations** | SmartBot v2 dynamically returns interactive Recharts (Line, Bar, Pie) directly inside chat message bubbles. |
| **SQLite WAL Mode Engine** | High-concurrency SQLite setup using `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, and foreign key integrity. |
| **Source Transparency System** | Every KPI card and chart features an inspectable **Source Button** detailing its mathematical formula, database table, columns, and business justification. |
| **Native Glassmorphic Dialogs** | Replaces default browser alerts with accessible, theme-consistent dark glass modals supporting keyboard navigation (`Enter` / `Escape`). |

---

## 📐 System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │           User / Store Manager         │
                                  └───────────────────┬────────────────────┘
                                                      │
                                    HTTP / REST API   │   Port 5173 / 8000
                                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FRONTEND (React 19 + Vite + Recharts)                            │
├────────────────────────────────┬────────────────────────────────┬────────────────────────────────┤
│  Executive Dashboard           │  Inventory & Restock Panel     │  Sales Insights & Heatmap      │
│  Customer RFM & Demographics   │  Demand Forecast Viewer        │  Recommendations & Pricing     │
│  Supplier Logistics & Ratings  │  Anomaly Detection Timeline    │  Portable Data Setup & Mapping │
├────────────────────────────────┴────────────────────────────────┴────────────────────────────────┤
│  SmartBot v2 (In-Chat Recharts) │ SourceButton (Data Inspector) │ ThemeDialog (Custom Modals)    │
└─────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                              │ Axios / Fetch Client (/api)
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BACKEND (FastAPI + Uvicorn + Pydantic)                           │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Routers:                                                                                        │
│  • /api/upload     — CSV preview, regex mapping, schema import, sample datasets, factory reset   │
│  • /api/inventory  — Paginated stock tracking, low stock alerts, category summaries, restock     │
│  • /api/sales      — Revenue series, category rankings, hourly/day-of-week heatmaps, margins     │
│  • /api/customers  — Segment distributions, demographic buckets, retention trends, CSV export    │
│  • /api/suppliers  — Vendor directory, reliability metrics, revenue generated per supplier       │
│  • /api/ml         — Forecast curves, anomaly lists, pricing suggestions, Apriori rules          │
│  • /api/chat       — SmartBot v2 NLP parser, fuzzy matching, temporal filters, chart payloads    │
│  Security: Header-based X-API-Key middleware for destructive operations (reset, retrain, demo)   │
└───────────────────────┬──────────────────────────────────────────────────┬───────────────────────┘
                        │                                                  │
            SQLAlchemy  │                                  Joblib / NumPy  │
                        ▼                                                  ▼
┌──────────────────────────────────────────────┐  ┌────────────────────────────────────────────────┐
│             DATABASE LAYER (SQLite)          │  │          MACHINE LEARNING MODELS LAYER         │
├──────────────────────────────────────────────┤  ├────────────────────────────────────────────────┤
│  • supermarket.db (WAL Mode)                 │  │  • demand_forecasts.joblib (Holt-Winters)      │
│    - products (SKU, cost, price, supplier)   │  │  • customer_segments.joblib (K-Means + RFM)    │
│    - customers (demographics, membership)    │  │  • recommendations.joblib (Apriori Rules)      │
│    - sales (baskets, timestamps, discounts)  │  │  • anomaly_detection.joblib (Isolation Forest) │
│    - inventory (stock, max, reorder level)   │  │  • dynamic_pricing.joblib (Velocity Engine)    │
│    - suppliers (lead time, reliability)      │  │                                                │
│  • upload_state.db (Persistent Upload State) │  │  Automated Retraining: triggered on CSV import │
└──────────────────────────────────────────────┘  └────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```
Our 6th sem final mini project/
├── README.md                            # Comprehensive project documentation
├── .gitignore                           # Git ignore configuration
└── project/
    ├── backend/                         # FastAPI Application & SQLite Databases
    │   ├── main.py                      # Application bootstrap, CORS, router registrations
    │   ├── database.py                  # SQLAlchemy engine, ORM declarations, WAL pragma, seed loader
    │   ├── auth.py                      # API Key authorization dependency (X-API-Key)
    │   ├── upload_store.py              # Persistent SQLite store for upload state and feature flags
    │   ├── upload_handler.py            # Universal CSV parser, regex matcher, column normalizer
    │   ├── supermarket.db               # Primary SQLite database file
    │   ├── upload_state.db              # Upload session state & feature flags cache
    │   ├── requirements.txt             # Python dependencies
    │   └── routes/                      # Modular API Route Controllers
    │       ├── __init__.py              # Route exports
    │       ├── inventory.py             # Stock queries, low-stock alerts, product creation, restock
    │       ├── sales.py                 # Revenue aggregations, best sellers, hourly heatmap, margins
    │       ├── customers.py             # Segments, demographic distributions, retention, CSV export
    │       ├── suppliers.py             # Supplier catalog, reliability metrics, supply volume
    │       ├── ml.py                    # Prediction endpoints, KPI summary, model retraining
    │       ├── upload.py                # Upload preview, import, demo dataset loader, reset, samples
    │       └── chatbot.py               # SmartBot v2 NLP engine, fuzzy matching, dynamic chart generation
    ├── ml_models/                       # Machine Learning Engines & Training Pipeline
    │   ├── demand_forecast.py           # Holt-Winters Exponential Smoothing + SARIMAX fallback
    │   ├── customer_segmentation.py     # RFM feature extraction + StandardScaler + K-Means
    │   ├── recommender.py               # Apriori frequent itemset mining & association rules
    │   ├── anomaly_detection.py         # Isolation Forest daily sales anomaly detection
    │   ├── dynamic_pricing.py           # Rule-based demand velocity & inventory health engine
    │   ├── train_all.py                 # Master orchestrator script training all 5 models
    │   └── saved/                       # Serialized Joblib model artifacts
    │       ├── demand_forecasts.joblib
    │       ├── customer_segments.joblib
    │       ├── recommendations.joblib
    │       ├── anomaly_detection.joblib
    │       └── dynamic_pricing.joblib
    ├── data/                            # Raw Datasets & Synthetic Generator
    │   ├── generate_data.py             # Indian Supermarket V3 synthetic data generator
    │   ├── products.csv                 # 250+ products across 15 categories (real INR prices)
    │   ├── customers.csv                # 2,000 customers across Indian cities & demographics
    │   ├── sales.csv                    # 50,000 checkout transactions (UPI, Cards, Cash)
    │   ├── inventory.csv                # Warehouse stock distributions across 8 metro hubs
    │   └── suppliers.csv                # 15 prominent Indian FMCG suppliers
    ├── frontend/                        # React 19 Single Page Application
    │   ├── package.json                 # Node dependencies (React 19, Recharts, Vite 8)
    │   ├── vite.config.js               # Vite config with backend proxy (/api -> localhost:8000)
    │   ├── index.html                   # HTML5 shell
    │   └── src/
    │       ├── main.jsx                 # React root render
    │       ├── App.jsx                  # Main layout, panel router, global modals & chatbot
    │       ├── index.css                # Custom dark glassmorphic design system
    │       ├── services/
    │       │   └── api.js               # Centralized API service layer
    │       ├── context/
    │       │   └── ColumnMappingContext.jsx # Cross-panel dynamic column resolution context
    │       ├── constants/
    │       │   ├── colors.js            # Semantic palette & category color maps
    │       │   ├── featureRequirements.js # Requirements mapping for locked features
    │       │   └── sources.js           # Full metadata documentation for all metrics & charts
    │       └── components/              # Modular Dashboard Components
    │           ├── Sidebar.jsx          # Navigation with locked feature popover triggers
    │           ├── DashboardOverview.jsx# Executive KPI cards, area trend, monthly bars, alerts
    │           ├── InventoryPanel.jsx   # Stock tracking, low-stock table, expiring table, add modal
    │           ├── SalesInsightsPanel.jsx# Daily/monthly sales toggle, category share, rankings
    │           ├── CustomerAnalyticsPanel.jsx # RFM scatter, demographic bars, retention line
    │           ├── DemandForecastPanel.jsx  # Category tabs, 30-day forecast curves, tables
    │           ├── RecommendationsPanel.jsx # Apriori co-purchase rules, lift multipliers
    │           ├── DynamicPricingPanel.jsx  # Price adjustments, distribution chart, rationale
    │           ├── AnomaliesPanel.jsx   # Sales timeline with anomaly dots, severity tables
    │           ├── SupplierPanel.jsx    # Vendor performance, lead times, reliability scores
    │           ├── SalesHeatmapPanel.jsx# 24x7 hourly heatmap grid, profit margins, payment split
    │           ├── DataSetupPanel.jsx   # Drag-and-drop CSV importer, column mapping, table preview
    │           ├── ChatBot.jsx          # SmartBot v2 floating UI with in-chat Recharts
    │           ├── SampleDataModal.jsx  # Preview & download built-in sample CSV datasets
    │           ├── SourceButton.jsx     # Clickable source inspector popover
    │           ├── LockedFeaturePopover.jsx # Floating tooltip for locked feature requirements
    │           ├── ThemeDialog.jsx      # Glassmorphic confirm/alert modal replacement
    │           └── ErrorBoundary.jsx    # React error boundary component
    ├── technologies_used.txt            # High-level technology overview report
    ├── project_report.txt               # Architectural project report
    └── ml_technologies_report.txt       # In-depth machine learning mathematical report
```

---

## 🧠 Machine Learning Engines & AI Modules

SmartMart AI incorporates 5 dedicated Machine Learning and statistical intelligence engines located in `project/ml_models/`. Each model can be trained independently or batch-trained via `train_all.py`.

```
                                  ┌───────────────────────────┐
                                  │    Database / CSV Data    │
                                  └─────────────┬─────────────┘
                                                │
                 ┌────────────────┬─────────────┴───┬────────────────┬────────────────┐
                 │                │                 │                │                │
                 ▼                ▼                 ▼                ▼                ▼
          ┌─────────────┐  ┌─────────────┐   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │    ARIMA/   │  │   K-Means   │   │   Apriori   │  │  Isolation  │  │   Dynamic   │
          │Holt-Winters │  │   + RFM     │   │   Mining    │  │   Forest    │  │   Pricing   │
          └──────┬──────┘  └──────┬──────┘   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                 │                │                 │                │                │
                 ▼                ▼                 ▼                ▼                ▼
          ┌──────────────────────────────────────────────────────────────────────────────────┐
          │                   Saved Serialized Artifacts (.joblib files)                     │
          └──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1. Demand Forecasting (Holt-Winters & SARIMAX)
- **File:** `project/ml_models/demand_forecast.py`
- **API:** `GET /api/forecast`, `GET /api/forecast/{category}`
- **Objective:** Generates daily demand projections per product category 30 days into the future.
- **Model Architecture:**
  - **Primary Model:** `statsmodels.tsa.holtwinters.ExponentialSmoothing`
    - **Trend:** Additive (`trend="add"`).
    - **Seasonality:** Additive with a 7-day period (`seasonal="add"`, `seasonal_periods=7`), reflecting weekly supermarket shopping cycles.
    - **Initialization:** Estimated via maximum likelihood.
  - **First Fallback:** `statsmodels.tsa.statespace.sarimax.SARIMAX` with `order=(1, 1, 1)` and `seasonal_order=(1, 0, 1, 7)`.
  - **Second Fallback:** Seasonal Naive method repeating the previous 7-day pattern with variance-calibrated Gaussian noise.
- **Feature Pipeline:** Aggregates transactions by `DATE(timestamp)`, fills missing intermediate days with zero quantity, and guarantees a continuous timeline joining historical actuals to future predictions.

---

### 2. Customer Segmentation (RFM + K-Means)
- **File:** `project/ml_models/customer_segmentation.py`
- **API:** `GET /api/customers/segments`, `GET /api/customers/segments/all`, `GET /api/customers/top`
- **Objective:** Segments customer accounts based on buying behavior to optimize loyalty marketing and churn intervention.
- **Model Architecture:**
  - **RFM Extraction:**
    - **Recency ($R$):** Days elapsed between the customer's last purchase and the latest dataset date ($t_{max} - t_{last}$).
    - **Frequency ($F$):** Total count of unique checkout transactions (`sale_id`).
    - **Monetary ($M$):** Total lifetime expenditure across all purchases (`total_price`).
  - **Feature Normalization:** `sklearn.preprocessing.StandardScaler` transforms RFM features to zero mean and unit variance.
  - **Clustering:** `sklearn.cluster.KMeans` ($k=5$, `n_init=10`, `random_state=42`).
  - **Dynamic Cluster Labeling:** Clusters are ranked by average monetary value and assigned intuitive labels:
    1. **Champions:** High frequency, high spend, very recent visits.
    2. **Loyal Customers:** Consistent visits and solid monetary spend.
    3. **Potential:** Moderate spend, recent joiners with growing frequency.
    4. **At Risk:** High previous spend, but long recency gaps without recent purchases.
    5. **Lost:** Infrequent purchases, low spend, dormant for extended periods.

---

### 3. Product Recommendations (Apriori Association Rules)
- **File:** `project/ml_models/recommender.py`
- **API:** `GET /api/recommendations`
- **Objective:** Identifies co-purchased items to drive cross-selling and strategic shelf co-location.
- **Model Architecture:**
  - **Basket Grouping:** Groups checkout line items by `basket_id`. When `basket_id` is absent, automatically clusters by `(customer_id, date)` or 15-minute checkout timestamp windows.
  - **Mining Metrics:**
    - **Support:** $P(A \cap B) = \frac{\text{Baskets containing both } A \text{ and } B}{\text{Total Baskets}}$
    - **Confidence:** $P(B|A) = \frac{P(A \cap B)}{P(A)}$
    - **Lift:** $\text{Lift}(A \rightarrow B) = \frac{P(A \cap B)}{P(A) \cdot P(B)}$
  - **Dynamic Scaling:** Support and confidence thresholds dynamically adapt to basket catalog size (support threshold down to 0.08% for large transaction sets), ranking itemsets by highest lift multiplier.

---

### 4. Sales Anomaly Detection (Isolation Forest)
- **File:** `project/ml_models/anomaly_detection.py`
- **API:** `GET /api/anomalies`
- **Objective:** Detects unusual sales days caused by promotions, holidays, supply shocks, or reporting glitches.
- **Model Architecture:**
  - **Algorithm:** `sklearn.ensemble.IsolationForest` (`n_estimators=100`, `contamination=0.05`).
  - **Engineered Daily Features:**
    1. Total daily gross sales (`total_sales`).
    2. Total items sold (`total_quantity`).
    3. Total completed transactions (`num_transactions`).
    4. Sales deviation from 7-day moving average (`sales_deviation = total_sales - rolling_7d_avg`).
    5. Unique product catalog count sold per day (`unique_products`).
  - **Classification:**
    - **Spike:** Positive deviation from rolling baseline.
    - **Drop:** Negative deviation from rolling baseline.
    - **Severity:** Classified as **High** if absolute deviation exceeds median anomaly deviation, otherwise **Medium**.

---

### 5. Dynamic Pricing Engine (Demand Velocity & Stock Health)
- **File:** `project/ml_models/dynamic_pricing.py`
- **API:** `GET /api/pricing`
- **Objective:** Proposes tactical price modifications based on real-time inventory velocity and product perishability.
- **Decision Engine Logic:**
  - **Demand Velocity:** Measures units sold over the last 30 days vs. historical daily burn rate.
  - **Days of Stock Remaining:** $\text{Days Remaining} = \frac{\text{Current Stock}}{\text{Average Daily Demand}}$
  - **Heuristic Rules:**
    - **Premium Markup (+5% to +15%):** Triggered when stock drops below safety reorder threshold while 30-day demand surges above 20x daily average.
    - **Clearance Markdown (-5% to -20%):** Triggered when stock exceeds 3x reorder threshold while sales velocity declines.
    - **Perishability Clearance (-15%):** Triggered when remaining shelf life $\le 7$ days but current stock exceeds 14 days of average demand.
    - **Hold:** Stock and demand remain in equilibrium.
  - Every recommendation includes the suggested price, price change percentage, action badge, plain-English justification, and confidence score.

---

## 💬 SmartBot v2 — Conversational AI Assistant

**SmartBot v2** is an embedded, data-aware natural language assistant (`project/backend/routes/chatbot.py` & `project/frontend/src/components/ChatBot.jsx`) providing store managers with instant voice/text answers.

```
       ┌───────────────────────────────┐
       │   User: "How's revenue this   │
       │   month compared to dairy?"   │
       └───────────────┬───────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│  SmartBot Natural Language Engine           │
├─────────────────────────────────────────────┤
│  1. Intent Recognition (25+ scored intents) │
│  2. Temporal Extraction ("this month")      │
│  3. Fuzzy Entity Matcher ("Dairy")          │
│  4. Parameterized SQL Query Execution       │
│  5. Chart Payload Generator (Line/Bar/Pie)  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   SmartBot: Formatted Metrics │
       │   + Interactive Recharts Card │
       │   + Follow-up Suggestion Chips│
       └───────────────────────────────┘
```

### Capabilities:
- **25+ Specialized Intents:** Total revenue, monthly trends, category breakdowns, best/worst sellers, low-stock warnings, customer counts, VIP spenders, RFM segments, profit margins, supplier summaries, payment methods, basket size analytics, peak hours, product lookups, category vs. category comparisons, discount impact, and growth rates.
- **Temporal Parser:** Understands relative time qualifiers (`today`, `yesterday`, `this week`, `last week`, `this month`, `last month`, `this year`, `last 30 days`, `March 2024`). If uploaded data is historical, SmartBot anchors relative dates to the dataset's maximum date.
- **Fuzzy Entity Matching:** Uses `difflib.SequenceMatcher` with substring boosting to resolve misspelled product and category names (e.g., "bakri", "milkk", "snaks").
- **Dynamic Head-to-Head Comparison:** Answers queries like *"compare Dairy vs Bakery"* with a Markdown comparison table contrasting revenue, units sold, product count, profit margin, and baskets, automatically crowning a revenue and margin winner.
- **In-Chat Data Visualizations:** Returns structured chart payloads that render interactive Recharts (Bar, Line, Pie) directly inside the chat stream.
- **Context Memory & LRU Eviction:** Retains conversation context per `session_id` with 30-minute TTL and automatic LRU eviction.

---

## 🔄 Universal Portable Data Importer & Schema Engine

SmartMart AI can operate with **any** retail dataset. The upload handler (`project/backend/upload_handler.py`) and upload route (`project/backend/routes/upload.py`) provide autonomous data ingestion:

```
┌──────────────┐     ┌───────────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
│ Custom CSV   │ ──► │ Column Auto-Detection │ ──► │ Interactive Preview & │ ──► │ Normalized Load &      │
│ File Upload  │     │ (Regex Pattern Match) │     │ Manual Override       │     │ Cross-Table Synthesis  │
└──────────────┘     └───────────────────────┘     └───────────────────────┘     └────────────────────────┘
```

1. **Auto-Detection Regex Patterns:** Matches common column variants across retail POS formats:
   - `product_id`: `sku`, `item_id`, `barcode`, `upc`, `article_no`, `stockcode`
   - `name`: `product_name`, `description`, `title`, `item_desc`, `merchandise`
   - `category`: `dept`, `department`, `class`, `product_line`, `aisle`, `segment`
   - `total_price`: `revenue`, `total_amount`, `order_total`, `line_total`, `net_amount`
   - `timestamp`: `date`, `sale_date`, `transaction_date`, `invoicedate`, `created_at`
2. **Numeric & Currency Normalization:** Strips currency symbols (`$`, `₹`, `€`, `£`, `Rs`, `INR`, `USD`), commas, spaces, percentages, and handles accounting negatives `(12.34)` $\rightarrow$ `-12.34`.
3. **Autonomous Entity Synthesis:**
   - Uploading a **Sales** file automatically creates missing entries in `products`, `customers`, and `inventory`.
   - Wholesale costs are approximated (55% of retail price) if cost columns are missing.
   - Warehouse locations, max capacities, and safety reorder thresholds are automatically assigned.
4. **Dynamic Feature Flags:** Calculates which dashboard features can safely be activated (`has_sales`, `has_customers`, `has_cost`, `enable_forecast`, `enable_pricing`, etc.) and stores them persistently in `upload_state.db`.

---

## 🖥️ Frontend Dashboard Panels

The React 19 frontend provides 11 specialized intelligence panels:

| Panel | Primary Route | Key Widgets & Capabilities |
|---|---|---|
| **📊 Dashboard Overview** | `dashboard` | 6 KPI cards, 60-day daily revenue sparkline, monthly revenue bar chart with hover glows, top 10 best sellers, low-stock warnings with stock vs. reorder ratios. |
| **📦 Inventory Management** | `inventory` | Stock by category bar chart, category share pie chart, low-stock table with instant restock (+50 units), expiring products table, master inventory table with debounced search, category filter, and "Add Product" modal. |
| **🛍️ Sales Insights** | `sales` | Daily/Monthly revenue toggle, revenue line chart, category revenue breakdown, best-selling products ranking table with transaction velocity. |
| **👥 Customer Analytics** | `customers` | 5-segment RFM breakdown, interactive Recency vs. Monetary scatter plot, demographic age buckets, membership tier breakdown, monthly customer retention curve, top 20 VIP table, and CSV export. |
| **📈 Demand Forecast** | `forecast` | Category tab selector, 30-day forecast line charts joining actuals to predictions, forecast table, model architecture inspection card. |
| **🤖 Recommendations** | `recommendations` | Apriori frequent itemset co-purchase cards with lift multipliers, association rules table (support, confidence, lift), bundle promotion ideas. |
| **💲 Dynamic Pricing** | `pricing` | Price increase/decrease/hold KPIs, price change distribution histogram, action filter, suggested price table with plain-English rationales. |
| **⚠️ Anomaly Detection** | `anomalies` | Timeline chart with red glowing anomaly dots, spike vs. drop counters, anomaly log table with deviation metrics and severity badges. |
| **🚚 Supplier Management** | `suppliers` | Supplier count, average reliability %, average lead time, revenue generated by vendor, supplier directory table with reliability progress bars. |
| **🔥 Sales Heatmap** | `heatmap` | 24x7 hourly and day-of-week shopping velocity heatmap grid, payment method pie chart and table, category profit margin breakdown. |
| **📁 Data Setup & Mapping** | `datasetup` | Drag-and-drop CSV uploader, column mapping dropdowns, table preview, demo dataset 1-click loader, database reset button, sample dataset download modal. |

---

## 🔌 Backend REST API Reference

The FastAPI backend serves comprehensive REST endpoints with automatic OpenAPI documentation available at `http://localhost:8000/docs`.

### Inventory Endpoints (`/api/inventory`)
- `GET /api/inventory` — Paginated inventory list (supports `search`, `category`, `page`, `limit`).
- `GET /api/inventory/all` — Full inventory list for charting.
- `GET /api/inventory/low-stock` — Products with stock $\le$ reorder threshold.
- `GET /api/inventory/by-category` — Stock and low-stock count summarized by category.
- `GET /api/inventory/expiring-soon` — Products expiring within 7 days.
- `GET /api/inventory/categories` — List of all distinct product categories.
- `POST /api/inventory` — Add a new product and create inventory records.
- `POST /api/inventory/restock/{product_id}` — Increment product stock by specified quantity.

### Sales Endpoints (`/api/sales`)
- `GET /api/sales` — Retrieve recent transactions (`limit` up to 1000).
- `GET /api/sales/revenue` — Daily and monthly aggregated revenue series.
- `GET /api/sales/best-sellers` — Top 20 products ranked by total revenue.
- `GET /api/sales/by-category` — Sales breakdown and average transaction by category.
- `GET /api/sales/hourly-heatmap` — Transaction counts and revenue by day-of-week and hour.
- `GET /api/sales/payment-breakdown` — Transaction distribution across payment methods.
- `GET /api/sales/profit-margins` — Category profit margins ($Revenue - Cost$).

### Customer Endpoints (`/api/customers`)
- `GET /api/customers` — Paginated customer profiles (supports `search`, `tier`, `page`, `limit`).
- `GET /api/customers/export` — Stream entire customer directory as a CSV file.
- `GET /api/customers/segments` — Segmentation metadata (counts, cluster means, top customers).
- `GET /api/customers/segments/all` — Lightweight customer records for scatter plotting.
- `GET /api/customers/top` — Top 20 highest lifetime spending customers.
- `GET /api/customers/demographics` — Age groups, gender distribution, tiers, and preferred sections.
- `GET /api/customers/retention` — Monthly active customer counts and spend.
- `POST /api/customers` — Register a new customer record.

### Supplier Endpoints (`/api/suppliers`)
- `GET /api/suppliers` — Supplier directory with product counts and reliability scores.
- `GET /api/suppliers/performance` — Supplier performance with revenue generated and units sold.
- `GET /api/suppliers/{supplier_id}` — Supplier profile and supplied product catalog.

### Machine Learning & Dashboard Endpoints (`/api`)
- `GET /api/dashboard/summary` — Executive store KPIs (revenue, cost, profit, margin, baskets, alerts).
- `GET /api/forecast` — Demand forecasts for all product categories.
- `GET /api/forecast/{category}` — 30-day forecast curve for a specific category.
- `GET /api/recommendations` — Apriori association rules and co-purchase suggestions.
- `GET /api/anomalies` — Isolation Forest detected sales anomalies, spikes, drops, and daily series.
- `GET /api/pricing` — Dynamic pricing adjustments, change percentages, and explanations.
- `POST /api/ml/retrain` — Retrain all 5 models via subprocess (`X-API-Key` required).

### Upload & Data Management Endpoints (`/api/upload`)
- `GET /api/upload/status` — Current database row counts, active feature flags, and mapping info.
- `POST /api/upload/preview` — Upload raw CSV and receive auto-detected column mappings and preview rows.
- `POST /api/upload/import` — Commit confirmed CSV mapping to database with automated cross-table sync.
- `POST /api/upload/reset` — Purge all database tables and serialized model files (`X-API-Key` required).
- `POST /api/upload/load-demo` — Load built-in Indian supermarket dataset and retrain models (`X-API-Key` required).
- `GET /api/upload/sample-datasets` — Metadata and preview rows for the 5 sample CSV datasets.
- `GET /api/upload/sample-datasets/{filename}/download` — Direct download endpoint for sample CSV files.

### Chatbot Endpoint (`/api/chat`)
- `POST /api/chat` — Send query to SmartBot v2, returning markdown responses, follow-up chips, and Recharts payloads.

---

## 🇮🇳 Built-In Indian Supermarket Dataset

SmartMart AI includes a realistic Indian supermarket dataset generator (`project/data/generate_data.py`):

- **Products (250+ SKUs across 15 categories):** Authentic Indian brands including *Amul, Mother Dairy, Aashirvaad, Tata Sampann, Fortune, Saffola, MDH, Britannia, English Oven, Nescafe, Taj Mahal, Thums Up, Lays, Haldiram's, Bikaji, Cadbury Dairy Milk, Dettol, Surf Excel, Maggi, MTR*, etc.
- **Customers (2,000 Profiles):** Indian demographics across Tier-1 and Tier-2 cities (Mumbai, Delhi, Bangalore, Hyderabad, Pune, Chennai, Kolkata, Ahmedabad) with realistic phone numbers, pincodes, and membership tiers.
- **Sales (50,000 Transactions):** Seasonal checkout baskets spanning a full 12-month calendar, incorporating festival demand surges (Diwali, Holi, New Year, Independence Day), weekend spikes, and Indian payment preferences (40% UPI, 20% Debit Card, 15% Credit Card, 15% Cash, 10% Net Banking).
- **Inventory Records:** Stock counts, warehouse shelf coordinates, and safety buffer levels distributed across 8 regional distribution centers.
- **Suppliers (15 Companies):** Prominent Indian FMCG conglomerates (*GCMMF / Amul, ITC Limited, Tata Consumer Products, Hindustan Unilever, Britannia Industries, Nestle India, Parle Products, Dabur India, Marico, Adani Wilmar*).

---

## 💻 Complete Local Setup & Execution Guide

Follow these step-by-step instructions to run the entire project on your local machine.

### Prerequisites

Ensure you have the following installed on your machine:
- **Python:** Version `3.10` or higher (`python --version`)
- **Node.js:** Version `18.0` or higher (`node --version`)
- **npm:** Version `9.0` or higher (`npm --version`)
- **Git:** (`git --version`)

---

### Step 1: Clone Repository

Open your terminal or PowerShell and navigate to your project directory:

```bash
git clone https://github.com/riteesh800/smart-supermarket.git
cd "smart-supermarket"
```

---

### Step 2: Backend Environment & Dependencies

Navigate to the project backend folder:

```bash
cd project/backend
```

Create a Python virtual environment:

```bash
# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# On macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install all required Python backend and machine learning dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Installed Packages:** `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `joblib`, `python-multipart`.

---

### Step 3: Generate Dataset

Generate the 250+ product catalog, 2,000 customers, 15 suppliers, warehouse stock records, and 50,000 sales transactions:

```bash
# Navigate to the data folder from project root
cd ../data
python generate_data.py
```

*Output will confirm generation of `products.csv`, `customers.csv`, `suppliers.csv`, `inventory.csv`, and `sales.csv`.*

---

### Step 4: Train Machine Learning Models

Train all 5 machine learning models (Demand Forecasting, Customer Segmentation, Recommendations, Anomaly Detection, Dynamic Pricing):

```bash
# Navigate to the ml_models folder
cd ../ml_models
python train_all.py
```

*Output will train each model sequentially and save `.joblib` artifacts into `project/ml_models/saved/`:*
- `demand_forecasts.joblib`
- `customer_segments.joblib`
- `recommendations.joblib`
- `anomaly_detection.joblib`
- `dynamic_pricing.joblib`

---

### Step 5: Launch FastAPI Backend Server

Navigate to the backend directory and launch Uvicorn:

```bash
cd ../backend
uvicorn main:app --reload --port 8000
```

*The backend server will start at `http://localhost:8000`.*
- **Interactive Swagger Documentation:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Alternative ReDoc Documentation:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

*(Keep this terminal open and running)*

---

### Step 6: Frontend Installation & Launch

Open a **new, separate terminal window** and navigate to the frontend directory:

```bash
cd project/frontend
```

Install frontend npm dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

*The frontend development server will launch at `http://localhost:5173`.*

---

### Step 7: Launch Application

Open your web browser and navigate to:

👉 **[http://localhost:5173](http://localhost:5173)**

The frontend automatically proxies `/api` requests to `http://localhost:8000`. You can now explore all 11 panels, converse with SmartBot v2, restock inventory, inspect data sources, or upload custom CSV datasets!

---

## 🧪 Testing & Validation

### Verify Backend Health
```bash
# Check root API status
curl http://localhost:8000/

# Check KPI summary
curl http://localhost:8000/api/dashboard/summary

# Check SmartBot
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"total revenue\"}"
```

### Verify Frontend Production Build
To validate that the frontend builds cleanly without TypeScript or bundling errors:

```bash
cd project/frontend
npm run build
```

---

## 🔐 Environment Variables & Security

| Variable | Default Value | Description |
|---|---|---|
| `SMARTMART_API_KEY` | `dev-key` | API key required in the `X-API-Key` request header for administrative endpoints (`/api/upload/reset`, `/api/upload/load-demo`, `/api/ml/retrain`). |

To set a custom API key:
```bash
# Windows PowerShell
$env:SMARTMART_API_KEY="your-secret-production-key"
uvicorn main:app --reload --port 8000

# Linux / macOS
export SMARTMART_API_KEY="your-secret-production-key"
uvicorn main:app --reload --port 8000
```

---

## ❓ Troubleshooting & FAQ

### 1. `ModuleNotFoundError: No module named 'fastapi'`
Make sure your Python virtual environment is activated before starting the server:
- Windows: `.\venv\Scripts\Activate.ps1`
- Linux/Mac: `source venv/bin/activate`

### 2. Frontend shows `Failed to fetch` or empty dashboard
Ensure the FastAPI backend is running on port 8000 (`http://localhost:8000`). Vite forwards `/api` calls directly to port 8000. Check the terminal running Uvicorn for errors.

### 3. "Model not trained" warning on Forecast or Recommendations panel
Run the training script to generate missing model artifacts:
```bash
python project/ml_models/train_all.py
```
Alternatively, log in to the dashboard, open **Data Setup**, and click **"Load Demo Data"**. The backend will automatically train all models.

### 4. Database Locked or Permission Errors
SmartMart uses SQLite in **WAL (Write-Ahead Logging)** mode. Ensure no external SQLite inspection tools hold exclusive locks on `supermarket.db` or `upload_state.db`.

---

## 👥 Contributors & Academic Context

- **Academic Context:** 6th Semester Final Mini Project
- **Project Name:** AI-Driven Smart Supermarket Management System (SmartMart AI)
- **Repository:** [riteesh800/smart-supermarket](https://github.com/riteesh800/smart-supermarket)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

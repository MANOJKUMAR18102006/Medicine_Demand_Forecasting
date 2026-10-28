# AI-Based Medicine Demand Forecasting & Inventory Optimization System

An enterprise data science, machine learning, and healthcare analytics application that forecasts future medicine demand using historical consumption patterns and provides automated inventory replenishment and procurement recommendations.

---

## Architecture Overview

```
medicine-demand-forecasting/
├── dataset/
│   ├── medicine_demand.csv             # Synthetic 3-year historical dataset (19,728 rows)
│   ├── cleaned_medicine_demand.csv     # Cleaned, continuous time-series dataset (19,728 rows)
│   ├── model_ready_data.csv            # Engineered features dataset (19,188 rows, 40 cols)
│   └── generate_dataset.py             # Reproducible data generator script
│
├── notebooks/
│   ├── 01_eda_and_data_understanding.ipynb # Interactive Jupyter analysis notebook
│   └── generate_notebook.py
│
├── reports/
│   ├── figures/                        # Matplotlib/Seaborn visualization figures
│   │   ├── 01_medicine_demand_bar.png
│   │   ├── 02_daily_demand_timeline.png
│   │   ├── 03_monthly_demand_trend.png
│   │   ├── 04_day_of_week_demand.png
│   │   ├── 05_seasonal_demand.png
│   │   ├── 06_correlation_heatmap.png
│   │   ├── 07_demand_distribution.png
│   │   ├── 08_stock_vs_demand.png
│   │   └── 09_actual_vs_predicted.png
│   ├── interactive_eda.html            # Plotly interactive dashboard
│   ├── eda_report.md                   # Full EDA markdown summary
│   └── medicine_summary_metrics.csv
│
├── ml/                                 # Machine Learning & Optimization Engine
│   ├── data_preprocessing.py           # Ingestion, cleaning, non-destructive outlier tagging
│   ├── eda.py                          # Exploratory analysis pipeline
│   ├── feature_engineering.py          # Lags, leakage-free rolling stats, calendar sinusoids
│   ├── train_model.py                  # Chronological training: LR, Random Forest, XGBoost
│   ├── evaluate_model.py               # Out-of-time test metrics (MAE, RMSE, R2, Safe MAPE)
│   ├── predict.py                      # Multi-horizon recursive demand forecasting (7, 14, 30 days)
│   ├── inventory_optimizer.py          # Decision-support engine (Safety stock, ROP, Order Qty)
│   ├── test_system.py                  # End-to-end verification test suite
│   └── models/
│       ├── linear_regression.pkl       # Baseline model
│       ├── random_forest.pkl           # Ensemble model
│       ├── xgboost.pkl                 # Gradient boosting model
│       ├── best_model.pkl              # Top model on test set (XGBoost)
│       ├── preprocessing.pkl           # Scaler & categorical encoders
│       └── model_metrics.json          # Machine-readable performance metrics
│
├── backend/                            # FastAPI REST API
│   ├── main.py                         # App entrypoint, CORS, startup model warming
│   ├── schemas/                        # Pydantic request & response validation
│   │   ├── forecast.py
│   │   ├── inventory.py
│   │   └── analytics.py
│   ├── routes/                         # Modular route controllers
│   │   ├── health.py                   # GET /api/health
│   │   ├── forecast.py                 # POST /api/forecast
│   │   ├── inventory.py                # POST /api/inventory-analysis, GET /api/medicines
│   │   └── analytics.py                # GET /api/model-metrics, GET /api/analytics/summary
│   └── services/                       # Orchestration & business logic
│       ├── prediction_service.py
│       ├── inventory_service.py
│       └── analytics_service.py
│
└── frontend/                           # React + Vite + Tailwind CSS Healthcare Dashboard
    ├── src/
    │   ├── App.jsx                     # Dashboard coordinator & tab router
    │   ├── main.jsx                    # React entrypoint
    │   ├── index.css                   # Tailwind CSS styling directives
    │   ├── services/
    │   │   └── api.js                  # Axios client configured for FastAPI
    │   └── components/
    │       ├── Navbar.jsx              # Navigation header & live connection monitor
    │       ├── DashboardTab.jsx        # KPIs, demand trends, top medicines, stock alerts
    │       ├── ForecastTab.jsx         # Medicine & horizon selector, Recharts forecast chart & table
    │       ├── InventoryTab.jsx        # Stock input, status badges, shortages, recommendations
    │       ├── AnalyticsTab.jsx        # Data science insights (monthly, day-of-week, seasonal)
    │       └── ModelPerformanceTab.jsx # Model comparison table, metrics explanations, R2
    ├── package.json
    └── vite.config.js
```

---

## Machine Learning Performance

Chronological Holdout Test Evaluation (Sep 2024 to Dec 2024, 2,196 records):

| Model | MAE (Units) | RMSE (Units) | $R^2$ Score | Safe MAPE (%) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Linear Regression** | 13.92 | 20.16 | 0.8029 | 40.20% | Baseline |
| **Random Forest Regressor** | 13.08 | 18.50 | 0.8340 | 30.20% | Benchmark |
| **XGBoost Regressor** | **12.68** | **17.67** | **0.8486** | **28.23%** | **★ Selected Best** |

---

## Multi-Shop Authentication & Data Isolation Architecture

MedDemand includes a secure multi-medical-shop tenant architecture:

- **Isolated Tenancy:** Every registered medical shop manages its own private inventory, stock thresholds, reorder points, and forecast history.
- **Server-Side Authorization:** Tenant boundaries are strictly enforced via JWT Bearer authentication and HTTP-only session cookies. Client-supplied IDs are never trusted as authorization proof.
- **Bcrypt Security:** Passwords are salted and hashed using bcrypt (12 rounds) — plain text passwords are never persisted or exposed.
- **Shared XGBoost Model:** The high-accuracy XGBoost demand forecaster and recursive feature pipeline are seamlessly leveraged across all shop inventories without data leakage.

### Authentication & Shop Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Register new medical shop with unique email check | No |
| `POST` | `/api/auth/login` | Authenticate shop credentials & issue JWT token | No |
| `POST` | `/api/auth/logout` | Terminate session & clear cookies | No |
| `GET` | `/api/auth/me` | Fetch authenticated shop profile | **Yes (Bearer)** |
| `PUT` | `/api/auth/profile` | Update shop contact details & address | **Yes (Bearer)** |
| `POST` | `/api/auth/forgot-password` | Request password reset token | No |
| `POST` | `/api/auth/reset-password` | Reset password using one-time token | No |
| `GET` | `/api/medicines` | Return shop's private medicine catalog | Optional / Shop |
| `POST` | `/api/medicines` | Add medicine to shop inventory | **Yes (Bearer)** |
| `POST` | `/api/medicines/seed-starter` | Pre-load 18 standard hospital drugs | **Yes (Bearer)** |
| `POST` | `/api/inventory/{name_or_id}` | Update physical stock for shop medicine | **Yes (Bearer)** |
| `POST` | `/api/forecast` | Run recursive XGBoost forecast & log to shop history | Optional / Shop |
| `GET` | `/api/forecasts/history` | View recent forecast execution history for shop | **Yes (Bearer)** |
| `POST` | `/api/inventory-analysis` | Compute safety stock, shortages & reorder recommendations | Optional / Shop |
| `GET` | `/api/analytics/summary` | Aggregate shop-specific KPIs, seasonality & stock alerts | Optional / Shop |
| `GET` | `/api/model-metrics` | Shared holdout test evaluation metrics | No |

---

## Quick Start Guide

### 1. Start the FastAPI Backend
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Swagger Interactive Documentation: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/api/health`

### 2. Start the React Frontend Dashboard
```bash
cd frontend
npm run dev
```
- Dashboard URL: `http://localhost:5173`

### 3. Run the Data Science & ML Demonstration (Viva-Ready)
```bash
python scripts/data_science_demo.py
```
*Optional parameters:*
```bash
# Custom medicine and horizon
python scripts/data_science_demo.py --medicine Paracetamol --days 7

# Fast mode (uses serialized models instead of full retraining)
python scripts/data_science_demo.py --skip-train
```

### 4. Run the Test Suites

**End-to-End ML Pipeline & Original API Test Suite:**
```bash
python ml/test_system.py
```

**Multi-Shop Authentication & Data Isolation Test Suite:**
```bash
python backend/test_multi_shop_auth.py
```

**Procurement & Nearby Exchange Test Suite:**
```bash
python backend/test_procurement_exchange.py
```


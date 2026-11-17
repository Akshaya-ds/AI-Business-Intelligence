# AI Business Intelligence & Inventory Intelligence Platform

An enterprise SaaS application providing multi-business intelligence, sales analytics, machine learning demand forecasting, inventory optimization, and an AI-powered business assistant grounded in business dataset records.

---

## Features

### Phase 1: Application Foundation & Business Analytics
- **Multi-Business Management**: Onboard and isolate multiple businesses with independent datasets and analytics.
- **Dataset Management**: Upload CSV and Excel (`.xlsx`) datasets with automatic column detection, validation, preview, and upload history.
- **Executive Overview Dashboard**: Total Revenue, Units Sold, Profit, Margin, Monitored Products, and inventory health metrics.
- **Sales & Product Analytics**: Historical daily sales trends, category performance, and top-selling product breakdowns.
- **Light SaaS Theme**: Modern design with soft sage green accents, clean card layouts, and responsive desktop/mobile styling.

### Phase 2: Machine Learning, Demand Forecasting & Inventory Intelligence
- **Data Preprocessing Pipeline**: Automatic date parsing, sales aggregation by product and date, missing value handling, and column mapping.
- **Automated ML Training**: Automated training of Random Forest Regressor and XGBoost time-series models per product using time-based train/test splits.
- **Model Evaluation**: Metrics computed from test partitions (MAE, RMSE, MAPE).
- **Demand Forecasting**: 7-day, 14-day, and 30-day demand predictions using saved trained models.
- **Inventory Intelligence**:
  - Live stock monitoring and risk assessment (Optimal, Low Stock, Stockout, Critical Low).
  - Dynamic reorder point calculations based on lead times and safety stock thresholds.
  - Calculated reorder quantity recommendations.

### Phase 3: Gemini AI Business Assistant & Deployment Readiness
- **Data-Grounded AI Assistant**: Business owners can query their data directly (e.g., top products, sales trends, inventory risks, demand predictions).
- **Gemini API Integration**: Leverages Google Gemini (`gemini-1.5-flash`) via `google-generativeai` with strict grounding rules preventing fabricated figures.
- **Fallback Intelligence**: When no Gemini API key is configured, provides grounded business summaries directly from the verified dataset and model records.
- **Strict Business Isolation**: All data, models, forecasts, and AI context are scoped strictly by `business_id`.

---

## Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Modern CSS
- **Backend**: Python FastAPI, Uvicorn, SQLAlchemy, Pydantic V2
- **Data & ML**: Pandas, NumPy, Scikit-Learn, XGBoost, Joblib
- **Database**: SQLite (local development), PostgreSQL ready for production
- **AI Integration**: Google Generative AI (Gemini 1.5 Flash)

---

## Project Structure

```
AI_Business_Intelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analytics.py      # Summary, trends, top products, category performance
│   │   │   ├── assistant.py      # Grounded AI Business Assistant endpoint
│   │   │   ├── business.py       # Business onboarding and listing
│   │   │   ├── dataset.py        # CSV/Excel upload, validation, and preview
│   │   │   ├── forecast.py       # ML demand predictions by product
│   │   │   ├── inventory.py      # Stock monitoring, alerts, and reorder logic
│   │   │   └── ml.py             # Model training trigger and model listing
│   │   ├── core/
│   │   │   ├── analytics_engine.py # Aggregation algorithms
│   │   │   ├── db.py             # Database engine & session management
│   │   │   ├── ml_training.py    # Time-split training and evaluation pipeline
│   │   │   ├── models.py         # SQLAlchemy models (Business, Dataset, MLModel, BusinessSettings)
│   │   │   ├── preprocess.py     # Column mapping & data cleaning
│   │   │   ├── schemas.py        # Pydantic V2 request & response models
│   │   │   └── upload.py         # File validation logic
│   │   ├── utils/
│   │   │   └── file_handler.py   # Upload file management
│   │   └── main.py               # FastAPI application entry point & CORS
│   ├── data/
│   │   └── demo.csv              # Demonstration dataset
│   ├── models/                   # Persisted machine learning models (.pkl)
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── api.ts            # Typed API client for all backend endpoints
│   │   ├── App.tsx               # Main SaaS dashboard application
│   │   ├── index.css             # Light sage green styling & responsive layout
│   │   └── main.tsx              # React DOM entry point
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── app.db                    # SQLite database
│   └── uploads/                  # Uploaded datasets
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
1. Open a terminal in `backend/`:
   ```bash
   cd backend
   ```
2. Activate your virtual environment (or create one):
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables (optional for live Gemini AI responses):
   ```bash
   # Copy .env.example to .env
   cp ../.env.example .env
   ```
   Edit `.env` and set:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
5. Start the FastAPI backend:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000) and interactive Swagger docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Frontend Setup
1. In a separate terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Deployment Configuration

### Database Configuration
- **Development**: Defaults automatically to SQLite stored at `data/app.db`.
- **Production**: Set the `DATABASE_URL` environment variable:
  ```env
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  ```

### Free-Tier Hosting (Render / Railway / Vercel)
- **Backend (Render / Railway)**:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Environment Variables: `DATABASE_URL`, `GEMINI_API_KEY`
- **Frontend (Vercel / Netlify)**:
  - Build Command: `npm run build`
  - Output Directory: `dist`
  - Environment Variable: Set `VITE_API_BASE_URL` to your production backend URL.

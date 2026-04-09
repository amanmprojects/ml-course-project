# Crop Recommendation Web App

This project now includes a mobile-first web app and a FastAPI inference backend around your trained crop models.

## Project Structure

- `backend/` - FastAPI service exposing health and prediction endpoints.
- `frontend/` - React + Vite single-page form for crop recommendation.
- `xg-boost/` - XGBoost model and notebook.
- `random-forest/` - Random Forest model and notebook.

## 1) Run the Backend

```bash
cd backend
/home/aman/Code2/ml-course-project/.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:
- `GET /health`
- `POST /predict?model=xgboost`

Example prediction request:

```bash
curl -X POST 'http://127.0.0.1:8000/predict?model=xgboost' \
  -H 'Content-Type: application/json' \
  -d '{"N":90,"P":42,"K":43,"temperature":20.87,"humidity":82.0,"ph":6.5,"rainfall":202.93}'
```

## 2) Run the Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

## 3) Production Build

```bash
cd frontend
npm run build
```

Build output is in `frontend/dist`.

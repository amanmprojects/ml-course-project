import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .model_service import ModelName, ModelService
from .report_extraction_service import ReportExtractionService
from .schemas import (
    ExtractedValues,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    ReportExtractionResponse,
)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_backend_env() -> None:
    env_path = get_project_root() / "backend" / ".env"
    load_dotenv(env_path, override=False)


def get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


load_backend_env()

model_service = ModelService(project_root=get_project_root())
report_extraction_service = ReportExtractionService()


def get_max_upload_bytes() -> int:
    mb = float(os.getenv("MAX_UPLOAD_MB", "8"))
    return int(mb * 1024 * 1024)


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_service.load_models()
    yield


app = FastAPI(title="Crop Recommendation API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", loaded_models=sorted(model_service.models.keys()))


@app.post("/predict", response_model=PredictionResponse)
def predict(
    payload: PredictionRequest,
    model: ModelName = Query(default=os.getenv("DEFAULT_MODEL", "xgboost")),
) -> PredictionResponse:
    try:
        crop = model_service.predict(payload.model_dump(), model_name=model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PredictionResponse(crop=crop, model=model)


@app.post("/extract-report-values", response_model=ReportExtractionResponse)
async def extract_report_values(file: UploadFile = File(...)) -> ReportExtractionResponse:
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WEBP images are allowed")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > get_max_upload_bytes():
        raise HTTPException(status_code=400, detail="Uploaded image exceeds MAX_UPLOAD_MB")

    try:
        values, confidence = report_extraction_service.extract_values(image_bytes, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc

    missing_fields = [
        key for key, value in values.model_dump().items() if value is None
    ]
    return ReportExtractionResponse(
        extracted_values=ExtractedValues(**values.model_dump()),
        missing_fields=missing_fields,
        confidence=confidence,
    )

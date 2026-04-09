from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    N: float = Field(..., ge=0, le=300, description="Nitrogen content")
    P: float = Field(..., ge=0, le=300, description="Phosphorus content")
    K: float = Field(..., ge=0, le=300, description="Potassium content")
    temperature: float = Field(..., ge=0, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=500, description="Rainfall in mm")


class PredictionResponse(BaseModel):
    crop: str
    model: Literal["xgboost", "random_forest"]


class HealthResponse(BaseModel):
    status: str
    loaded_models: list[str]


class ExtractedValues(BaseModel):
    N: float | None = Field(default=None, ge=0, le=300)
    P: float | None = Field(default=None, ge=0, le=300)
    K: float | None = Field(default=None, ge=0, le=300)
    temperature: float | None = Field(default=None, ge=0, le=60)
    humidity: float | None = Field(default=None, ge=0, le=100)
    ph: float | None = Field(default=None, ge=0, le=14)
    rainfall: float | None = Field(default=None, ge=0, le=500)


class ReportExtractionResponse(BaseModel):
    extracted_values: ExtractedValues
    missing_fields: list[str]
    confidence: float = Field(..., ge=0, le=1)
    source: Literal["llm_vision"] = "llm_vision"

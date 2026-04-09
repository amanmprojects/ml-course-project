import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

ModelName = Literal["xgboost", "random_forest"]
FEATURE_ORDER = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


@dataclass
class LoadedModel:
    model: Any
    label_encoder: Any | None = None


class ModelService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.models: dict[ModelName, LoadedModel] = {}

    def load_models(self) -> None:
        self.models["xgboost"] = self._load_xgboost_model(
            self.project_root / "xg-boost" / "crop_model_xgboost.pkl"
        )
        self.models["random_forest"] = self._load_random_forest_model(
            self.project_root / "random-forest" / "crop_model_random_forest.pkl"
        )

    def _load_xgboost_model(self, model_path: Path) -> LoadedModel:
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")

        with model_path.open("rb") as f:
            payload = pickle.load(f)

        if isinstance(payload, dict) and "model" in payload:
            return LoadedModel(model=payload["model"], label_encoder=payload.get("label_encoder"))

        raise ValueError("Invalid XGBoost model payload format")

    def _load_random_forest_model(self, model_path: Path) -> LoadedModel:
        if not model_path.exists():
            raise FileNotFoundError(f"Missing model file: {model_path}")

        with model_path.open("rb") as f:
            model = pickle.load(f)

        return LoadedModel(model=model)

    def predict(self, features: dict[str, float], model_name: ModelName) -> str:
        loaded_model = self.models.get(model_name)
        if loaded_model is None:
            raise ValueError(f"Model '{model_name}' is not loaded")

        ordered = np.array([[features[name] for name in FEATURE_ORDER]], dtype=float)
        predicted = loaded_model.model.predict(ordered)

        if loaded_model.label_encoder is not None:
            decoded = loaded_model.label_encoder.inverse_transform(predicted)
            return str(decoded[0])

        return str(predicted[0])

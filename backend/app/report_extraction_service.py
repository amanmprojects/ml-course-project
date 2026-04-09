import json
import os
from base64 import b64encode

from openai import OpenAI

from .schemas import ExtractedValues

REQUIRED_FIELDS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


class ReportExtractionService:
    def __init__(self) -> None:
        pass

    def _settings(self) -> tuple[str, str, str]:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
        return api_key, base_url, model

    def _client(self) -> OpenAI:
        api_key, base_url, _ = self._settings()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured in backend environment")
        return OpenAI(api_key=api_key, base_url=base_url)

    def extract_values(self, image_bytes: bytes, mime_type: str) -> tuple[ExtractedValues, float]:
        _, _, model = self._settings()
        image_data_url = f"data:{mime_type};base64,{b64encode(image_bytes).decode('utf-8')}"
        client = self._client()

        schema = {
            "name": "crop_report_values",
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "N": {"type": ["number", "null"]},
                    "P": {"type": ["number", "null"]},
                    "K": {"type": ["number", "null"]},
                    "temperature": {"type": ["number", "null"]},
                    "humidity": {"type": ["number", "null"]},
                    "ph": {"type": ["number", "null"]},
                    "rainfall": {"type": ["number", "null"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": [
                    "N",
                    "P",
                    "K",
                    "temperature",
                    "humidity",
                    "ph",
                    "rainfall",
                    "confidence"
                ]
            },
            "strict": True
        }

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract agronomy lab report values from an image. "
                        "Return numeric values only. If uncertain, return null for that field."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract N, P, K, temperature, humidity, ph, and rainfall from the report. "
                                "Use null when value is missing or unreadable."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                },
            ],
            response_format={"type": "json_schema", "json_schema": schema},
        )

        content = completion.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM returned empty extraction payload")

        parsed = json.loads(content)
        confidence = float(parsed.pop("confidence", 0))

        values = ExtractedValues(**parsed)
        return values, confidence

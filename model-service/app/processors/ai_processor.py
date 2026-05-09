from abc import ABC, abstractmethod
from typing import Any
from app.config import settings
from app.model import ModelLoader, convert_tiff_to_png, CLASS_NAMES


class AIProcessorBase(ABC):
    @abstractmethod
    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class PlaceholderAIProcessor(AIProcessorBase):
    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "processed": True,
            "input_data": data,
            "result": "processed_placeholder_output",
        }


class DockAIProcessor(AIProcessorBase):
    def __init__(self):
        self.model_loader = ModelLoader()

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        images = data.get("images", [])
        predictions = []

        for item in images:
            try:
                image_bytes = item.get("bytes")
                image_key = item.get("key", "unknown")

                if not image_bytes:
                    predictions.append({
                        "key": image_key,
                        "success": False,
                        "error": "No image bytes provided",
                    })
                    continue

                png_bytes = convert_tiff_to_png(image_bytes)
                result = self.model_loader.predict(png_bytes)

                predictions.append({
                    "key": image_key,
                    "success": True,
                    "class_name": result["class_name"],
                    "confidence": result["confidence"],
                    "probabilities": result["probabilities"],
                })

            except Exception as e:
                predictions.append({
                    "key": item.get("key", "unknown"),
                    "success": False,
                    "error": str(e),
                })

        return {
            "processed": True,
            "predictions": predictions,
            "total_images": len(images),
            "successful": sum(1 for p in predictions if p.get("success")),
        }


def get_ai_processor() -> AIProcessorBase:
    model_type = settings.ai_model_type.lower() if settings.ai_model_type else ""

    if not model_type or model_type == "placeholder":
        return PlaceholderAIProcessor()
    elif model_type == "dock":
        return DockAIProcessor()
    else:
        raise NotImplementedError(f"AI model type '{settings.ai_model_type}' not implemented")
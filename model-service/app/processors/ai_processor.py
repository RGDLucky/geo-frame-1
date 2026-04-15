from abc import ABC, abstractmethod
from typing import Any
from app.config import settings


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


def get_ai_processor() -> AIProcessorBase:
    if not settings.ai_model_type:
        return PlaceholderAIProcessor()
    raise NotImplementedError(f"AI model type '{settings.ai_model_type}' not implemented")
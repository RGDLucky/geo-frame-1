from abc import ABC, abstractmethod
from typing import Any
import httpx
from app.config import settings


class ExternalAPIClientBase(ABC):
    @abstractmethod
    async def fetch(self, **kwargs) -> dict[str, Any]:
        raise NotImplementedError


class MockExternalAPIClient(ExternalAPIClientBase):
    async def fetch(self, **kwargs) -> dict[str, Any]:
        return {
            "data": [
                {"id": 1, "name": "Sample Record 1", "value": 100},
                {"id": 2, "name": "Sample Record 2", "value": 200},
            ],
            "timestamp": "2026-01-15T12:00:00Z",
        }


class ExternalAPIClient(ExternalAPIClientBase):
    def __init__(self):
        self.base_url = settings.external_api_url
        self.api_key = settings.external_api_key

    async def fetch(self, **kwargs) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = await client.get(self.base_url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()


def get_external_api_client() -> ExternalAPIClientBase:
    if not settings.external_api_url:
        return MockExternalAPIClient()
    return ExternalAPIClient()
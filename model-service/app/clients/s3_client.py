import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
import aiobotocore.session
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import settings


class S3ClientBase(ABC):
    @abstractmethod
    async def fetch(self, file_key: Optional[str] = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def find_latest_file(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def download_bytes(self, bucket: str, key: str) -> bytes:
        raise NotImplementedError


class MockS3Client(S3ClientBase):
    async def fetch(self, file_key: Optional[str] = None) -> dict[str, Any]:
        return {
            "data": [
                {"id": 1, "name": "Sample Record 1", "value": 100},
                {"id": 2, "name": "Sample Record 2", "value": 200},
            ],
            "timestamp": "2026-01-15T12:00:00Z",
        }

    async def find_latest_file(self) -> Optional[str]:
        return "data/mock/latest.json"

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        return b"mock_image_bytes"


class S3Client(S3ClientBase):
    def __init__(self):
        self.bucket = settings.s3_bucket_name
        self.region = settings.s3_region
        self.prefix = settings.s3_file_prefix
        self._session = None
        self._client = None
        self._client_lock = asyncio.Lock()

    async def _get_client(self):
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    config = Config(
                        connect_timeout=5,
                        read_timeout=60,
                        retries={"max_attempts": 3},
                    )
                    self._session = aiobotocore.session.get_session()
                    self._client = self._session.create_client(
                        "s3",
                        region_name=self.region,
                        config=config,
                    )
        return self._client

    def _extract_date_from_key(self, key: str) -> Optional[str]:
        parts = key.rstrip("/").split("/")
        if parts:
            filename = parts[-1]
            date_part = filename.replace(".json", "")
            if len(date_part) == 10 and date_part[4] == "-":
                return date_part
        return None

    async def find_latest_file(self) -> Optional[str]:
        if not self.bucket or not self.prefix:
            return None

        client = await self._get_client()
        latest_key = None
        latest_date = None

        try:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=self.bucket, Prefix=self.prefix
            ):
                if "Contents" not in page:
                    continue
                for obj in page["Contents"]:
                    key = obj["Key"]
                    date_str = self._extract_date_from_key(key)
                    if date_str:
                        try:
                            file_date = datetime.strptime(date_str, "%Y-%m-%d")
                            if latest_date is None or file_date > latest_date:
                                latest_date = file_date
                                latest_key = key
                        except ValueError:
                            continue
        except ClientError as e:
            raise Exception(f"Failed to list S3 objects: {e}") from e

        return latest_key

    async def fetch(self, file_key: Optional[str] = None) -> dict[str, Any]:
        if not self.bucket:
            raise Exception("S3 bucket not configured")

        if file_key is None:
            file_key = await self.find_latest_file()
            if file_key is None:
                raise Exception("No file found in S3 bucket")

        client = await self._get_client()

        try:
            response = await client.get_object(Bucket=self.bucket, Key=file_key)
            async with response as stream:
                body = await stream["Body"].read()
                data = json.loads(body.decode("utf-8"))
        except ClientError as e:
            raise Exception(f"Failed to fetch from S3: {e}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse S3 JSON: {e}") from e

        return data

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        client = await self._get_client()

        try:
            response = await client.get_object(Bucket=bucket, Key=key)
            async with response as stream:
                body = await stream["Body"].read()
                return body
        except ClientError as e:
            raise Exception(f"Failed to download from S3: {e}") from e


def get_s3_client() -> S3ClientBase:
    if not settings.s3_bucket_name:
        return MockS3Client()
    return S3Client()

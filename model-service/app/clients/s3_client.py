import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
import boto3
from botocore.exceptions import ClientError
from app.config import settings


class S3ClientBase(ABC):
    @abstractmethod
    async def fetch(self, file_key: Optional[str] = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def find_latest_file(self) -> Optional[str]:
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


class S3Client(S3ClientBase):
    def __init__(self):
        self.bucket = settings.s3_bucket_name
        self.region = settings.s3_region
        self.prefix = settings.s3_file_prefix
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    async def find_latest_file(self) -> Optional[str]:
        if not self.bucket or not self.prefix:
            return None

        paginator = self.client.get_paginator("list_objects_v2")
        operation_input = {
            "Bucket": self.bucket,
            "Prefix": self.prefix,
        }

        latest_key = None
        latest_date = None

        try:
            for page in paginator.paginate(**operation_input):
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

    def _extract_date_from_key(self, key: str) -> Optional[str]:
        parts = key.rstrip("/").split("/")
        if parts:
            filename = parts[-1]
            date_part = filename.replace(".json", "")
            if len(date_part) == 10 and date_part[4] == "-":
                return date_part
        return None

    async def fetch(self, file_key: Optional[str] = None) -> dict[str, Any]:
        if not self.bucket:
            raise Exception("S3 bucket not configured")

        if file_key is None:
            file_key = await self.find_latest_file()
            if file_key is None:
                raise Exception("No file found in S3 bucket")

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_key)
            body = response["Body"].read().decode("utf-8")
            data = json.loads(body)
        except ClientError as e:
            raise Exception(f"Failed to fetch from S3: {e}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse S3 JSON: {e}") from e

        return data


def get_s3_client() -> S3ClientBase:
    if not settings.s3_bucket_name:
        return MockS3Client()
    return S3Client()
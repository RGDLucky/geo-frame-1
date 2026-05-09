from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "model-service"
    api_host: str = "0.0.0.0"
    api_port: int = 50051
    rest_host: str = "0.0.0.0"
    rest_port: int = 8000
    database_url: str = "sqlite:///./geo_int.db"

    sync_interval_hours: float = 1.0
    sync_max_retries: int = 3
    sync_retry_backoff_seconds: int = 30

    s3_bucket_name: str = ""
    s3_region: str = "us-east-1"
    s3_file_prefix: str = ""

    ai_model_type: str = "placeholder"

    model_path: str = ""
    model_input_size: int = 260
    model_device: str = "cpu"

    class Config:
        env_file = ".env"

    @property
    def model_path_resolved(self) -> Path:
        if self.model_path:
            return Path(self.model_path)
        return Path(__file__).parent.parent.parent / "ml" / "checkpoints" / "best_model.pth"


settings = Settings()
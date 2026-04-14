from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "model-service"
    api_host: str = "0.0.0.0"
    api_port: int = 50051
    database_url: str = "sqlite:///./geo_int.db"

    class Config:
        env_file = ".env"

settings = Settings()
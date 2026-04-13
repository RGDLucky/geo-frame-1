from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI App"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
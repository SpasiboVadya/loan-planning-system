from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    DB_URL: Optional[str] = None  # Optional full DB URL
    DB_USER: str = "root"
    DB_PASSWORD: str = "Gcort_50"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "FastAPI_TEST"

    # API settings
    API_VERSION: str = "v1"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_default = True  # Updated from validate_all to validate_default for Pydantic v2

    @property
    def sync_db_url(self) -> str:
        """Get synchronous database URL."""
        if self.DB_URL:
            return self.DB_URL.replace("mysql+aiomysql", "mysql+pymysql")
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def async_db_url(self) -> str:
        """Get asynchronous database URL."""
        if self.DB_URL:
            return self.DB_URL
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance to avoid reloading .env file on every access
    """
    return Settings()


settings = get_settings()

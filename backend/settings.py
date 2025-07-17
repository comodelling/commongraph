import os
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    ENABLE_GRAPH_DB: bool = False
    JANUSGRAPH_HOST: str = "localhost"
    TRAVERSAL_SOURCE: str = "g_test"
    BACKEND_HOST: str                # e.g. https://api.commongraph.org or http://localhost:8000
    FRONTEND_HOST: str               # e.g. https://commongraph.org or http://localhost:5173
    POSTGRES_DB_URL: str
    ALLOWED_ORIGINS_RAW: str = ""
    INITIAL_ADMIN_USER: str
    INITIAL_ADMIN_PASSWORD: str

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if not self.ALLOWED_ORIGINS_RAW:
            return []
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS_RAW.split(",")
            if origin.strip()
        ]

    class Config:
        # base_dir is two levels up from this file
        base_dir = Path(__file__).parent.parent
        # pick an environment name, default to “development”
        app_env = os.getenv("APP_ENV", "development")
        # load .env first, then .env.<environment> to override
        env_file = [
            base_dir / ".env",
            base_dir / f".env.{app_env}"
        ]
        env_file_encoding = "utf-8"

settings = Settings()
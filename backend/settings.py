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
    QUOTES_FILE: str = ""
    ALLOWED_ORIGINS_RAW: str = ""               # <<< raw comma-sep string
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
        # load root-level .env overrides
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"

settings = Settings()
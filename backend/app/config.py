import os
from pathlib import Path
from typing import List, Optional, Any
from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "KANAKKUFLOW"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # JWT & Security
    SECRET_KEY: str = Field(
        default="kanakkuflow_super_secret_jwt_key_nit_trichy_2026_challenge",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "kanakkuflow"
    DATABASE_URL: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                import json
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [origin.strip() for origin in v_trimmed.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Business defaults
    BENCHMARK_GST_RATE: float = 0.05
    BENCHMARK_HSN: str = "1905"
    DEFAULT_VARIANCE_TOLERANCE_PCT: float = 3.0
    
    # App
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # Normalize postgres:// or postgresql:// to postgresql+psycopg://
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+psycopg://", 1)
            return url

        # When running in serverless environments (e.g. Vercel) or when external DB is not configured,
        # fallback to the pre-seeded SQLite database so demo logins & ERP features function out of the box.
        is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
        seed_db = Path(__file__).resolve().parent / "seed_data.db"

        if is_serverless:
            import tempfile
            import shutil
            tmp_db = Path(tempfile.gettempdir()) / "kanakkuflow.db"
            if not tmp_db.exists() and seed_db.exists():
                try:
                    shutil.copyfile(seed_db, tmp_db)
                except Exception:
                    pass
            if tmp_db.exists():
                return f"sqlite:///{tmp_db.as_posix()}"
            if seed_db.exists():
                return f"sqlite:///{seed_db.as_posix()}"

        # Local development SQLite fallback if available
        local_db = Path.cwd() / "kanakkuflow.db"
        if local_db.exists():
            return f"sqlite:///{local_db.as_posix()}"
        if seed_db.exists():
            return f"sqlite:///{seed_db.as_posix()}"

        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

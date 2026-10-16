
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PASTA_APP = Path(__file__).resolve().parents[1]
ARQUIVO_ENV = PASTA_APP / ".env"


class Settings(BaseSettings):
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    ssh_password: str | None = None

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "sistema-estacionamento"

    model_config = SettingsConfigDict(
        env_file=ARQUIVO_ENV,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

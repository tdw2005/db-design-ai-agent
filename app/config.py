from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


@dataclass(slots=True)
class Settings:
    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    mysql_root_password: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mysql_host=_get_env("MYSQL_HOST", "db"),
            mysql_port=int(_get_env("MYSQL_PORT", "3306")),
            mysql_database=_get_env("MYSQL_DATABASE", "erp_crm_demo"),
            mysql_user=_get_env("MYSQL_USER", "app_user"),
            mysql_password=_get_env("MYSQL_PASSWORD", "app_password"),
            mysql_root_password=_get_env("MYSQL_ROOT_PASSWORD", "root_password"),
            openai_api_key=_get_env("OPENAI_API_KEY", ""),
            openai_base_url=_get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
            openai_model=_get_env("OPENAI_MODEL", "deepseek-chat"),
        )

    def mysql_connection_kwargs(self) -> dict[str, object]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
            "charset": "utf8mb4",
            "autocommit": False,
        }


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

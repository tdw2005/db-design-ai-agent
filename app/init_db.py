from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.db_executor import DatabaseExecutor


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "schema.sql"


def main() -> None:
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"schema.sql not found: {SCHEMA_FILE}")

    settings = Settings.from_env()
    executor = DatabaseExecutor(settings)
    executor.wait_until_ready()
    executor.execute_sql(SCHEMA_FILE.read_text(encoding="utf-8"))
    print("Database schema initialized successfully.")


if __name__ == "__main__":
    main()

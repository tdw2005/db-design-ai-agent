from __future__ import annotations

import time

import pymysql

from app.config import Settings


class DatabaseExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def wait_until_ready(self, retries: int = 20, interval_seconds: int = 3) -> None:
        last_error: Exception | None = None
        for _ in range(retries):
            try:
                with pymysql.connect(**self.settings.mysql_connection_kwargs()):
                    return
            except Exception as exc:  # pragma: no cover - runtime connectivity guard
                last_error = exc
                time.sleep(interval_seconds)
        raise RuntimeError("Database is not ready.") from last_error

    def execute_sql(self, sql: str) -> None:
        statements = _split_sql_statements(sql)
        with pymysql.connect(**self.settings.mysql_connection_kwargs()) as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)
            connection.commit()


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    in_single_quote = False
    in_double_quote = False

    for char in sql:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote

        if char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            continue

        buffer.append(char)

    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)

    return statements

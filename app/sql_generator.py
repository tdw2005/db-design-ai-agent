from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from app.llm import ChatMessage, DeepSeekClient


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = PROJECT_ROOT / "SKILL.md"


@dataclass(slots=True)
class DesignArtifact:
    summary: str
    mermaid: str
    sql: str


class DatabaseDesignGenerator:
    def __init__(self, client: DeepSeekClient) -> None:
        self.client = client

    def generate(self, requirement: str) -> DesignArtifact:
        skill_prompt = SKILL_FILE.read_text(encoding="utf-8")
        user_prompt = (
            "请根据下面的自然语言需求生成数据库设计结果，并严格遵循输出契约。\n"
            "需求如下：\n"
            f"{requirement.strip()}\n"
        )
        response = self.client.chat(
            [
                ChatMessage(role="system", content=skill_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
        )
        payload = _extract_json(response)
        artifact = DesignArtifact(
            summary=payload["summary"].strip(),
            mermaid=payload["mermaid"].strip(),
            sql=payload["sql"].strip(),
        )
        _validate_sql(artifact.sql)
        return artifact


def _extract_json(text: str) -> dict[str, str]:
    fenced_match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    object_match = re.search(r"(\{[\s\S]*\})", text)
    if object_match:
        return json.loads(object_match.group(1))

    raise ValueError("LLM response does not contain a valid JSON object.")


def _validate_sql(sql: str) -> None:
    statements = _split_sql_statements(sql)
    if not statements:
        raise ValueError("Generated SQL is empty.")

    create_table_statements: list[str] = []
    for statement in statements:
        normalized_statement = _strip_leading_sql_comments(statement).strip()
        if not normalized_statement:
            continue
        if re.match(r"^\s*CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\b", normalized_statement, re.IGNORECASE):
            create_table_statements.append(normalized_statement)
            continue
        if re.match(r"^\s*CREATE\s+TABLE\b", normalized_statement, re.IGNORECASE):
            raise ValueError("Every CREATE TABLE statement must use IF NOT EXISTS.")
        if re.match(
            r"^\s*(DROP|TRUNCATE|DELETE|UPDATE|INSERT|ALTER|RENAME|USE)\b",
            normalized_statement,
            re.IGNORECASE,
        ):
            raise ValueError("Generated SQL contains unsupported or potentially destructive statements.")
        raise ValueError("Generated SQL may only contain CREATE TABLE statements.")

    if not create_table_statements:
        raise ValueError("Generated SQL does not contain any CREATE TABLE IF NOT EXISTS statements.")

    for statement in create_table_statements:
        _validate_create_table_statement(statement)


def _validate_create_table_statement(statement: str) -> None:
    table_name = _extract_table_name(statement)
    body = _extract_table_body(statement)
    definitions = _split_top_level_items(body)
    column_definitions = _extract_column_definitions(definitions)

    if not re.search(r"ENGINE\s*=\s*INNODB\b", statement, re.IGNORECASE):
        raise ValueError(f"Table `{table_name}` must use ENGINE=InnoDB.")
    if not re.search(r"CHARSET\s*=\s*utf8mb4\b", statement, re.IGNORECASE):
        raise ValueError(f"Table `{table_name}` must use utf8mb4 charset.")
    if "created_at" not in column_definitions:
        raise ValueError(f"Table `{table_name}` is missing created_at column.")
    if "updated_at" not in column_definitions:
        raise ValueError(f"Table `{table_name}` is missing updated_at column.")
    _validate_timestamp_columns(table_name, column_definitions)

    primary_key_columns = _extract_primary_key_columns(definitions)
    if len(primary_key_columns) != 1:
        raise ValueError(f"Table `{table_name}` must define a single-column primary key.")

    primary_key_column = primary_key_columns[0]
    primary_key_definition = column_definitions.get(primary_key_column)
    if primary_key_definition is None:
        raise ValueError(
            f"Table `{table_name}` primary key column `{primary_key_column}` is not defined."
        )

    normalized_primary_key = primary_key_definition.upper()
    required_primary_key_parts = [
        "BIGINT",
        "UNSIGNED",
        "NOT NULL",
        "AUTO_INCREMENT",
    ]
    for part in required_primary_key_parts:
        if part not in normalized_primary_key:
            raise ValueError(
                f"Table `{table_name}` primary key column `{primary_key_column}` "
                f"must include `{part}`."
            )

    indexed_columns = _extract_indexed_columns(definitions)
    foreign_key_columns = _extract_foreign_key_columns(definitions)
    for foreign_key_column in foreign_key_columns:
        foreign_key_definition = column_definitions.get(foreign_key_column)
        if foreign_key_definition is None:
            raise ValueError(
                f"Table `{table_name}` foreign key column `{foreign_key_column}` is not defined."
            )

        normalized_foreign_key = foreign_key_definition.upper()
        if "BIGINT" not in normalized_foreign_key or "UNSIGNED" not in normalized_foreign_key:
            raise ValueError(
                f"Table `{table_name}` foreign key column `{foreign_key_column}` "
                "must use BIGINT UNSIGNED to match referenced primary keys."
            )
        if foreign_key_column not in indexed_columns:
            raise ValueError(
                f"Table `{table_name}` foreign key column `{foreign_key_column}` "
                "must have an explicit index."
            )


def _validate_timestamp_columns(table_name: str, column_definitions: dict[str, str]) -> None:
    created_at_definition = column_definitions["created_at"].upper()
    if "TIMESTAMP" not in created_at_definition and "DATETIME" not in created_at_definition:
        raise ValueError(f"Table `{table_name}` created_at must use TIMESTAMP or DATETIME.")
    if "DEFAULT CURRENT_TIMESTAMP" not in created_at_definition:
        raise ValueError(f"Table `{table_name}` created_at must default to CURRENT_TIMESTAMP.")

    updated_at_definition = column_definitions["updated_at"].upper()
    if "TIMESTAMP" not in updated_at_definition and "DATETIME" not in updated_at_definition:
        raise ValueError(f"Table `{table_name}` updated_at must use TIMESTAMP or DATETIME.")
    if "DEFAULT CURRENT_TIMESTAMP" not in updated_at_definition:
        raise ValueError(f"Table `{table_name}` updated_at must default to CURRENT_TIMESTAMP.")
    if "ON UPDATE CURRENT_TIMESTAMP" not in updated_at_definition:
        raise ValueError(
            f"Table `{table_name}` updated_at must include ON UPDATE CURRENT_TIMESTAMP."
        )


def _extract_table_name(statement: str) -> str:
    match = re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+`?([A-Za-z_][A-Za-z0-9_]*)`?",
        statement,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError("Unable to parse table name from generated SQL.")
    return match.group(1)


def _extract_table_body(statement: str) -> str:
    open_index = statement.find("(")
    if open_index == -1:
        raise ValueError("CREATE TABLE statement is missing column definitions.")

    depth = 0
    in_single_quote = False
    in_double_quote = False

    for index in range(open_index, len(statement)):
        char = statement[index]
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return statement[open_index + 1 : index]

    raise ValueError("Unable to locate the end of CREATE TABLE column definitions.")


def _split_top_level_items(text: str) -> list[str]:
    items: list[str] = []
    buffer: list[str] = []
    depth = 0
    in_single_quote = False
    in_double_quote = False

    for char in text:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                item = "".join(buffer).strip()
                if item:
                    items.append(item)
                buffer = []
                continue

        buffer.append(char)

    tail = "".join(buffer).strip()
    if tail:
        items.append(tail)
    return items


def _extract_column_definitions(definitions: list[str]) -> dict[str, str]:
    columns: dict[str, str] = {}
    for definition in definitions:
        stripped = definition.strip()
        upper = stripped.upper()
        if upper.startswith(("PRIMARY KEY", "UNIQUE KEY", "KEY ", "INDEX ", "CONSTRAINT", "UNIQUE ")):
            continue

        match = re.match(r"`?([A-Za-z_][A-Za-z0-9_]*)`?\s+.+", stripped)
        if match:
            columns[match.group(1)] = stripped
    return columns


def _extract_primary_key_columns(definitions: list[str]) -> list[str]:
    for definition in definitions:
        match = re.search(r"PRIMARY\s+KEY\s*\(([^)]+)\)", definition, re.IGNORECASE)
        if match:
            return [
                column.strip().strip("`")
                for column in match.group(1).split(",")
                if column.strip()
            ]
    return []


def _extract_indexed_columns(definitions: list[str]) -> set[str]:
    indexed_columns: set[str] = set()
    for definition in definitions:
        match = re.search(
            r"(?:PRIMARY\s+KEY|UNIQUE\s+KEY|UNIQUE|KEY|INDEX)\s*(?:`?[A-Za-z0-9_]+`?)?\s*\(([^)]+)\)",
            definition,
            re.IGNORECASE,
        )
        if not match:
            continue

        for column in match.group(1).split(","):
            cleaned = column.strip().strip("`")
            if cleaned:
                indexed_columns.add(cleaned)
    return indexed_columns


def _extract_foreign_key_columns(definitions: list[str]) -> set[str]:
    foreign_key_columns: set[str] = set()
    for definition in definitions:
        match = re.search(r"FOREIGN\s+KEY\s*\(([^)]+)\)", definition, re.IGNORECASE)
        if not match:
            continue

        for column in match.group(1).split(","):
            cleaned = column.strip().strip("`")
            if cleaned:
                foreign_key_columns.add(cleaned)
    return foreign_key_columns


def _strip_leading_sql_comments(statement: str) -> str:
    stripped = statement.lstrip()
    while True:
        if stripped.startswith("--"):
            newline_index = stripped.find("\n")
            if newline_index == -1:
                return ""
            stripped = stripped[newline_index + 1 :].lstrip()
            continue
        if stripped.startswith("#"):
            newline_index = stripped.find("\n")
            if newline_index == -1:
                return ""
            stripped = stripped[newline_index + 1 :].lstrip()
            continue
        if stripped.startswith("/*"):
            block_end = stripped.find("*/")
            if block_end == -1:
                return ""
            stripped = stripped[block_end + 2 :].lstrip()
            continue
        return stripped


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

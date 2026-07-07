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
    normalized_sql = sql.upper()
    required_keywords = [
        "CREATE TABLE IF NOT EXISTS",
        "ENGINE=INNODB",
        "CHARSET=UTF8MB4",
        "CREATED_AT",
        "UPDATED_AT",
    ]
    for keyword in required_keywords:
        if keyword not in normalized_sql:
            raise ValueError(f"Generated SQL is missing required keyword: {keyword}")

from __future__ import annotations

from dataclasses import dataclass

import requests

from app.config import Settings


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def chat(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

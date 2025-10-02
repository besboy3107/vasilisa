from __future__ import annotations
import json
import re
from typing import Any, Dict

from .config import Config


def _extract_json(text: str) -> str:
    # Try to extract the first {...} block as JSON
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else text


def _build_prompt(topic: str) -> str:
    return (
        "Сгенерируй статью на русском строго в формате JSON с полями:\n"
        "{\n"
        "  \"title\": \"...\",\n"
        "  \"subtitle\": \"...\",\n"
        "  \"slug\": \"kebab-case\",\n"
        "  \"keywords\": [\"...\", \"...\"],\n"
        "  \"description\": \"meta description, 140-160 символов\",\n"
        "  \"sections\": [\n"
        "    {\"heading\": \"H2\", \"content_md\": \"markdown контент 120-200 слов\"}\n"
        "  ],\n"
        "  \"image_queries\": [\n"
        "    {\"topic\": \"кратко, что искать для обложки\", \"style\": \"cinematic, vibrant, colorful\"}\n"
        "  ],\n"
        "  \"sources\": [{\"title\":\"...\", \"url\":\"...\"}]\n"
        "}\n\n"
        "Требования: 800-1200 слов, краткие абзацы, списки, примеры. Не выдумывай факты;"
        " если не уверен — пиши общими словами. Тон — экспертно, дружелюбно."
        f"\nТема: {topic}\n"
    )


def generate_article_payload(topic: str, cfg: Config) -> Dict[str, Any]:
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover - import-time failure
        raise RuntimeError("openai package is required. Add to requirements.txt and install.") from e

    if not cfg.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=cfg.openai_api_key, base_url=cfg.openai_base_url or None)

    system_msg = (
        "Ты — опытный редактор. Пиши структурированные, читабельные статьи."
        " Возвращай только валидный JSON без пояснений."
    )
    user_msg = _build_prompt(topic)

    # Use Chat Completions for broad compatibility
    resp = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.7,
    )

    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except Exception:
        return json.loads(_extract_json(text))

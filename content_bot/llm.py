def _build_prompt(topic: str, target_chars: int | None = None) -> str:
    limit = f" Ограничь общий объём примерно {target_chars} символов." if target_chars else ""
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
        "Требования: краткие абзацы, списки, примеры. Не выдумывай факты;"
        " если не уверен — пиши общими словами. Тон — экспертно, дружелюбно."
        + limit
        + f"\nТема: {topic}\n"
    )

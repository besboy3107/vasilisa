from __future__ import annotations
import json
import re
from typing import Any, Dict

from .config import Config
import requests


def _extract_json(text: str) -> str:
    # Try to extract the first {...} block as JSON
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else text


def _build_prompt(topic: str, target_chars: int | None = None) -> str:
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
        + (f" Ограничь общий объём примерно {target_chars} символов." if target_chars else "")
        f"\nТема: {topic}\n"
    )


def generate_article_payload(topic: str, cfg: Config, *, target_chars: int | None = None) -> Dict[str, Any]:
    if cfg.llm_provider == "gigachat":
        return _generate_with_gigachat(topic, cfg)
    # default: openai-compatible
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("openai package is required. Add to requirements.txt and install.") from e

    if not cfg.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=cfg.openai_api_key, base_url=cfg.openai_base_url or None)

    system_msg = (
        "Ты — опытный редактор. Пиши структурированные, читабельные статьи."
        " Возвращай только валидный JSON без пояснений."
    )
    user_msg = _build_prompt(topic, target_chars)

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


def _gigachat_get_token(cfg: Config) -> str:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {
        "scope": cfg.gigachat_scope,
        "grant_type": "client_credentials",
    }
    auth = None
    if cfg.gigachat_basic:
        headers["Authorization"] = f"Basic {cfg.gigachat_basic}"
    else:
        auth = (cfg.gigachat_client_id or "", cfg.gigachat_client_secret or "")
    verify = cfg.gigachat_verify_ssl
    resp = requests.post(cfg.gigachat_token_url, headers=headers, data=data, auth=auth, verify=verify, timeout=30)
    resp.raise_for_status()
    return resp.json().get("access_token")


def _generate_with_gigachat(topic: str, cfg: Config, *, target_chars: int | None = None) -> Dict[str, Any]:
    if not (cfg.gigachat_basic or (cfg.gigachat_client_id and cfg.gigachat_client_secret)):
        raise RuntimeError("Provide GIGACHAT_BASIC or both GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET")

    token = _gigachat_get_token(cfg)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": "GigaChat",  # default model name per API
        "messages": [
            {"role": "system", "content": "Ты — опытный редактор. Возвращай только валидный JSON."},
            {"role": "user", "content": _build_prompt(topic, target_chars)},
        ],
        "temperature": 0.7,
    }
    verify = cfg.gigachat_verify_ssl
    resp = requests.post(f"{cfg.gigachat_base_url}/chat/completions", headers=headers, json=payload, verify=verify, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        return json.loads(text)
    except Exception:
        return json.loads(_extract_json(text))

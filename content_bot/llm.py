from __future__ import annotations
import json, re, requests
from typing import Any, Dict
from .config import Config

def _extract_json(text: str) -> str:
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else text

def _build_prompt(topic: str) -> str:
    return (
        "Сгенерируй статью на русском строго в формате JSON с полями:\n"
        "{\n"
        '  "title": "...",\n'
        '  "subtitle": "...",\n'
        '  "slug": "kebab-case",\n'
        '  "keywords": ["...", "..."],\n'
        '  "description": "meta description, 140-160 символов",\n'
        '  "sections": [\n'
        '    {"heading": "H2", "content_md": "markdown контент 120-200 слов"}\n'
        "  ],\n"
        '  "image_queries": [\n'
        '    {"topic": "кратко, что искать для обложки", "style": "cinematic, vibrant, colorful"}\n'
        "  ],\n"
        '  "sources": [{"title":"...", "url":"..."}]\n'
        "}\n\n"
        "Требования: 800-1200 слов, краткие абзацы, списки, примеры. Не выдумывай факты; "
        "если не уверен — пиши общими словами. Тон — экспертно, дружелюбно."
        f"\nТема: {topic}\n"
    )

def generate_article_payload(topic: str, cfg: Config) -> Dict[str, Any]:
    if cfg.llm_provider == "gigachat":
        return _generate_with_gigachat(topic, cfg)
    from openai import OpenAI  # type: ignore
    if not cfg.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=cfg.openai_api_key, base_url=cfg.openai_base_url or None)
    resp = client.chat.completions.create(
        model=cfg.openai_model,
        messages=[
            {"role": "system", "content": "Ты — опытный редактор. Возвращай только валидный JSON."},
            {"role": "user", "content": _build_prompt(topic)},
        ],
        temperature=0.7,
    )
    text = resp.choices[0].message.content or "{}"
    try:
        return json.loads(text)
    except Exception:
        return json.loads(_extract_json(text))

def _gigachat_get_token(cfg: Config) -> str:
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = {"scope": cfg.gigachat_scope, "grant_type": "client_credentials"}
    auth = None
    if cfg.gigachat_basic:
        headers["Authorization"] = f"Basic {cfg.gigachat_basic}"
    else:
        auth = (cfg.gigachat_client_id or "", cfg.gigachat_client_secret or "")
    resp = requests.post(cfg.gigachat_token_url, headers=headers, data=data, auth=auth,
                         verify=cfg.gigachat_verify_ssl, timeout=30)
    resp.raise_for_status()
    return resp.json().get("access_token")

def _generate_with_gigachat(topic: str, cfg: Config) -> Dict[str, Any]:
    if not (cfg.gigachat_basic or (cfg.gigachat_client_id and cfg.gigachat_client_secret)):
        raise RuntimeError("Provide GIGACHAT_BASIC or both GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET")
    token = _gigachat_get_token(cfg)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": "Ты — опытный редактор. Возвращай только валидный JSON."},
            {"role": "user", "content": _build_prompt(topic)},
        ],
        "temperature": 0.7,
    }
    resp = requests.post(f"{cfg.gigachat_base_url}/chat/completions", headers=headers, json=payload,
                         verify=cfg.gigachat_verify_ssl, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
    try:
        return json.loads(text)
    except Exception:
        return json.loads(_extract_json(text))

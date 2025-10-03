from __future__ import annotations
import sys, time
from pathlib import Path
from typing import Optional, Dict, Any, List
import click
from slugify import slugify
from .config import load_config
from .topics import load_topics
from .llm import generate_article_payload
from .writer import write_markdown

@click.group()
def cli() -> None:
    pass

@cli.command()
@click.option("--count", default=10, show_default=True, type=int)
@click.option("--topics-file", type=click.Path(path_type=Path))
@click.option("--output-dir", type=click.Path(path_type=Path))
@click.option("--date", "date_str", type=str)
@click.option("--target-chars", type=int, help="Approximate total characters per article body")
def generate(count: int, topics_file: Optional[Path], output_dir: Optional[Path], date_str: Optional[str], target_chars: Optional[int]) -> None:
    cfg = load_config()
    if output_dir is None:
        output_dir = cfg.content_base_dir
    from datetime import datetime, timezone
    date_dir = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    topics = load_topics(count, topics_file)
    if not topics:
        click.echo("No topics found", err=True)
        sys.exit(1)

    generated = 0

    def _fallback_post(topic_text: str) -> Dict[str, Any]:
        title = topic_text.strip()[:80]
        return {
            "title": title,
            "subtitle": "Черновик статьи",
            "slug": slugify(title),
            "keywords": ["черновик", "статья"],
            "description": "Автоматически сгенерированный черновик статьи.",
            "sections": [
                {"heading": "Введение", "content_md": "Черновик создан автоматически. Обновите ключи LLM и перезапустите."},
                {"heading": "Основные идеи", "content_md": "Опишите ключевые тезисы по теме и добавьте примеры."},
                {"heading": "Выводы", "content_md": "Сформулируйте краткие выводы и список действий."},
            ],
            "image_queries": [{"topic": topic_text, "style": "vibrant, cinematic"}],
            "sources": [],
        }

    for idx, topic in enumerate(topics[:count], start=1):
        click.echo(f"[{idx}/{count}] Topic: {topic}")
        try:
            post = generate_article_payload(topic, cfg, target_chars=target_chars)
        except Exception as e:
            click.echo(f"  LLM error: {e}", err=True)
            post = _fallback_post(topic)
        slug = post.get("slug") or slugify(post.get("title") or topic)
        out_dir = (output_dir / date_dir / slug)
        write_markdown(post, [], out_dir, target_chars=target_chars)
        generated += 1
        time.sleep(0.5)

    if generated == 0:
        click.echo("No articles generated", err=True)
        raise SystemExit(1)
    click.echo(f"Done. Generated {generated} article(s).")
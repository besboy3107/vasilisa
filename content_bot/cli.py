from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import click
from slugify import slugify

from .config import load_config
from .topics import load_topics
from .llm import generate_article_payload
from .images import search_images, download_image
from .writer import write_markdown


@click.group()
def cli() -> None:
    """Content bot CLI."""


@cli.command()
@click.option("--count", default=10, show_default=True, type=int, help="How many articles to generate")
@click.option("--topics-file", type=click.Path(path_type=Path), help="Optional file with topics (one per line)")
@click.option("--output-dir", type=click.Path(path_type=Path), help="Base content directory")
@click.option("--date", "date_str", type=str, help="YYYY-MM-DD for subdir; default: today UTC")
@click.option("--provider", type=click.Choice(["unsplash", "pexels", "pixabay"]), help="Image provider override")
@click.option("--inline-images", type=int, help="Number of inline images per article")
def generate(count: int, topics_file: Optional[Path], output_dir: Optional[Path], date_str: Optional[str], provider: Optional[str], inline_images: Optional[int]) -> None:
    """Generate N articles with images into content/DATE/SLUG."""
    cfg = load_config()

    if output_dir is None:
        output_dir = cfg.content_base_dir
    if provider is None:
        provider = cfg.image_provider
    if inline_images is None:
        inline_images = cfg.inline_images

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
                {
                    "heading": "Введение",
                    "content_md": "Черновик создан автоматически, так как основной провайдер контента недоступен. Обновите ключи API и перезапустите генерацию.",
                },
                {
                    "heading": "Основные идеи",
                    "content_md": "Опишите ключевые тезисы по теме и добавьте примеры.",
                },
                {
                    "heading": "Выводы",
                    "content_md": "Сформулируйте краткие выводы и список действий.",
                },
            ],
            "image_queries": [{"topic": topic_text, "style": "vibrant, cinematic"}],
            "sources": [],
        }

    for idx, topic in enumerate(topics[:count], start=1):
        click.echo(f"[{idx}/{count}] Topic: {topic}")
        try:
            post = generate_article_payload(topic, cfg)
        except Exception as e:
            click.echo(f"  LLM error: {e}", err=True)
            post = _fallback_post(topic)

        slug = post.get("slug") or slugify(post.get("title") or topic)
        out_dir = (output_dir / date_dir / slug)
        images_meta: List[Dict[str, Any]] = []

        # Cover image
        image_queries = post.get("image_queries", []) or [{"topic": topic, "style": "vibrant"}]
        cover_query = image_queries[0].get("topic") if image_queries else topic
        try:
            results = search_images(
                query=cover_query,
                provider=provider,
                per_page=3,
                unsplash_access_key=cfg.unsplash_access_key,
                pexels_api_key=cfg.pexels_api_key,
                timeout=cfg.request_timeout_seconds,
            )
            if results:
                cover_path = out_dir / "images" / "cover.jpg"
                download_image(results[0].url, cover_path, timeout=cfg.request_timeout_seconds)
                images_meta.append({
                    "role": "cover",
                    "file": "images/cover.jpg",
                    "author": results[0].author,
                    "link": results[0].link,
                    "source": results[0].source,
                })
        except Exception as e:
            click.echo(f"  Image search error: {e}")

        # Inline images
        for qidx, imgq in enumerate(image_queries[1: inline_images + 1], start=1):
            q = imgq.get("topic") or topic
            try:
                res = search_images(
                    query=q,
                    provider=provider,
                    per_page=1,
                    unsplash_access_key=cfg.unsplash_access_key,
                    pexels_api_key=cfg.pexels_api_key,
                    timeout=cfg.request_timeout_seconds,
                )
                if res:
                    p = out_dir / "images" / f"img{qidx}.jpg"
                    download_image(res[0].url, p, timeout=cfg.request_timeout_seconds)
                    images_meta.append({
                        "role": f"inline{qidx}",
                        "file": f"images/img{qidx}.jpg",
                        "author": res[0].author,
                        "link": res[0].link,
                        "source": res[0].source,
                    })
            except Exception:
                continue

        write_markdown(post, images_meta, out_dir)
        generated += 1
        time.sleep(0.5)

    if generated == 0:
        click.echo("No articles generated", err=True)
        raise SystemExit(1)
    click.echo(f"Done. Generated {generated} article(s).")

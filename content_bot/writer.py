from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
import yaml


def _yaml_dump(data: Dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def write_markdown(post: Dict[str, Any], images_meta: List[Dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "title": post.get("title"),
        "subtitle": post.get("subtitle"),
        "date": datetime.now(timezone.utc).isoformat(),
        "description": post.get("description"),
        "keywords": post.get("keywords", []),
        "images": images_meta,
        "sources": post.get("sources", []),
    }
    sections = post.get("sections", [])
    body_parts: List[str] = []
    for sec in sections:
        heading = sec.get("heading", "")
        content_md = sec.get("content_md", "")
        body_parts.append(f"## {heading}\n\n{content_md}")
    body_md = "\n\n".join(body_parts)

    md = f"---\n{_yaml_dump(frontmatter)}---\n\n" + body_md
    (out_dir / "index.md").write_text(md, encoding="utf-8")

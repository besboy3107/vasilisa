from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import yaml

def _yaml_dump(data: Dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)

def write_markdown(post: Dict[str, Any], images_meta: List[Dict[str, Any]], out_dir: Path, target_chars: Optional[int] = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "title": post.get("title"),
        "subtitle": post.get("subtitle"),
        "date": datetime.now(timezone.utc).isoformat(),
        "description": post.get("description"),
        "keywords": post.get("keywords", []),
        "sources": post.get("sources", []),
    }
    if images_meta:
        frontmatter["images"] = images_meta
    sections = post.get("sections", [])
    body_parts: List[str] = []
    for sec in sections:
        heading = sec.get("heading", "")
        content_md = sec.get("content_md", "")
        body_parts.append(f"## {heading}\n\n{content_md}")
    body_md = "\n\n".join(body_parts)

    if target_chars is not None and target_chars > 0 and len(body_md) > target_chars:
        cut = body_md[:target_chars]
        last_space = cut.rfind(" ")
        if last_space != -1 and last_space > int(target_chars * 0.6):
            cut = cut[:last_space]
        body_md = cut.rstrip() + "…"

    md = f"---\n{_yaml_dump(frontmatter)}---\n\n" + body_md
    (out_dir / "index.md").write_text(md, encoding="utf-8")

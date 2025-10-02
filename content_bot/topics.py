from __future__ import annotations
from pathlib import Path
from typing import List, Optional


def load_topics(count: int, topics_file: Optional[Path] = None) -> List[str]:
    if topics_file and topics_file.exists():
        lines = [ln.strip() for ln in topics_file.read_text(encoding="utf-8").splitlines()]
        topics = [ln for ln in lines if ln and not ln.startswith("#")] 
        if len(topics) >= count:
            return topics[:count]
        return topics

    # Fallback sample topics; replace with your domain
    seed = [
        "Тренды ИИ для контент-маркетинга",
        "UX-советы для лендингов 2025",
        "Как написать продающий лид-абзац",
        "SEO: внутренняя перелинковка без боли",
        "Подбор изображений: стоки vs генерация",
        "Структура идеальной статьи 1000 слов",
        "Оформление обложки: принципы и примеры",
        "Как планировать контент на неделю",
        "Проверка фактов: быстрый чек-лист",
        "Как избежать плагиата при генерации",
        "JSON-LD для статей: кратко",
        "Оптимизация alt-текстов для картинок",
    ]
    return seed[:count]

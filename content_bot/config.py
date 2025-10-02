import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # optional at runtime if not installed
    load_dotenv = None  # type: ignore


@dataclass
class Config:
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    openai_model: str

    unsplash_access_key: Optional[str]
    pexels_api_key: Optional[str]
    image_provider: str  # "unsplash" | "pexels"

    content_base_dir: Path
    articles_per_day: int
    inline_images: int
    request_timeout_seconds: int


def load_config(env_path: Optional[Path] = None) -> Config:
    if load_dotenv is not None:
        if env_path is None:
            env_path = Path(os.getcwd()) / ".env"
        if env_path.exists():
            load_dotenv(env_path)  # load if present

    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    image_provider = os.getenv("IMAGE_PROVIDER", "unsplash").lower()

    content_base_dir = Path(os.getenv("CONTENT_BASE_DIR", "content")).resolve()
    articles_per_day = int(os.getenv("ARTICLES_PER_DAY", "10"))
    inline_images = int(os.getenv("INLINE_IMAGES", "2"))
    request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    return Config(
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_model=openai_model,
        unsplash_access_key=unsplash_access_key,
        pexels_api_key=pexels_api_key,
        image_provider=image_provider,
        content_base_dir=content_base_dir,
        articles_per_day=articles_per_day,
        inline_images=inline_images,
        request_timeout_seconds=request_timeout_seconds,
    )

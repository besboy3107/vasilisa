import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore

@dataclass
class Config:
    llm_provider: str  # "openai" | "gigachat"

    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    openai_model: str

    gigachat_client_id: Optional[str]
    gigachat_client_secret: Optional[str]
    gigachat_basic: Optional[str]
    gigachat_scope: str
    gigachat_base_url: str
    gigachat_token_url: str
    gigachat_verify_ssl: bool

    content_base_dir: Path
    articles_per_day: int
    inline_images: int
    request_timeout_seconds: int

def load_config(env_path: Optional[Path] = None) -> Config:
    if load_dotenv is not None:
        if env_path is None:
            env_path = Path(os.getcwd()) / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    gigachat_client_id = os.getenv("GIGACHAT_CLIENT_ID")
    gigachat_client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
    gigachat_basic = os.getenv("GIGACHAT_BASIC")
    gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    gigachat_base_url = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
    gigachat_token_url = os.getenv("GIGACHAT_TOKEN_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
    gigachat_verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL", "true").lower() in ("1", "true", "yes")

    content_base_dir = Path(os.getenv("CONTENT_BASE_DIR", "content")).resolve()
    articles_per_day = int(os.getenv("ARTICLES_PER_DAY", "10"))
    inline_images = int(os.getenv("INLINE_IMAGES", "2"))
    request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

    return Config(
        llm_provider=llm_provider,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_model=openai_model,
        gigachat_client_id=gigachat_client_id,
        gigachat_client_secret=gigachat_client_secret,
        gigachat_basic=gigachat_basic,
        gigachat_scope=gigachat_scope,
        gigachat_base_url=gigachat_base_url,
        gigachat_token_url=gigachat_token_url,
        gigachat_verify_ssl=gigachat_verify_ssl,
        content_base_dir=content_base_dir,
        articles_per_day=articles_per_day,
        inline_images=inline_images,
        request_timeout_seconds=request_timeout_seconds,
    )
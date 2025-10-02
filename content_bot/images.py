from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import requests


@dataclass
class ImageResult:
    url: str
    author: Optional[str]
    link: Optional[str]
    source: str  # unsplash | pexels


def _search_unsplash(query: str, per_page: int, access_key: str, timeout: int) -> List[ImageResult]:
    endpoint = "https://api.unsplash.com/search/photos"
    headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {access_key}"}
    params = {"query": query, "per_page": per_page, "orientation": "landscape"}
    r = requests.get(endpoint, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    results: List[ImageResult] = []
    for item in r.json().get("results", []):
        results.append(
            ImageResult(
                url=item["urls"].get("regular") or item["urls"].get("full"),
                author=(item.get("user") or {}).get("name"),
                link=(item.get("links") or {}).get("html"),
                source="unsplash",
            )
        )
    return results


def _search_pexels(query: str, per_page: int, api_key: str, timeout: int) -> List[ImageResult]:
    endpoint = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page}
    r = requests.get(endpoint, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    results: List[ImageResult] = []
    for item in r.json().get("photos", []):
        src = item.get("src") or {}
        results.append(
            ImageResult(
                url=src.get("large2x") or src.get("large") or src.get("original"),
                author=item.get("photographer"),
                link=item.get("url"),
                source="pexels",
            )
        )
    return results

def _search_pixabay(query: str, per_page: int, api_key: str, timeout: int) -> List[ImageResult]:
    endpoint = "https://pixabay.com/api/"
    params = {"key": api_key, "q": query, "per_page": per_page, "image_type": "photo", "safesearch": "true"}
    r = requests.get(endpoint, params=params, timeout=timeout)
    r.raise_for_status()
    results: List[ImageResult] = []
    for item in r.json().get("hits", []):
        results.append(
            ImageResult(
                url=item.get("largeImageURL") or item.get("webformatURL"),
                author=item.get("user"),
                link=item.get("pageURL"),
                source="pixabay",
            )
        )
    return results


def search_images(
    query: str,
    provider: str,
    per_page: int = 3,
    *,
    unsplash_access_key: Optional[str] = None,
    pexels_api_key: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    timeout: int = 60,
) -> List[ImageResult]:
    provider = (provider or "unsplash").lower()
    if provider == "unsplash":
        if not unsplash_access_key:
            raise RuntimeError("UNSPLASH_ACCESS_KEY is required for provider=unsplash")
        return _search_unsplash(query, per_page, unsplash_access_key, timeout)
    if provider == "pexels":
        if not pexels_api_key:
            raise RuntimeError("PEXELS_API_KEY is required for provider=pexels")
        return _search_pexels(query, per_page, pexels_api_key, timeout)
    if provider == "pixabay":
        if not pixabay_api_key:
            raise RuntimeError("PIXABAY_API_KEY is required for provider=pixabay")
        return _search_pixabay(query, per_page, pixabay_api_key, timeout)
    raise ValueError(f"Unknown image provider: {provider}")


def download_image(url: str, dest_path: Path, timeout: int = 120) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

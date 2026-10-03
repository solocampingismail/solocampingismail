#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://solocampingismail.github.io/solocampingismail/"
SITE_HOST = urlparse(SITE_URL).netloc
KEY_PATH = ROOT / "4d83a4010876b1810494ea664b458271.txt"
SITEMAPS = (
    ROOT / "sitemap.xml",
    ROOT / "video-sitemap.xml",
    ROOT / "youtube-video-sitemap.xml",
)
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP_NAMESPACE = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"


def load_urls() -> list[str]:
    urls: set[str] = set()
    site_prefix = SITE_URL.rstrip("/") + "/"
    for sitemap in SITEMAPS:
        if not sitemap.exists() and sitemap.name == "youtube-video-sitemap.xml":
            continue
        tree = ET.parse(sitemap)
        for element in tree.iter(SITEMAP_NAMESPACE):
            if not element.text:
                continue
            url = element.text.strip()
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.netloc != SITE_HOST:
                raise ValueError(f"Unexpected URL in {sitemap.name}: {url}")
            if not url.startswith(site_prefix):
                raise ValueError(f"URL is outside the configured site path: {url}")
            urls.add(url)
    if not urls:
        raise ValueError("No URLs found in the configured sitemaps.")
    if len(urls) > 10_000:
        raise ValueError("IndexNow allows at most 10,000 URLs per request.")
    return sorted(urls)


def build_payload(urls: list[str], key: str) -> dict[str, object]:
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        raise ValueError("IndexNow key must contain 8 to 128 letters, digits, or dashes.")
    site_prefix = SITE_URL.rstrip("/") + "/"
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != SITE_HOST:
            raise ValueError(f"Cannot submit a URL outside {SITE_HOST}: {url}")
        if not url.startswith(site_prefix):
            raise ValueError(f"Cannot submit a URL outside the configured site path: {url}")
    return {
        "host": SITE_HOST,
        "key": key,
        "keyLocation": f"{SITE_URL}{KEY_PATH.name}",
        "urlList": urls,
    }


def submit_urls(urls: list[str]) -> int:
    key = KEY_PATH.read_text(encoding="utf-8").strip()
    payload = build_payload(urls, key)
    request = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"IndexNow returned HTTP {response.status}; URLs were not confirmed as received."
                )
            print(
                json.dumps(
                    {
                        "status": "accepted",
                        "urls_submitted": len(urls),
                        "note": "HTTP 200 confirms receipt only; it does not guarantee indexing.",
                    }
                )
            )
            return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"IndexNow returned HTTP {exc.code}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach the IndexNow endpoint: {exc.reason}") from exc


def main() -> int:
    try:
        return submit_urls(load_urls())
    except (ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"IndexNow submission failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

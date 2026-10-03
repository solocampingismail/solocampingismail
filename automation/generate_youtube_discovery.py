#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://solocampingismail.github.io/solocampingismail/"
CHANNEL_ID = "UC87pVteBukFzQv_xA1UC6Kg"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUTPUT_DIR = ROOT / "channel-videos"
SITEMAP_PATH = ROOT / "youtube-video-sitemap.xml"
ATOM = "{http://www.w3.org/2005/Atom}"
YOUTUBE = "{http://www.youtube.com/xml/schemas/2015}"
MEDIA = "{http://search.yahoo.com/mrss/}"
SITEMAP = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
VIDEO_SITEMAP = "{http://www.google.com/schemas/sitemap-video/1.1}"
VIDEO_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{11}")
ALLOWED_THUMBNAIL_HOST = re.compile(r"(?:[A-Za-z0-9-]+\.)*ytimg\.com", re.IGNORECASE)


def _text(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_feed(feed_xml: bytes) -> list[dict[str, str]]:
    feed = ET.fromstring(feed_xml)
    feed_channel_id = _text(feed.find(f"{YOUTUBE}channelId"))
    if feed_channel_id not in {CHANNEL_ID, CHANNEL_ID.removeprefix("UC")}:
        raise ValueError(
            "YouTube RSS feed channel ID does not match the configured channel."
        )

    videos: list[dict[str, str]] = []
    for entry in feed.findall(f"{ATOM}entry"):
        video_id = _text(entry.find(f"{YOUTUBE}videoId"))
        title = _text(entry.find(f"{ATOM}title"))
        published = _text(entry.find(f"{ATOM}published"))
        media_group = entry.find(f"{MEDIA}group")
        description = _text(
            media_group.find(f"{MEDIA}description")
            if media_group is not None
            else None
        )
        description = " ".join(description.split())
        thumbnail = ""
        if media_group is not None:
            thumbnail_element = media_group.find(f"{MEDIA}thumbnail")
            if thumbnail_element is not None:
                thumbnail = thumbnail_element.get("url", "")

        if not VIDEO_ID_PATTERN.fullmatch(video_id):
            raise ValueError(f"Invalid YouTube video ID in RSS feed: {video_id!r}")
        if not title:
            raise ValueError(f"YouTube RSS entry {video_id} has no title.")
        if not published:
            raise ValueError(f"YouTube RSS entry {video_id} has no publication date.")
        try:
            datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"YouTube RSS entry {video_id} has an invalid publication date."
            ) from exc
        thumbnail_host = urlparse(thumbnail).hostname or ""
        if (
            urlparse(thumbnail).scheme != "https"
            or not ALLOWED_THUMBNAIL_HOST.fullmatch(thumbnail_host)
        ):
            raise ValueError(f"YouTube RSS entry {video_id} has an invalid thumbnail URL.")
        if not description:
            description = title

        videos.append(
            {
                "video_id": video_id,
                "title": title,
                "description": description,
                "published": published,
                "thumbnail": thumbnail,
            }
        )
    if not videos:
        raise ValueError("YouTube RSS feed contained no video entries.")
    return videos


def fetch_feed() -> list[dict[str, str]]:
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "SoloCampingIsmailVideoDiscovery/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return parse_feed(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"YouTube RSS returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach YouTube RSS: {exc.reason}") from exc


def _json_for_script(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def render_page(video: dict[str, str]) -> str:
    video_id = video["video_id"]
    page_url = f"{SITE_URL}channel-videos/{video_id}/"
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
    title = html.escape(video["title"])
    description = html.escape(video["description"])
    thumbnail = html.escape(video["thumbnail"], quote=True)
    structured_data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": video["title"],
        "description": video["description"],
        "thumbnailUrl": [video["thumbnail"]],
        "embedUrl": embed_url,
        "url": watch_url,
        "publisher": {
            "@type": "Organization",
            "name": "Solo Camping İsmail",
            "url": f"https://www.youtube.com/@solocampingismail",
        },
    }
    if video["published"]:
        structured_data["uploadDate"] = video["published"]

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <meta name="description" content="{description[:300]}">
  <link rel="canonical" href="{page_url}">
  <meta property="og:type" content="video.other">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description[:300]}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{thumbnail}">
  <title>{title} | Solo Camping İsmail</title>
  <style>
    body{{margin:0;background:#080b09;color:#f2f5f2;font:18px/1.6 Arial,sans-serif}}
    main{{width:min(900px,92%);margin:40px auto}}
    a{{color:#a9d99d}}
    .player{{position:relative;aspect-ratio:16/9;margin:24px 0}}
    iframe{{position:absolute;width:100%;height:100%;border:0;border-radius:12px}}
  </style>
</head>
<body>
  <main>
    <p><a href="{SITE_URL}">Solo Camping İsmail</a></p>
    <h1>{title}</h1>
    <p>{description}</p>
    <div class="player">
      <iframe src="{embed_url}" title="{title}" loading="eager" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </div>
    <p><a href="{watch_url}" rel="noopener noreferrer">Videoyu YouTube'da aç</a> · <a href="https://www.youtube.com/@solocampingismail?sub_confirmation=1" rel="noopener noreferrer">Kanala abone ol</a></p>
  </main>
  <script type="application/ld+json">{_json_for_script(structured_data)}</script>
</body>
</html>
"""


def build_video_sitemap(videos: list[dict[str, str]]) -> ET.Element:
    ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.register_namespace("video", "http://www.google.com/schemas/sitemap-video/1.1")
    root = ET.Element(f"{SITEMAP}urlset")
    for video in videos:
        video_id = video["video_id"]
        url_element = ET.SubElement(root, f"{SITEMAP}url")
        ET.SubElement(url_element, f"{SITEMAP}loc").text = (
            f"{SITE_URL}channel-videos/{video_id}/"
        )
        details = ET.SubElement(url_element, f"{VIDEO_SITEMAP}video")
        ET.SubElement(details, f"{VIDEO_SITEMAP}thumbnail_loc").text = video[
            "thumbnail"
        ]
        ET.SubElement(details, f"{VIDEO_SITEMAP}title").text = video["title"]
        ET.SubElement(details, f"{VIDEO_SITEMAP}description").text = video[
            "description"
        ][:2048]
        ET.SubElement(details, f"{VIDEO_SITEMAP}publication_date").text = video[
            "published"
        ]
        ET.SubElement(details, f"{VIDEO_SITEMAP}player_loc").text = (
            f"https://www.youtube-nocookie.com/embed/{video_id}"
        )
    return root


def generate_discovery_pages(
    videos: list[dict[str, str]],
    output_dir: Path = OUTPUT_DIR,
    sitemap_path: Path = SITEMAP_PATH,
    curated_pages_dir: Path = ROOT / "videos",
) -> int:
    if len(videos) > 15:
        raise ValueError("Only the latest 15 videos from the public YouTube RSS feed are supported.")
    output_dir.mkdir(parents=True, exist_ok=True)
    sitemap_path.parent.mkdir(parents=True, exist_ok=True)
    indexable_videos = [
        video
        for video in videos
        if not (curated_pages_dir / video["video_id"] / "index.html").is_file()
    ]
    for video in indexable_videos:
        page_dir = output_dir / video["video_id"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_page(video), encoding="utf-8"
        )

    sitemap = build_video_sitemap(indexable_videos)
    ET.ElementTree(sitemap).write(
        sitemap_path,
        encoding="utf-8",
        xml_declaration=True,
    )
    return len(indexable_videos)


def main() -> int:
    try:
        videos = fetch_feed()
        count = generate_discovery_pages(videos)
        print(
            json.dumps(
                {
                    "status": "generated",
                    "videos": count,
                    "sitemap": str(SITEMAP_PATH.relative_to(ROOT)),
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"YouTube discovery generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

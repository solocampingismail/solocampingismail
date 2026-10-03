#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "automation" / "generated"
BACKUP_DIR = OUTPUT_DIR / "youtube-metadata-backups"
CHANNEL_HANDLE = "solocampingismail"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2/reports"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
SUPPORTED_LANGUAGES = ("en", "tr")
VIDEO_METADATA: tuple[Dict[str, Any], ...] = (
    {
        "video_id": "OR62dmVC7h4",
        "title": {
            "en": "Solo Camping in the Rain | A Night Under the Tent",
            "tr": "Yağmurda Tek Başına Kamp | Çadır Altında Bir Gece",
        },
        "description": {
            "en": "Join me for a solo camping night as rain continues outside the tent. Subscribe for more solo camping and outdoor videos.\n\nMore from Solo Camping İsmail: https://linktr.ee/solocampingismail",
            "tr": "Yağmurun çadırın dışında devam ettiği tek başına kamp geceme eşlik edin. Yeni solo kamp ve doğa videoları için kanala abone olun.\n\nSolo Camping İsmail'in diğer hesapları: https://linktr.ee/solocampingismail",
        },
        "tags": {
            "en": ["solo camping", "camping in the rain", "rain camping", "tent camping", "outdoor adventure"],
            "tr": ["tek başına kamp", "yağmurda kamp", "çadır kampı", "doğa", "kamp"],
        },
    },
    {
        "video_id": "j1AQwpMbIOw",
        "title": {
            "en": "Walking Through an Old Forest | Solo Camping by the Lake",
            "tr": "Eski Bir Ormanda Yürüyüş | Göl Kenarında Tek Başına Kamp",
        },
        "description": {
            "en": "Come along on a walk through an old forest and a solo camping trip beside the lake. Subscribe for more camping and outdoor videos.\n\nMore from Solo Camping İsmail: https://linktr.ee/solocampingismail",
            "tr": "Eski bir ormanda yürüyüşe ve göl kenarında tek başıma kamp yolculuğuma eşlik edin. Yeni kamp ve doğa videoları için kanala abone olun.\n\nSolo Camping İsmail'in diğer hesapları: https://linktr.ee/solocampingismail",
        },
        "tags": {
            "en": ["solo camping", "forest walk", "lake camping", "nature", "outdoor adventure"],
            "tr": ["tek başına kamp", "orman yürüyüşü", "göl kenarında kamp", "doğa", "kamp"],
        },
    },
    {
        "video_id": "DGYvjoCzK9Y",
        "title": {
            "en": "Tent Camping After Heavy Rain | Bushcraft & ASMR",
            "tr": "Şiddetli Yağmur Sonrası Çadırda Kamp Yapmak 🌧️ | Bushcraft, Outdoor Survival & ASMR",
        },
        "description": {
            "en": "A solo camping video about tent camping after heavy rain, with bushcraft, outdoor survival, and ASMR themes. Subscribe for more camping videos.\n\nMore from Solo Camping İsmail: https://linktr.ee/solocampingismail",
            "tr": "Şiddetli yağmur sonrasında çadırda kamp, bushcraft, outdoor survival ve ASMR temalı bir solo kamp videosu. Yeni kamp videoları için kanala abone olun.\n\nSolo Camping İsmail'in diğer hesapları: https://linktr.ee/solocampingismail",
        },
        "tags": {
            "en": ["camping after heavy rain", "tent camping", "bushcraft", "outdoor survival", "solo camping", "camping ASMR"],
            "tr": ["şiddetli yağmur sonrası kamp", "çadırda kamp", "bushcraft", "doğada hayatta kalma", "tek başına kamp", "kamp ASMR"],
        },
    },
    {
        "video_id": "gfYmui17Z5s",
        "title": {
            "en": "Solo Camping in Pitch Darkness | Night Camping #Shorts",
            "tr": "Zifiri Karanlıkta Tek Başıma Kamp! ⛺ Hataya Yer Yok! #shorts #camping",
        },
        "description": {
            "en": "A short solo-camping video in pitch darkness. Subscribe for more camping and outdoor videos.\n\nMore from Solo Camping İsmail: https://linktr.ee/solocampingismail",
            "tr": "Zifiri karanlıkta geçen kısa bir tek başına kamp videosu. Yeni kamp ve doğa videoları için kanala abone olun.\n\nSolo Camping İsmail'in diğer hesapları: https://linktr.ee/solocampingismail",
        },
        "tags": {
            "en": ["solo camping at night", "camping in the dark", "night camping", "camping shorts", "outdoor adventure"],
            "tr": ["gece kampı", "karanlıkta kamp", "tek başına kamp", "kamp shorts", "doğa"],
        },
    },
)


def metadata_for(video: Dict[str, Any], language: str) -> Dict[str, Any]:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    title = video["title"][language].strip()
    description = video["description"][language].strip()
    tags = list(dict.fromkeys(video["tags"][language]))
    validate_metadata(title, description, tags)
    return {
        "video_id": video["video_id"],
        "video_url": f"https://www.youtube.com/watch?v={video['video_id']}",
        "language": language,
        "title": title,
        "description": description,
        "tags": tags,
    }


def validate_metadata(title: str, description: str, tags: List[str]) -> None:
    if not title or len(title) > 100:
        raise ValueError("YouTube titles must contain 1 to 100 characters.")
    if len(description) > 5000:
        raise ValueError("YouTube descriptions cannot exceed 5,000 characters.")
    if any(not tag.strip() for tag in tags):
        raise ValueError("YouTube tags cannot be empty.")
    if len(",".join(tags).encode("utf-8")) > 500:
        raise ValueError("Combined YouTube tags exceed the 500-byte limit.")


def write_metadata_plan(videos: tuple[Dict[str, Any], ...] = VIDEO_METADATA) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "youtube-seo-plan.md"
    lines = [
        "# YouTube metadata review plan",
        "",
        "Drafts only. Nothing is changed on YouTube unless a specific video is explicitly selected for metadata update.",
        "",
        "Titles/descriptions are based on the existing video cards in this repository. Verify that every detail matches the actual footage before applying.",
        "",
        "Tags are included for spelling/topic context; YouTube says tags are not an important discovery signal compared with title, thumbnail, description, and viewer response.",
        "",
    ]
    for video in videos:
        english = metadata_for(video, "en")
        turkish = metadata_for(video, "tr")
        lines.extend(
            [
                f"## {english['video_url']}",
                "",
                f"### English title",
                english["title"],
                "",
                "### English description",
                english["description"],
                "",
                "### Turkish title",
                turkish["title"],
                "",
                "### Turkish description",
                turkish["description"],
                "",
                "### Suggested tags",
                ", ".join(dict.fromkeys(english["tags"] + turkish["tags"])),
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def access_token() -> str:
    required = {
        "YOUTUBE_CLIENT_ID": os.getenv("YOUTUBE_CLIENT_ID"),
        "YOUTUBE_CLIENT_SECRET": os.getenv("YOUTUBE_CLIENT_SECRET"),
        "YOUTUBE_REFRESH_TOKEN": os.getenv("YOUTUBE_REFRESH_TOKEN"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError("Missing YouTube OAuth configuration: " + ", ".join(missing))

    response = requests.post(
        OAUTH_TOKEN_URL,
        data={
            "client_id": required["YOUTUBE_CLIENT_ID"],
            "client_secret": required["YOUTUBE_CLIENT_SECRET"],
            "refresh_token": required["YOUTUBE_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = checked_json(response, "Google OAuth")
    token = payload.get("access_token")
    if not token:
        raise ValueError("Google OAuth did not return an access token.")
    return token


def checked_json(response: requests.Response, service: str) -> Dict[str, Any]:
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"{service} returned an unexpected response.")
    error = payload.get("error")
    if error:
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code") or "unknown API error"
        else:
            detail = str(error)
        raise ValueError(f"{service} API error: {detail}")
    return payload


class YouTubeClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.get(
            f"{YOUTUBE_API}/{endpoint}", params=params, timeout=30
        )
        response.raise_for_status()
        return checked_json(response, "YouTube")

    def put(self, endpoint: str, params: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.put(
            f"{YOUTUBE_API}/{endpoint}",
            params=params,
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        return checked_json(response, "YouTube")

    def analytics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.get(ANALYTICS_API, params=params, timeout=30)
        response.raise_for_status()
        return checked_json(response, "YouTube Analytics")


def owned_channel(client: YouTubeClient) -> Dict[str, Any]:
    payload = client.get("channels", {"part": "id,snippet", "mine": "true"})
    channels = payload.get("items", [])
    if len(channels) != 1:
        raise ValueError(
            f"Expected one authenticated YouTube channel, received {len(channels)}."
        )
    channel = channels[0]
    expected_id = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
    if not expected_id:
        raise ValueError("Set YOUTUBE_CHANNEL_ID to the channel you authorize.")
    if channel.get("id") != expected_id:
        raise ValueError(
            "Authenticated YouTube account does not match YOUTUBE_CHANNEL_ID."
        )
    return channel


def analytics_query(
    client: YouTubeClient,
    start_date: date,
    end_date: date,
    metrics: str,
    dimensions: str | None = None,
    sort: str | None = None,
    max_results: int | None = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "ids": "channel==MINE",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "metrics": metrics,
    }
    if dimensions:
        params["dimensions"] = dimensions
    if sort:
        params["sort"] = sort
    if max_results:
        params["maxResults"] = max_results
    return client.analytics(params)


def build_analytics_report(
    client: YouTubeClient,
    end_date: date | None = None,
    days: int = 28,
) -> Dict[str, Any]:
    if days < 1 or days > 90:
        raise ValueError("Analytics period must be between 1 and 90 days.")
    report_end = end_date or (date.today() - timedelta(days=1))
    report_start = report_end - timedelta(days=days - 1)
    video_metrics = (
        "views,estimatedMinutesWatched,averageViewDuration,"
        "averageViewPercentage,likes,comments,shares,subscribersGained"
    )
    channel_metrics = (
        "views,estimatedMinutesWatched,averageViewDuration,"
        "likes,comments,shares,subscribersGained,subscribersLost"
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel_id": os.getenv("YOUTUBE_CHANNEL_ID"),
        "period": {
            "start": report_start.isoformat(),
            "end": report_end.isoformat(),
            "days": days,
        },
        "summary": analytics_query(client, report_start, report_end, channel_metrics),
        "videos": analytics_query(
            client,
            report_start,
            report_end,
            video_metrics,
            dimensions="video",
            sort="-views",
            max_results=200,
        ),
        "countries": analytics_query(
            client,
            report_start,
            report_end,
            "views,estimatedMinutesWatched",
            dimensions="country",
            sort="-views",
            max_results=25,
        ),
        "traffic_sources": analytics_query(
            client,
            report_start,
            report_end,
            "views,estimatedMinutesWatched",
            dimensions="trafficSourceType",
            sort="-views",
            max_results=25,
        ),
    }


def report_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# YouTube channel performance",
        "",
        f"Period: {report['period']['start']} to {report['period']['end']}",
        "",
        "## Channel summary",
        "",
    ]
    summary = report["summary"]
    headers = [column["name"] for column in summary.get("columnHeaders", [])]
    rows = summary.get("rows", [])
    if rows:
        lines.append(" | ".join(f"{name}: {value}" for name, value in zip(headers, rows[0])))
    else:
        lines.append("No channel summary data returned for this period.")
    for key, heading in (
        ("videos", "Videos"),
        ("countries", "Top countries"),
        ("traffic_sources", "Traffic sources"),
    ):
        lines.extend(["", f"## {heading}", ""])
        section = report[key]
        section_headers = [
            column["name"] for column in section.get("columnHeaders", [])
        ]
        section_rows = section.get("rows", [])
        if not section_rows:
            lines.append("No report rows returned.")
            continue
        lines.append(" | ".join(section_headers))
        lines.append(" | ".join("---" for _ in section_headers))
        lines.extend(
            " | ".join(str(value) for value in row) for row in section_rows
        )
    lines.extend(
        [
            "",
            "Interpret these results as observed channel data, not a guarantee of future reach. Use the video retention and viewer satisfaction shown in YouTube Studio when deciding creative changes.",
            "",
        ]
    )
    return "\n".join(lines)


def apply_metadata(
    client: YouTubeClient,
    video: Dict[str, Any],
    language: str,
    confirm_handle: str,
) -> Dict[str, Any]:
    if confirm_handle.casefold().removeprefix("@") != CHANNEL_HANDLE:
        raise ValueError(
            f"Pass --confirm-handle {CHANNEL_HANDLE} to confirm the target channel."
        )
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Choose en or tr as the video default language.")

    channel = owned_channel(client)
    video_payload = client.get(
        "videos",
        {"part": "snippet,localizations", "id": video["video_id"]},
    )
    videos = video_payload.get("items", [])
    if len(videos) != 1:
        raise ValueError(f"Video not found: {video['video_id']}")
    current = videos[0]
    current_snippet = current.get("snippet", {})
    if current_snippet.get("channelId") != channel["id"]:
        raise ValueError(
            f"Video {video['video_id']} does not belong to the authenticated channel."
        )
    current_default_language = current_snippet.get("defaultLanguage")
    if current_default_language != language:
        raise ValueError(
            "Metadata updates require the video's existing default language to match "
            f"--language {language}; current value is {current_default_language!r}. "
            "Review/change video language in YouTube Studio first."
        )

    draft = metadata_for(video, language)
    original_localizations = current.get("localizations", {})
    localizations = dict(original_localizations)
    for locale in SUPPORTED_LANGUAGES:
        localized_draft = metadata_for(video, locale)
        localizations[locale] = {
            "title": localized_draft["title"],
            "description": localized_draft["description"],
        }

    snippet: Dict[str, Any] = {
        "title": draft["title"],
        "description": draft["description"],
        "categoryId": current_snippet.get("categoryId"),
        "defaultLanguage": current_default_language,
        "tags": draft["tags"],
    }
    if not snippet["categoryId"]:
        raise ValueError("YouTube returned no categoryId; refusing an incomplete update.")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{video['video_id']}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    backup_path.write_text(
        json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    update = client.put(
        "videos",
        {"part": "snippet,localizations"},
        {
            "id": video["video_id"],
            "snippet": snippet,
            "localizations": localizations,
        },
    )
    updated_items = update.get("items", [])
    if len(updated_items) != 1:
        raise ValueError("YouTube update response did not contain the updated video.")
    return {
        "status": "updated",
        "video_id": video["video_id"],
        "video_url": f"https://www.youtube.com/watch?v={video['video_id']}",
        "backup": str(backup_path.relative_to(ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="YouTube-only channel analytics and video metadata tools"
    )
    parser.add_argument(
        "--mode",
        choices=("metadata-preview", "analytics", "metadata-apply"),
        default="metadata-preview",
    )
    parser.add_argument("--video-id", help="Required for a live metadata update.")
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default="en")
    parser.add_argument(
        "--confirm-handle",
        help="Must be solocampingismail before any metadata update.",
    )
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "youtube-analytics-report.json",
    )
    args = parser.parse_args()
    try:
        if args.mode == "metadata-preview":
            output_path = write_metadata_plan()
            print(json.dumps({"status": "preview", "path": str(output_path.relative_to(ROOT))}))
            return 0

        token = access_token()
        client = YouTubeClient(token)
        if args.mode == "analytics":
            owned_channel(client)
            report = build_analytics_report(client, days=args.days)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            markdown_path = args.output.with_suffix(".md")
            markdown_path.write_text(report_markdown(report), encoding="utf-8")
            print(
                json.dumps(
                    {
                        "status": "reported",
                        "json": str(args.output.relative_to(ROOT)),
                        "markdown": str(markdown_path.relative_to(ROOT)),
                    }
                )
            )
            return 0

        if not args.video_id:
            raise ValueError("--video-id is required for metadata-apply.")
        selected_video = next(
            (
                candidate
                for candidate in VIDEO_METADATA
                if candidate.get("video_id") == args.video_id
            ),
            None,
        )
        if not selected_video:
            raise ValueError(
                "Only a video explicitly included in the reviewed metadata plan can be updated."
            )
        result = apply_metadata(
            client,
            selected_video,
            args.language,
            args.confirm_handle or "",
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, requests.RequestException, json.JSONDecodeError) as exc:
        print(f"YouTube operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

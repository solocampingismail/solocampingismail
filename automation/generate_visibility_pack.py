#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "automation" / "generated"
SITE_URL = "https://solocampingismail.github.io/solocampingismail/"
LINKTREE_URL = "https://linktr.ee/solocampingismail"

VIDEOS = [
    {
        "id": "OR62dmVC7h4",
        "titles": {
            "tr": "Yağmur Hiç Durmadı — Çadır Olmasa Yanmıştım",
            "en": "The Rain Never Stopped — My Tent Made All the Difference",
        },
        "descriptions": {
            "tr": "Yağmurun hiç dinmediği bir solo kamp gecesi. Çadırda yağmur sesleri ve doğanın gerçek hali.",
            "en": "A solo camping night in nonstop rain, with the sound of the weather and a quiet shelter in the outdoors.",
        },
        "prompts": {
            "tr": "Yağmurlu kampta senin için en önemli ekipman ne olurdu?",
            "en": "What would be your must-have piece of gear for a rainy camp?",
        },
    },
    {
        "id": "j1AQwpMbIOw",
        "titles": {
            "tr": "Eski Ormanda Yürüyüş — Göl Kenarında Solo Kamp",
            "en": "A Walk Through the Old Forest — Solo Camping by the Lake",
        },
        "descriptions": {
            "tr": "Eski ormanda yürüyüş, göl kıyısında kamp ve doğada sakin bir mola.",
            "en": "A walk through an old forest, a lakeside camp, and a quiet break in nature.",
        },
        "prompts": {
            "tr": "Göl kenarında mı, ormanın içinde mi kamp yapmayı seçerdin?",
            "en": "Would you choose a lakeside camp or a spot deep in the forest?",
        },
    },
    {
        "id": "DGYvjoCzK9Y",
        "titles": {
            "tr": "Doğada Tek Başına — Solo Camping İsmail",
            "en": "Alone in Nature — Solo Camping İsmail",
        },
        "descriptions": {
            "tr": "Doğada tek başına kamp deneyiminden sakin bir kesit.",
            "en": "A quiet moment from a solo camping trip in nature.",
        },
        "prompts": {
            "tr": "Tek başına kamp yaparken yanında mutlaka ne bulundurursun?",
            "en": "What is one thing you always bring on a solo camping trip?",
        },
    },
    {
        "id": "gfYmui17Z5s",
        "titles": {
            "tr": "Kamp ve Doğa — Solo Camping İsmail",
            "en": "Camping and Nature — Solo Camping İsmail",
        },
        "descriptions": {
            "tr": "Kamp hayatından ve doğanın içinden kısa bir kaçış.",
            "en": "A short escape into camping life and the outdoors.",
        },
        "prompts": {
            "tr": "Bir sonraki videoda yağmur, orman ya da göl kampından hangisini görmek istersin?",
            "en": "Which would you like to see next: a rainy camp, a forest camp, or a lakeside trip?",
        },
    },
]

HASHTAGS = {
    "tr": "#SoloCamping #Kamp #Doğa",
    "en": "#SoloCamping #Camping #Nature",
}

def platform_content(video: Dict[str, object], language: str) -> Dict[str, Dict[str, str]]:
    title = video["titles"][language]
    description = video["descriptions"][language]
    video_url = f"https://www.youtube.com/watch?v={video['id']}"
    site_url = SITE_URL + ("en/" if language == "en" else "")
    hashtags = HASHTAGS[language]
    prompt = video["prompts"][language]

    return {
        "youtube": {
            "title": title[:100],
            "body": (
                f"{description}\n\n{prompt}\n\n"
                f"{site_url}\n{LINKTREE_URL}\n{hashtags}"
            ),
            "cta": prompt,
            "format": "video-description",
        },
        "instagram": {
            "title": title,
            "body": (
                f"{title}\n\n{description}\n\n{prompt}\n\n"
                + (
                    "Tam video ve diğer hesaplarım için profilimdeki Linktree bağlantısını ziyaret et."
                    if language == "tr"
                    else "Visit the Linktree link in my profile for the full video and all my channels."
                )
                + f"\n\n{hashtags}"
            ),
            "cta": (
                "Tam video ve diğer hesaplarım için profilimdeki Linktree bağlantısını ziyaret et."
                if language == "tr"
                else "Visit the Linktree link in my profile for the full video and all my channels."
            ),
            "format": "image-post-caption",
        },
        "tiktok": {
            "title": title,
            "body": (
                f"{title}\n\n{description}\n\n{prompt}\n\n"
                + (
                    "Tam video YouTube'da; profilimdeki Linktree bağlantısından ulaş."
                    if language == "tr"
                    else "Watch the full video on YouTube via the Linktree link in my profile."
                )
                + f"\n\n{hashtags}"
            ),
            "cta": (
                "Tam video YouTube'da; profilimdeki Linktree bağlantısından ulaş."
                if language == "tr"
                else "Watch the full video on YouTube via the Linktree link in my profile."
            ),
            "format": "short-video-caption",
        },
        "x": {
            "title": title,
            "body": (
                f"{title}\n{description}\n\n{video_url}\n"
                f"{LINKTREE_URL}\n{hashtags}"
            ),
            "cta": prompt,
            "format": "short-post",
        },
        "facebook": {
            "title": title,
            "body": (
                f"{title}\n\n{description}\n\n{prompt}\n\n"
                f"{video_url}\n{LINKTREE_URL}\n\n{hashtags}"
            ),
            "cta": prompt,
            "format": "page-post",
        },
        "pinterest": {
            "title": title[:100],
            "body": (
                f"{description}\n\n{prompt}\n\n"
                f"{video_url}\n{LINKTREE_URL}\n{hashtags}"
            )[:800],
            "cta": prompt,
            "format": "pin-description",
        },
    }


def build_pack(date_str: str) -> Dict[str, object]:
    content_items = []
    for index, video in enumerate(VIDEOS, start=1):
        localized_platforms = {
            language: platform_content(video, language)
            for language in ("tr", "en")
        }
        content_items.append(
            {
                "id": f"video-{video['id']}",
                "video_id": video["id"],
                "video_url": f"https://www.youtube.com/watch?v={video['id']}",
                "thumbnail_url": f"https://i.ytimg.com/vi/{video['id']}/hqdefault.jpg",
                "title": video["titles"]["tr"],
                "titles": video["titles"],
                "descriptions": video["descriptions"],
                "generated_for": date_str,
                "platforms": localized_platforms["tr"],
                "localized_platforms": localized_platforms,
                "engagement_prompt": video["prompts"],
                "rotation": index,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brand": "Solo Camping İsmail",
        "goal": "Bilingual, video-specific global discovery and genuine conversation",
        "languages": ["tr", "en"],
        "posts": content_items,
    }


def write_outputs(pack: Dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markdown = [
        "# Global visibility pack",
        "",
        f"Generated at: {pack['generated_at']}",
        f"Brand: {pack['brand']}",
        f"Goal: {pack['goal']}",
        "",
        "Captions below refer to videos already listed on the channel. Review each caption and attach the original video before publishing.",
        "",
    ]

    for post in pack["posts"]:
        markdown.extend(
            [
                f"## {post['titles']['tr']} / {post['titles']['en']}",
                "",
                f"Video: {post['video_url']}",
                "",
            ]
        )
        for language in ("tr", "en"):
            markdown.extend([f"### {language.upper()}", ""])
            for platform_name, payload in post["localized_platforms"][language].items():
                markdown.extend(
                    [
                        f"#### {platform_name.upper()}",
                        f"Title: {payload['title']}",
                        f"CTA: {payload['cta']}",
                        "Body:",
                        payload["body"],
                        "",
                    ]
                )
        markdown.extend(["---", ""])

    (OUTPUT_DIR / "social-visibility-pack.md").write_text(
        "\n".join(markdown), encoding="utf-8"
    )
    (OUTPUT_DIR / "social-visibility-pack.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    pack = build_pack(today)
    write_outputs(pack)
    print(f"Generated visibility pack: {OUTPUT_DIR / 'social-visibility-pack.json'}")


if __name__ == "__main__":
    main()

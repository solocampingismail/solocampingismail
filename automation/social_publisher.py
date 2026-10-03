#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parent.parent
PACK_PATH = ROOT / "automation" / "generated" / "social-visibility-pack.json"
LEDGER_PATH = ROOT / "automation" / "generated" / "publishing-ledger.json"
LINKTREE_URL = "https://linktr.ee/solocampingismail"
CHANNELS = ("x", "facebook", "instagram", "pinterest", "tiktok", "youtube")


def load_pack() -> Dict[str, Any]:
    if not PACK_PATH.exists():
        import automation.generate_visibility_pack as generator

        generator.main()
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def select_post(
    pack: Dict[str, Any],
    post_id: str | None = None,
    scheduled_date: date | None = None,
) -> Dict[str, Any]:
    posts = pack.get("posts") or []
    if not posts:
        raise ValueError("The visibility pack contains no posts.")
    if post_id:
        for post in posts:
            if post.get("id") == post_id:
                return post
        raise ValueError(f"Post id not found in visibility pack: {post_id}")

    run_date = scheduled_date or datetime.now(timezone.utc).date()
    scheduled_day_slots = {1: 0, 3: 1, 5: 2}
    weekday_slot = scheduled_day_slots.get(run_date.weekday())
    if weekday_slot is None:
        return posts[(run_date.toordinal() - 1) % len(posts)]

    iso_week = run_date.isocalendar().week
    rotation_index = ((iso_week - 1) * len(scheduled_day_slots) + weekday_slot) % len(
        posts
    )
    return posts[rotation_index]


def text_for_platform(post: Dict[str, Any], platform_name: str, language: str) -> str:
    localized = post.get("localized_platforms", {}).get(language, {})
    platform_data = localized.get(platform_name, {})
    return platform_data.get("body") or platform_data.get("title") or ""


def checked_json(response: requests.Response, platform: str) -> Dict[str, Any]:
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"{platform} returned an unexpected response.")
    error = payload.get("error")
    if error:
        if isinstance(error, dict):
            message = error.get("message") or error.get("code") or "unknown API error"
        else:
            message = str(error)
        raise ValueError(f"{platform} API error: {message}")
    return payload


def x_publish(text: str, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run:
        return {"status": "dry-run", "channel": "x", "message": text}
    if len(text) > 280:
        raise ValueError(f"X post exceeds 280 characters ({len(text)}).")
    token = os.getenv("X_USER_ACCESS_TOKEN")
    if not token:
        return {"status": "skipped", "channel": "x", "reason": "missing X_USER_ACCESS_TOKEN"}

    response = requests.post(
        "https://api.x.com/2/tweets",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"text": text},
        timeout=30,
    )
    response.raise_for_status()
    payload = checked_json(response, "X")
    post_id = payload.get("data", {}).get("id")
    if not post_id:
        raise ValueError("X did not return a published post id.")
    return {"status": "published", "channel": "x", "id": post_id}


def graph_api_version() -> str | None:
    version = os.getenv("META_GRAPH_API_VERSION", "").strip()
    return version if re.fullmatch(r"v\d+\.\d+", version) else None


def facebook_publish(text: str, video_url: str, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run:
        return {"status": "dry-run", "channel": "facebook", "message": text}
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    version = graph_api_version()
    if not token or not page_id:
        return {
            "status": "skipped",
            "channel": "facebook",
            "reason": "missing FACEBOOK_PAGE_ACCESS_TOKEN or FACEBOOK_PAGE_ID",
        }
    if not version:
        return {
            "status": "skipped",
            "channel": "facebook",
            "reason": "set META_GRAPH_API_VERSION to a currently supported version",
        }

    response = requests.post(
        f"https://graph.facebook.com/{version}/{page_id}/feed",
        data={
            "message": text.replace(video_url, "").strip(),
            "link": video_url,
            "access_token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = checked_json(response, "Facebook")
    post_id = payload.get("id")
    if not post_id:
        raise ValueError("Facebook did not return a published post id.")
    return {"status": "published", "channel": "facebook", "id": post_id}


def instagram_publish(
    text: str, user_id: str, image_url: str, token: str, version: str
) -> Dict[str, Any]:
    if not image_url.startswith("https://"):
        raise ValueError("Instagram image_url must be an HTTPS URL.")

    container_response = requests.post(
        f"https://graph.facebook.com/{version}/{user_id}/media",
        data={"image_url": image_url, "caption": text, "access_token": token},
        timeout=30,
    )
    container_response.raise_for_status()
    container_id = checked_json(container_response, "Instagram").get("id")
    if not container_id:
        raise ValueError("Instagram did not return a media container id.")

    publish_response = requests.post(
        f"https://graph.facebook.com/{version}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    publish_response.raise_for_status()
    post_id = checked_json(publish_response, "Instagram").get("id")
    if not post_id:
        raise ValueError("Instagram did not return a published post id.")
    return {"status": "published", "channel": "instagram", "id": post_id}


def instagram_publish_or_skip(
    text: str, image_url: str, dry_run: bool = False
) -> Dict[str, Any]:
    if dry_run:
        return {"status": "dry-run", "channel": "instagram", "message": text}
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    user_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    version = graph_api_version()
    if not token or not user_id:
        return {
            "status": "skipped",
            "channel": "instagram",
            "reason": "missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID",
        }
    if not version:
        return {
            "status": "skipped",
            "channel": "instagram",
            "reason": "set META_GRAPH_API_VERSION to a currently supported version",
        }

    return instagram_publish(text, user_id, image_url, token, version)


def pinterest_publish(
    title: str,
    description: str,
    video_url: str,
    image_url: str,
    board_id: str,
    token: str,
) -> Dict[str, Any]:
    if not image_url.startswith("https://") or not video_url.startswith("https://"):
        raise ValueError("Pinterest image and destination URLs must use HTTPS.")
    response = requests.post(
        "https://api.pinterest.com/v5/pins",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "board_id": board_id,
            "title": title[:100],
            "description": description[:800],
            "link": video_url,
            "media_source": {"source_type": "image_url", "url": image_url},
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = checked_json(response, "Pinterest")
    pin_id = payload.get("id")
    if not pin_id:
        raise ValueError("Pinterest did not return a published pin id.")
    return {"status": "published", "channel": "pinterest", "id": pin_id}


def pinterest_publish_or_skip(
    post: Dict[str, Any], text: str, language: str, dry_run: bool = False
) -> Dict[str, Any]:
    if dry_run:
        return {"status": "dry-run", "channel": "pinterest", "message": text}
    token = os.getenv("PINTEREST_ACCESS_TOKEN")
    board_id = os.getenv("PINTEREST_BOARD_ID")
    if not token or not board_id:
        return {
            "status": "skipped",
            "channel": "pinterest",
            "reason": "missing PINTEREST_ACCESS_TOKEN or PINTEREST_BOARD_ID",
        }
    localized = (
        post.get("localized_platforms", {}).get(language, {}).get("pinterest", {})
    )
    return pinterest_publish(
        localized.get("title") or post["title"],
        text,
        LINKTREE_URL,
        post["thumbnail_url"],
        board_id,
        token,
    )


def tiktok_manual_result() -> Dict[str, Any]:
    return {
        "status": "manual",
        "channel": "tiktok",
        "reason": (
            "Direct public posting requires an approved TikTok app, an interactive "
            "creator/privacy confirmation, and media hosted on a URL domain verified "
            "for that app. No authorized video source or approved app is configured."
        ),
    }


def youtube_manual_result() -> Dict[str, Any]:
    return {
        "status": "manual",
        "channel": "youtube",
        "reason": (
            "The existing videos are already on the channel. Uploading new videos "
            "requires source video files and YouTube OAuth; this project only has "
            "public video IDs, not the original media files."
        ),
    }


def publish_all(
    dry_run: bool = False,
    channels: List[str] | None = None,
    language: str = "en",
    post_id: str | None = None,
) -> List[Dict[str, Any]]:
    pack = load_pack()
    post = select_post(pack, post_id)
    enabled = channels or list(CHANNELS)
    results: List[Dict[str, Any]] = []

    for channel in enabled:
        text = text_for_platform(post, channel, language)
        try:
            if not dry_run:
                result = publish_once(post, channel, language)
            elif channel == "x":
                result = x_publish(text, dry_run=True)
            elif channel == "facebook":
                result = facebook_publish(text, post["video_url"], dry_run=True)
            elif channel == "instagram":
                result = instagram_publish_or_skip(
                    text, post["thumbnail_url"], dry_run=True
                )
            elif channel == "pinterest":
                result = pinterest_publish_or_skip(
                    post, text, language, dry_run=True
                )
            elif channel == "tiktok":
                result = tiktok_manual_result()
            elif channel == "youtube":
                result = youtube_manual_result()
            else:
                result = {"status": "skipped", "channel": channel, "reason": "unsupported"}
        except (ValueError, requests.RequestException) as exc:
            result = {"status": "error", "channel": channel, "reason": str(exc)}
        results.append(result)
    return results


def publish_once(
    post: Dict[str, Any],
    channel: str,
    language: str,
) -> Dict[str, Any]:
    publication_key = f"{post['id']}:{channel}:{language}:{datetime.now(timezone.utc):%Y-%m-%d}"
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a+", encoding="utf-8") as ledger_file:
        fcntl.flock(ledger_file.fileno(), fcntl.LOCK_EX)
        ledger_file.seek(0)
        ledger_content = ledger_file.read()
        if ledger_content.strip():
            ledger = json.loads(ledger_content)
            if not isinstance(ledger, dict):
                raise ValueError("The publication ledger must contain a JSON object.")
        else:
            ledger = {}
        if publication_key in ledger:
            return {
                "status": "already-published",
                "channel": channel,
                "id": ledger[publication_key],
            }

        text = text_for_platform(post, channel, language)
        if channel == "x":
            result = x_publish(text)
        elif channel == "facebook":
            result = facebook_publish(text, post["video_url"])
        elif channel == "instagram":
            result = instagram_publish_or_skip(text, post["thumbnail_url"])
        elif channel == "pinterest":
            result = pinterest_publish_or_skip(post, text, language)
        elif channel == "tiktok":
            result = tiktok_manual_result()
        elif channel == "youtube":
            result = youtube_manual_result()
        else:
            result = {"status": "skipped", "channel": channel, "reason": "unsupported"}

        if result["status"] == "published":
            ledger[publication_key] = result.get("id")
            ledger_file.seek(0)
            ledger_file.truncate()
            json.dump(ledger, ledger_file, ensure_ascii=False, indent=2)
            ledger_file.write("\n")
            ledger_file.flush()
            os.fsync(ledger_file.fileno())
        return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish a scheduled post from the bilingual Solo Camping visibility pack"
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Preview posts without contacting social platforms.",
    )
    parser.add_argument(
        "--live",
        dest="dry_run",
        action="store_false",
        help="Publish to the selected platforms using configured account credentials.",
    )
    parser.add_argument(
        "--channel",
        action="append",
        dest="channels",
        choices=CHANNELS,
        help="Limit publishing to one or more supported channels.",
    )
    parser.add_argument(
        "--language", choices=("tr", "en"), default="en", help="Caption language."
    )
    parser.add_argument(
        "--post-id",
        help="Select one video entry; otherwise the daily rotation is used.",
    )
    parser.set_defaults(dry_run=None)
    args = parser.parse_args()

    if args.dry_run is None:
        auto_publish = os.getenv("AUTO_PUBLISH", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        args.dry_run = not auto_publish

    try:
        results = publish_all(
            dry_run=args.dry_run,
            channels=args.channels,
            language=args.language,
            post_id=args.post_id,
        )
    except (FileNotFoundError, ValueError, requests.RequestException) as exc:
        print(f"Publishing failed: {exc}", file=sys.stderr)
        return 1

    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    failed = any(result["status"] == "error" for result in results)
    incomplete_live_publish = not args.dry_run and any(
        result["status"] in {"skipped", "manual", "already-published"}
        for result in results
    )
    if incomplete_live_publish:
        print(
            "Live publishing incomplete: one or more selected channels need "
            "credentials, app approval, or source media.",
            file=sys.stderr,
        )
    return int(failed or incomplete_live_publish)


if __name__ == "__main__":
    raise SystemExit(main())

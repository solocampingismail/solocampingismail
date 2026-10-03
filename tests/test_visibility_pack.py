import html
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch

import automation.youtube_channel as youtube
import automation.submit_indexnow as indexnow


class YouTubeChannelTests(unittest.TestCase):
    def test_video_metadata_has_bilingual_copy_and_valid_limits(self):
        self.assertEqual(len(youtube.VIDEO_METADATA), 4)
        for video in youtube.VIDEO_METADATA:
            for language in youtube.SUPPORTED_LANGUAGES:
                metadata = youtube.metadata_for(video, language)
                youtube.validate_metadata(
                    metadata["title"], metadata["description"], metadata["tags"]
                )
                self.assertIn(
                    "https://linktr.ee/solocampingismail",
                    metadata["description"],
                )
                self.assertNotIn("subtitles", metadata["description"].lower())

    def test_public_video_cards_match_the_verified_youtube_titles(self):
        root = Path(__file__).resolve().parents[1]
        turkish_page = (root / "index.html").read_text(encoding="utf-8")
        english_page = html.unescape(
            (root / "en" / "index.html").read_text(encoding="utf-8")
        )
        heavy_rain = next(
            video for video in youtube.VIDEO_METADATA
            if video["video_id"] == "DGYvjoCzK9Y"
        )
        night_short = next(
            video for video in youtube.VIDEO_METADATA
            if video["video_id"] == "gfYmui17Z5s"
        )

        self.assertIn(heavy_rain["title"]["tr"], turkish_page)
        self.assertIn(heavy_rain["title"]["en"], english_page)
        self.assertIn(night_short["title"]["tr"], turkish_page)
        self.assertIn(night_short["title"]["en"], english_page)
        self.assertNotIn("Alone in Nature", english_page)
        self.assertNotIn("Camping and Nature", english_page)

    def test_plan_contains_only_youtube_metadata_in_both_languages(self):
        with tempfile.TemporaryDirectory(dir=youtube.OUTPUT_DIR) as directory:
            with patch.object(youtube, "OUTPUT_DIR", Path(directory)):
                output_path = youtube.write_metadata_plan()
            plan = output_path.read_text(encoding="utf-8")
            self.assertIn("## https://www.youtube.com/watch?v=OR62dmVC7h4", plan)
            self.assertIn("### English title", plan)
            self.assertIn("### Turkish title", plan)
            self.assertNotIn("Instagram", plan)

    def test_metadata_apply_requires_exact_handle_confirmation(self):
        client = Mock()
        with self.assertRaisesRegex(ValueError, "confirm the target channel"):
            youtube.apply_metadata(
                client,
                youtube.VIDEO_METADATA[0],
                "en",
                "different-channel",
            )
        client.get.assert_not_called()

    def test_metadata_apply_rejects_video_from_another_channel(self):
        client = Mock()
        client.get.side_effect = [
            {"items": [{"id": "UCexample"}]},
            {
                "items": [
                    {
                        "snippet": {
                            "channelId": "UCsomeone-else",
                            "defaultLanguage": "en",
                        }
                    }
                ]
            },
        ]
        with patch.dict("os.environ", {"YOUTUBE_CHANNEL_ID": "UCexample"}):
            with self.assertRaisesRegex(ValueError, "does not belong"):
                youtube.apply_metadata(
                    client, youtube.VIDEO_METADATA[0], "en", "solocampingismail"
                )
        client.put.assert_not_called()

    def test_metadata_apply_backs_up_video_and_preserves_other_localizations(self):
        client = Mock()
        original_video = {
            "id": "OR62dmVC7h4",
            "snippet": {
                "channelId": "UCexample",
                "defaultLanguage": "en",
                "categoryId": "22",
                "title": "Existing title",
                "description": "Existing description",
            },
            "localizations": {"es": {"title": "Título", "description": "Descripción"}},
        }
        client.get.side_effect = [
            {"items": [{"id": "UCexample"}]},
            {"items": [original_video]},
        ]
        client.put.return_value = {"items": [{"id": "OR62dmVC7h4"}]}

        with tempfile.TemporaryDirectory(dir=youtube.OUTPUT_DIR) as directory:
            with patch.dict("os.environ", {"YOUTUBE_CHANNEL_ID": "UCexample"}):
                with patch.object(youtube, "BACKUP_DIR", Path(directory)):
                    result = youtube.apply_metadata(
                        client,
                        youtube.VIDEO_METADATA[0],
                        "en",
                        "solocampingismail",
                    )
            backup = json.loads(Path(directory, Path(result["backup"]).name).read_text())

        self.assertEqual(backup, original_video)
        self.assertEqual(result["status"], "updated")
        update = client.put.call_args.args[2]
        self.assertEqual(update["localizations"]["es"], original_video["localizations"]["es"])
        self.assertIn("en", update["localizations"])
        self.assertIn("tr", update["localizations"])

    def test_media_kit_uses_requested_youtube_handle(self):
        root = Path(__file__).resolve().parents[1]
        for page in (root / "index.html", root / "en" / "index.html"):
            content = page.read_text(encoding="utf-8")
            self.assertIn("https://www.youtube.com/@solocampingismail", content)

    def test_video_discovery_pages_and_sitemaps_are_connected(self):
        root = Path(__file__).resolve().parents[1]
        sitemap = ET.parse(root / "video-sitemap.xml").getroot()
        namespaces = {
            "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "v": "http://www.google.com/schemas/sitemap-video/1.1",
        }
        entries = sitemap.findall("s:url", namespaces)
        self.assertEqual(len(entries), 4)
        for entry in entries:
            page_url = entry.findtext("s:loc", namespaces=namespaces)
            self.assertIsNotNone(page_url)
            relative_page = page_url.split(
                "https://solocampingismail.github.io/solocampingismail/", 1
            )[1]
            self.assertTrue((root / relative_page / "index.html").is_file())
            self.assertTrue(
                entry.findtext("v:video/v:title", namespaces=namespaces)
            )
            self.assertTrue(
                entry.findtext("v:video/v:description", namespaces=namespaces)
            )
            self.assertTrue(
                entry.findtext("v:video/v:thumbnail_loc", namespaces=namespaces)
            )
            self.assertTrue(
                entry.findtext("v:video/v:player_loc", namespaces=namespaces)
            )
            video_id = entry.findtext("v:video/v:player_loc", namespaces=namespaces)
            video_id = video_id.rsplit("/", 1)[-1]
            self.assertIn(
                f"youtube-nocookie.com/embed/{video_id}",
                (root / relative_page / "index.html").read_text(encoding="utf-8"),
            )

        robots = (root / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("/video-sitemap.xml", robots)

    def test_video_pages_expose_parseable_video_object_data(self):
        root = Path(__file__).resolve().parents[1]
        pages = (
            root / "videos/DGYvjoCzK9Y/index.html",
            root / "en/videos/DGYvjoCzK9Y/index.html",
            root / "videos/gfYmui17Z5s/index.html",
            root / "en/videos/gfYmui17Z5s/index.html",
        )
        for page in pages:
            content = page.read_text(encoding="utf-8")
            structured_data = re.search(
                r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
                content,
                re.DOTALL,
            )
            self.assertIsNotNone(structured_data, page)
            video_object = json.loads(structured_data.group(1))
            self.assertEqual(video_object["@type"], "VideoObject")
            self.assertIn("youtube.com/watch?v=", video_object["url"])

    def test_indexnow_submits_only_site_urls_from_both_sitemaps(self):
        urls = indexnow.load_urls()
        payload = indexnow.build_payload(
            urls, indexnow.KEY_PATH.read_text(encoding="utf-8").strip()
        )
        self.assertEqual(len(urls), 6)
        self.assertEqual(payload["host"], "solocampingismail.github.io")
        self.assertEqual(payload["urlList"], urls)
        self.assertEqual(
            payload["keyLocation"],
            "https://solocampingismail.github.io/solocampingismail/"
            + indexnow.KEY_PATH.name,
        )
        self.assertFalse(any("youtube.com" in url for url in urls))

    def test_indexnow_refuses_invalid_keys_and_external_urls(self):
        site_url = "https://solocampingismail.github.io/solocampingismail/"
        with self.assertRaisesRegex(ValueError, "IndexNow key"):
            indexnow.build_payload([site_url], "bad key")
        with self.assertRaisesRegex(ValueError, "outside"):
            indexnow.build_payload(
                ["https://www.youtube.com/@solocampingismail"],
                indexnow.KEY_PATH.read_text(encoding="utf-8").strip(),
            )

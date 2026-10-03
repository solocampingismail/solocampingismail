import html
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import automation.youtube_channel as youtube


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

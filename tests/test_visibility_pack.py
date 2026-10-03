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
import automation.generate_youtube_discovery as discovery


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
            self.assertIn(
                "UC87pVteBukFzQv_xA1UC6Kg",
                content,
            )
            self.assertIn(
                "UU87pVteBukFzQv_xA1UC6Kg",
                content,
            )
            self.assertNotIn("UC87pVteBukFZqv_xA1UC6Kg", content)

    def test_bilingual_homepages_offer_manual_global_channel_sharing(self):
        root = Path(__file__).resolve().parents[1]
        for page in (root / "index.html", root / "en" / "index.html"):
            content = html.unescape(page.read_text(encoding="utf-8"))
            self.assertIn("https://wa.me/?text=", content)
            self.assertIn("https://t.me/share/url?", content)
            self.assertIn("https://www.facebook.com/sharer/sharer.php?", content)
            self.assertIn("https://twitter.com/intent/tweet?", content)
            self.assertIn("https://www.reddit.com/submit?", content)
            self.assertIn(
                "https://www.youtube.com/@solocampingismail",
                content,
            )

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

    def test_verified_channel_rss_creates_recent_video_pages_and_sitemap(self):
        feed = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:yt="http://www.youtube.com/xml/schemas/2015"
              xmlns:media="http://search.yahoo.com/mrss/">
          <yt:channelId>87pVteBukFzQv_xA1UC6Kg</yt:channelId>
          <entry>
            <yt:videoId>abcDE123_-9</yt:videoId>
            <title>Rain &amp; Camp &lt;script&gt;</title>
            <published>2026-10-01T12:30:00+00:00</published>
            <media:group>
              <media:description>Camping &amp; rain.</media:description>
              <media:thumbnail url="https://i.ytimg.com/vi/abcDE123_-9/hqdefault.jpg"/>
            </media:group>
          </entry>
        </feed>"""
        videos = discovery.parse_feed(feed)
        self.assertEqual(videos[0]["video_id"], "abcDE123_-9")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page_dir = root / "channel-videos"
            sitemap_path = root / "youtube-video-sitemap.xml"
            generated = discovery.generate_discovery_pages(
                videos,
                output_dir=page_dir,
                sitemap_path=sitemap_path,
                curated_pages_dir=root / "curated",
                localizations={
                    "abcDE123_-9": {
                        "title": "A Rainy Camp",
                        "description": "A quiet camp in the rain.",
                    }
                },
            )
            self.assertEqual(generated, 1)
            page = (page_dir / "abcDE123_-9" / "index.html").read_text()
            self.assertIn("Rain &amp; Camp &lt;script&gt;", page)
            self.assertIn(r"\u003cscript>", page)
            self.assertIn(
                'hreflang="en" href="https://solocampingismail.github.io/'
                "solocampingismail/en/channel-videos/abcDE123_-9/\"",
                page,
            )
            english_page = (
                root / "en" / "channel-videos" / "abcDE123_-9" / "index.html"
            ).read_text()
            self.assertIn('<html lang="en">', english_page)
            self.assertIn("A Rainy Camp", english_page)
            self.assertIn("Original Turkish title and description", english_page)
            self.assertIn("Check YouTube’s CC menu", english_page)
            generated_sitemap = ET.parse(sitemap_path).getroot()
            entries = generated_sitemap.findall(
                "s:url",
                {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"},
            )
            self.assertEqual(len(entries), 2)
            alternate_namespaces = {
                "x": "http://www.w3.org/1999/xhtml"
            }
            for entry in entries:
                alternate_hreflangs = {
                    link.get("hreflang")
                    for link in entry.findall("x:link", alternate_namespaces)
                }
                self.assertEqual(
                    alternate_hreflangs, {"tr", "en", "x-default"}
                )
            video_namespaces = {
                "v": "http://www.google.com/schemas/sitemap-video/1.1"
            }
            for entry in entries:
                description = entry.findtext(
                    "v:video/v:description", namespaces=video_namespaces
                )
                publication_date = entry.findtext(
                    "v:video/v:publication_date", namespaces=video_namespaces
                )
                self.assertLessEqual(len(description), 2048)
                self.assertEqual(publication_date, videos[0]["published"])

    def test_video_sitemap_does_not_advertise_missing_language_pages(self):
        video = {
                "video_id": "abcDE123_-9",
                "title": "Rainy camp",
                "description": "A quiet rainy camp.",
                "published": "2026-10-01T12:30:00+00:00",
                "thumbnail": "https://i.ytimg.com/vi/abcDE123_-9/hqdefault.jpg",
        }
        sitemap = discovery.build_video_sitemap([video], {})
        namespaces = {
                "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
                "x": "http://www.w3.org/1999/xhtml",
        }
        entry = sitemap.find("s:url", namespaces)
        self.assertIsNotNone(entry)
        self.assertEqual(
                {
                    link.get("hreflang")
                    for link in entry.findall("x:link", namespaces)
                },
                {"tr", "x-default"},
        )
        page = discovery.render_page(video)
        self.assertNotIn('hreflang="en"', page)

    def test_current_recent_uploads_have_english_localization_drafts(self):
        root = Path(__file__).resolve().parents[1]
        localizations = discovery.load_english_localizations()
        sitemap = ET.parse(root / "youtube-video-sitemap.xml").getroot()
        namespaces = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        english_video_ids = {
            entry.findtext("s:loc", namespaces=namespaces)
            .rstrip("/")
            .rsplit("/", 1)[-1]
            for entry in sitemap.findall("s:url", namespaces)
            if "/en/channel-videos/" in entry.findtext("s:loc", namespaces=namespaces)
        }
        self.assertTrue(english_video_ids)
        self.assertTrue(english_video_ids.issubset(localizations))

    def test_channel_rss_generator_rejects_wrong_channel_and_thumbnail_hosts(self):
        wrong_channel_feed = b"""<feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:yt="http://www.youtube.com/xml/schemas/2015">
          <yt:channelId>UCnotthischannel</yt:channelId></feed>"""
        with self.assertRaisesRegex(ValueError, "does not match"):
            discovery.parse_feed(wrong_channel_feed)

        bad_thumbnail_feed = b"""<feed xmlns="http://www.w3.org/2005/Atom"
              xmlns:yt="http://www.youtube.com/xml/schemas/2015"
              xmlns:media="http://search.yahoo.com/mrss/">
          <yt:channelId>87pVteBukFzQv_xA1UC6Kg</yt:channelId>
          <entry><yt:videoId>abcDE123_-9</yt:videoId><title>Camping</title>
            <published>2026-10-01T12:30:00+00:00</published>
            <media:group><media:thumbnail url="https://attacker.example/image.jpg"/></media:group>
          </entry></feed>"""
        with self.assertRaisesRegex(ValueError, "thumbnail URL"):
            discovery.parse_feed(bad_thumbnail_feed)

    def test_generated_page_metadata_escapes_long_text_before_truncating(self):
        video = {
            "video_id": "abcDE123_-9",
            "title": "Camp",
            "description": "a" * 299 + "&",
            "published": "2026-10-01T12:30:00+00:00",
            "thumbnail": "https://i.ytimg.com/vi/abcDE123_-9/hqdefault.jpg",
        }
        page = discovery.render_page(video)
        expected_meta = f'<meta name="description" content="{"a" * 299}&amp;">'
        self.assertIn(expected_meta, page)

    def test_indexnow_submits_only_site_urls_from_both_sitemaps(self):
        urls = indexnow.load_urls()
        payload = indexnow.build_payload(
            urls, indexnow.KEY_PATH.read_text(encoding="utf-8").strip()
        )
        with patch.object(indexnow, "SITEMAPS", indexnow.SITEMAPS[:2]):
            baseline_urls = set(indexnow.load_urls())
        generated_sitemap = ET.parse(
            Path(__file__).resolve().parents[1] / "youtube-video-sitemap.xml"
        ).getroot()
        dynamic_urls = {
            element.text.strip()
            for element in generated_sitemap.iter(indexnow.SITEMAP_NAMESPACE)
            if element.text
        }
        self.assertEqual(set(urls), baseline_urls | dynamic_urls)
        self.assertGreaterEqual(len(urls), len(baseline_urls))
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

import unittest

import automation.generate_visibility_pack as generator


class VisibilityPackTests(unittest.TestCase):
    def test_pack_uses_existing_videos_and_has_bilingual_captions(self):
        pack = generator.build_pack("2026-10-03")

        self.assertEqual(len(pack["posts"]), 4)
        self.assertEqual(pack["languages"], ["tr", "en"])
        expected_channels = {
            "youtube",
            "instagram",
            "tiktok",
            "x",
            "facebook",
            "pinterest",
        }

        first_post = pack["posts"][0]
        self.assertEqual(first_post["video_id"], "OR62dmVC7h4")
        self.assertEqual(
            first_post["video_url"],
            "https://www.youtube.com/watch?v=OR62dmVC7h4",
        )
        self.assertEqual(set(first_post["localized_platforms"]), {"tr", "en"})

        for language in ("tr", "en"):
            captions = first_post["localized_platforms"][language]
            self.assertEqual(
                set(captions),
                expected_channels,
            )
            for platform_name, payload in captions.items():
                self.assertTrue(payload["body"].strip(), platform_name)
                self.assertTrue(payload["cta"].strip(), platform_name)
                if platform_name == "youtube":
                    site_url = "https://solocampingismail.github.io/solocampingismail/"
                    expected_link = site_url + ("en/" if language == "en" else "")
                    self.assertIn(expected_link, payload["body"])
                elif platform_name in {"instagram", "tiktok"}:
                    profile_link_prompt = (
                        "Linktree bağlantısı"
                        if language == "tr"
                        else "Linktree link in my profile"
                    )
                    self.assertIn(profile_link_prompt, payload["body"])
                elif platform_name == "pinterest":
                    self.assertLessEqual(len(payload["body"]), 800)
                    self.assertIn(
                        "https://linktr.ee/solocampingismail", payload["body"]
                    )
                else:
                    self.assertIn(first_post["video_url"], payload["body"])
                    self.assertIn(
                        "https://linktr.ee/solocampingismail", payload["body"]
                    )

    def test_engagement_questions_are_specific_to_each_video(self):
        pack = generator.build_pack("2026-10-03")
        questions = {
            post["engagement_prompt"]["en"] for post in pack["posts"]
        }
        self.assertEqual(len(questions), len(pack["posts"]))

    def test_x_captions_fit_character_limit_in_both_languages(self):
        pack = generator.build_pack("2026-10-03")
        for post in pack["posts"]:
            for language in ("tr", "en"):
                caption = post["localized_platforms"][language]["x"]["body"]
                self.assertLessEqual(len(caption), 280, (language, caption))
                pin = post["localized_platforms"][language]["pinterest"]["body"]
                self.assertLessEqual(len(pin), 800, (language, pin))

    def test_media_kit_profiles_match_linktree_in_both_site_languages(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        expected_profiles = (
            "https://www.youtube.com/@solocampismail",
            "https://www.instagram.com/solocampingismail",
            "https://www.tiktok.com/@solocampingismail",
            "https://www.facebook.com/solocampingismails",
            "https://x.com/solocampismail",
            "https://www.pinterest.com/solocampingismail",
        )
        for page in (root / "index.html", root / "en" / "index.html"):
            content = page.read_text(encoding="utf-8")
            for profile in expected_profiles:
                self.assertIn(profile, content, (page, profile))
        turkish_page = (root / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("youtube.com/@solocampingismail", turkish_page)
        self.assertNotIn('facebook.com/solocampingismail"', turkish_page)


if __name__ == "__main__":
    unittest.main()

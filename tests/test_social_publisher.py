import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import automation.social_publisher as publisher


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class SocialPublisherTests(unittest.TestCase):
    def test_each_scheduled_day_gets_a_different_video(self):
        pack = {
            "posts": [
                {"id": f"video-{index}", "video_id": str(index)}
                for index in range(4)
            ]
        }
        selected = [
            publisher.select_post(pack, scheduled_date=date(2026, 10, day))["id"]
            for day in (6, 8, 10)
        ]

        self.assertEqual(len(set(selected)), 3)

    def test_x_uses_user_bearer_token_without_truncating_caption(self):
        caption = "A complete caption with a video link."
        with patch.dict(
            os.environ, {"X_USER_ACCESS_TOKEN": "test-user-token"}, clear=True
        ), patch.object(
            publisher.requests,
            "post",
            return_value=FakeResponse({"data": {"id": "tweet-123"}}),
        ) as request:
            result = publisher.x_publish(caption)

        self.assertEqual(result["status"], "published")
        self.assertEqual(result["id"], "tweet-123")
        self.assertEqual(
            request.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-user-token",
        )
        self.assertEqual(request.call_args.kwargs["json"], {"text": caption})

    def test_x_authorization_uses_user_token_as_bearer(self):
        token = "test-user-token"
        with patch.dict(
            os.environ, {"X_USER_ACCESS_TOKEN": token}, clear=True
        ), patch.object(
            publisher.requests,
            "post",
            return_value=FakeResponse({"data": {"id": "tweet-123"}}),
        ) as request:
            publisher.x_publish("A short post")

        self.assertEqual(
            request.call_args.kwargs["headers"]["Authorization"],
            f"Bearer {token}",
        )

    def test_instagram_creates_then_publishes_image_container(self):
        responses = [
            FakeResponse({"id": "container-123"}),
            FakeResponse({"id": "post-456"}),
        ]
        with patch.object(
            publisher.requests, "post", side_effect=responses
        ) as request:
            result = publisher.instagram_publish(
                "A caption",
                "instagram-user",
                "https://i.ytimg.com/vi/video/hqdefault.jpg",
                "test-access-token",
                "v22.0",
            )

        self.assertEqual(result["status"], "published")
        self.assertEqual(result["id"], "post-456")
        self.assertEqual(request.call_count, 2)
        self.assertTrue(request.call_args_list[0].args[0].endswith("/media"))
        self.assertTrue(
            request.call_args_list[1].args[0].endswith("/media_publish")
        )
        self.assertEqual(
            request.call_args_list[1].kwargs["data"]["creation_id"],
            "container-123",
        )

    def test_pinterest_creates_pin_with_thumbnail_and_link(self):
        with patch.object(
            publisher.requests,
            "post",
            return_value=FakeResponse({"id": "pin-123"}),
        ) as request:
            result = publisher.pinterest_publish(
                "Forest camp",
                "A quiet night outdoors.",
                "https://linktr.ee/solocampingismail",
                "https://i.ytimg.com/vi/video/hqdefault.jpg",
                "board-123",
                "test-access-token",
            )

        self.assertEqual(result["status"], "published")
        self.assertEqual(result["id"], "pin-123")
        self.assertEqual(request.call_args.args[0], "https://api.pinterest.com/v5/pins")
        self.assertEqual(
            request.call_args.kwargs["json"]["media_source"],
            {
                "source_type": "image_url",
                "url": "https://i.ytimg.com/vi/video/hqdefault.jpg",
            },
        )
        self.assertEqual(
            request.call_args.kwargs["json"]["link"],
            "https://linktr.ee/solocampingismail",
        )

    def test_dry_run_needs_no_credentials_and_makes_no_requests(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            publisher.requests, "post"
        ) as request:
            result = publisher.x_publish("Preview only", dry_run=True)

        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["message"], "Preview only")
        request.assert_not_called()

    def test_published_platform_is_not_published_twice_same_day(self):
        post = {
            "id": "video-1",
            "title": "Camp",
            "video_url": "https://youtube.com/watch?v=video-1",
            "localized_platforms": {"en": {"x": {"body": "Camp today"}}},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "publishing-ledger.json"
            with patch.object(publisher, "LEDGER_PATH", ledger), patch.object(
                publisher,
                "x_publish",
                return_value={
                    "status": "published",
                    "channel": "x",
                    "id": "x-123",
                },
            ) as publish:
                first = publisher.publish_once(post, "x", "en")
                second = publisher.publish_once(post, "x", "en")

        self.assertEqual(first["status"], "published")
        self.assertEqual(second["status"], "already-published")
        publish.assert_called_once()

    def test_corrupt_publication_ledger_fails_closed(self):
        post = {
            "id": "video-1",
            "title": "Camp",
            "video_url": "https://youtube.com/watch?v=video-1",
            "localized_platforms": {"en": {"x": {"body": "Camp today"}}},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "publishing-ledger.json"
            ledger.write_text("{invalid", encoding="utf-8")
            with patch.object(publisher, "LEDGER_PATH", ledger), patch.object(
                publisher, "x_publish"
            ) as publish:
                with self.assertRaises(ValueError):
                    publisher.publish_once(post, "x", "en")
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()

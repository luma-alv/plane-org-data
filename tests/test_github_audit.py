import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from validation.github_audit import GitHubAPI, bounded_endpoint, pagination_status, rate_limit_status, parse_link_header


class GitHubAuditHelpersTest(unittest.TestCase):
    def test_parse_link_header_and_pagination(self):
        headers = {"Link": '<https://api.github.com?page=2>; rel="next", <https://api.github.com?page=4>; rel="last"'}
        self.assertEqual(parse_link_header(headers["Link"])["next"], "https://api.github.com?page=2")
        self.assertFalse(pagination_status(headers)["complete"])

    def test_pagination_without_next_is_complete(self):
        status = pagination_status({})
        self.assertTrue(status["complete"])
        self.assertFalse(status["has_next"])

    def test_rate_limit_values_are_parsed(self):
        status = rate_limit_status({"X-RateLimit-Limit": "60", "X-RateLimit-Remaining": "59", "X-RateLimit-Reset": "123"})
        self.assertEqual(status["limit"], 60)
        self.assertEqual(status["remaining"], 59)
        self.assertEqual(status["reset_epoch"], 123)

    def test_invalid_rate_limit_values_become_null(self):
        self.assertIsNone(rate_limit_status({"X-RateLimit-Limit": "unknown"})["limit"])

    def test_bounded_endpoint_processes_records_and_pagination(self):
        class FakeAPI:
            def get(self, path):
                return ([{"id": 1}, {"id": 2}], {"Link": '<https://api.github.com?page=2>; rel="next"'})

        result = bounded_endpoint(FakeAPI(), "/sample")
        self.assertEqual(result["records_returned"], 2)
        self.assertTrue(result["pagination"]["has_next"])

    @patch("validation.github_audit.urlopen")
    def test_api_http_errors_are_reported(self, mocked_urlopen):
        error = HTTPError("https://api.github.com/test", 403, "forbidden", {}, BytesIO(b"rate limited"))
        mocked_urlopen.side_effect = error
        with self.assertRaisesRegex(RuntimeError, "HTTP 403"):
            GitHubAPI().get("/test")


if __name__ == "__main__":
    unittest.main()

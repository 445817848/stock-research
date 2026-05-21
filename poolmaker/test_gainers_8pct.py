"""Unit tests for fetch_gainers_until_8pct mocking requests.get (no network)."""

import json
import unittest
from unittest import mock

from rank_fetcher import fetch_gainers_until_8pct


def _make_response(page_items):
    """Build fake East Money JSON response text."""
    payload = {
        "data": {
            "diff": page_items,
        },
    }
    return json.dumps(payload)


def _make_mock_resp(items):
    """Create a mock requests.Response with .text and .raise_for_status()."""
    resp = mock.Mock()
    resp.text = _make_response(items)
    resp.raise_for_status = mock.Mock()
    return resp


class TestFetchGainersUntil8Pct(unittest.TestCase):
    """Mock tests for fetch_gainers_until_8pct using requests.get."""

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher.requests.get")
    def test_all_above_8pct_until_page3(self, mock_get, _mock_sleep):
        """
        Scenario 1: All stocks > 8%% on pages 1-3.
        Should fetch 300 stocks (3 pages) then stop on empty page 4.
        """
        def side_effect(url, **kwargs):
            # Extract page number from URL
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            page = int(qs.get("pn", [1])[0])

            if page == 1:
                items = [
                    {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 20.0 - i * 0.05}
                    for i in range(100)
                ]  # last = 15.05
            elif page == 2:
                items = [
                    {"f12": f"{i + 100:06d}", "f14": f"Stock{i + 100}", "f3": 15.0 - i * 0.05}
                    for i in range(100)
                ]  # last = 10.05
            elif page == 3:
                items = [
                    {"f12": f"{i + 200:06d}", "f14": f"Stock{i + 200}", "f3": 10.0 - i * 0.015}
                    for i in range(100)
                ]  # last = 8.515 (> 8.0)
            else:
                items = []
            return _make_mock_resp(items)

        mock_get.side_effect = side_effect

        result = fetch_gainers_until_8pct(min_count=150)

        self.assertEqual(mock_get.call_count, 4)
        self.assertEqual(len(result), 300)
        self.assertGreater(result[99]["change_pct"], 8.0)
        self.assertGreater(result[-1]["change_pct"], 8.0)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher.requests.get")
    def test_pct_drops_on_page1_but_min_count_forces_page2(self, mock_get, _mock_sleep):
        """
        Scenario 2: change_pct drops to 7%% on page 1,
        but min_count=150 forces fetching page 2 (should fetch 200).
        """
        def side_effect(url, **kwargs):
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            page = int(qs.get("pn", [1])[0])

            if page == 1:
                items = [
                    {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 10.0 - i * 0.03}
                    for i in range(100)
                ]  # last = 7.03 (<= 8.0)
            elif page == 2:
                items = [
                    {"f12": f"{i + 100:06d}", "f14": f"Stock{i + 100}", "f3": 7.0 - i * 0.03}
                    for i in range(100)
                ]  # last = 4.03
            else:
                items = []
            return _make_mock_resp(items)

        mock_get.side_effect = side_effect

        result = fetch_gainers_until_8pct(min_count=150)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(result), 200)
        self.assertLessEqual(result[99]["change_pct"], 8.0)
        self.assertLessEqual(result[-1]["change_pct"], 8.0)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher.requests.get")
    def test_less_than_150_total(self, mock_get, _mock_sleep):
        """
        Scenario 3: Less than 150 stocks total available.
        Should fetch all and stop on empty page.
        """
        def side_effect(url, **kwargs):
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            page = int(qs.get("pn", [1])[0])

            if page == 1:
                items = [
                    {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 10.0 - i * 0.1}
                    for i in range(80)
                ]  # last = 2.1 (<= 8.0)
            else:
                items = []
            return _make_mock_resp(items)

        mock_get.side_effect = side_effect

        result = fetch_gainers_until_8pct(min_count=150)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(result), 80)
        self.assertLess(len(result), 150)
        self.assertLessEqual(result[-1]["change_pct"], 8.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

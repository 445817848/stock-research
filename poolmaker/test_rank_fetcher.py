"""Tests for rank_fetcher.py using only the Python standard library."""

import json
import os
import unittest
from unittest import mock

from rank_fetcher import (
    _parse_item,
    _strip_jsonp,
    fetch_ranking,
)


class TestStripJsonp(unittest.TestCase):
    """Tests for _strip_jsonp."""

    def test_jsonp_wrapper(self):
        """jQuery123({...}) -> inner JSON string."""
        raw = 'jQuery123({"data": {"diff": [{"f12": "300302"}]}})'
        stripped = _strip_jsonp(raw)
        self.assertEqual(stripped, '{"data": {"diff": [{"f12": "300302"}]}}')
        # Verify it's valid JSON
        parsed = json.loads(stripped)
        self.assertEqual(parsed["data"]["diff"][0]["f12"], "300302")

    def test_plain_json(self):
        """Plain JSON should pass through unchanged."""
        raw = '{"data": {"diff": []}}'
        stripped = _strip_jsonp(raw)
        self.assertEqual(stripped, raw)

    def test_no_parentheses(self):
        """String without parentheses returns as-is."""
        raw = '{"key": "value"}'
        stripped = _strip_jsonp(raw)
        self.assertEqual(stripped, raw)


class TestParseItem(unittest.TestCase):
    """Tests for _parse_item field mapping."""

    def test_field_mapping(self):
        """f12→code, f14→name, f3→change_pct, and other fields."""
        raw = {
            "f12": "300302",
            "f14": "同有科技",
            "f2": 12.34,
            "f3": 5.67,
            "f4": 0.66,
            "f5": 123456,
            "f6": 789012,
            "f17": 11.80,
            "f18": 11.68,
            "f20": 5000000000,
            "unknown": "keep",
        }
        parsed = _parse_item(raw)
        self.assertEqual(parsed["code"], "300302")
        self.assertEqual(parsed["name"], "同有科技")
        self.assertEqual(parsed["price"], 12.34)
        self.assertEqual(parsed["change_pct"], 5.67)
        self.assertEqual(parsed["change_amt"], 0.66)
        self.assertEqual(parsed["volume"], 123456)
        self.assertEqual(parsed["turnover"], 789012)
        self.assertEqual(parsed["open"], 11.80)
        self.assertEqual(parsed["prev_close"], 11.68)
        self.assertEqual(parsed["market_cap"], 5000000000)
        # Unknown keys are preserved with original name
        self.assertEqual(parsed["unknown"], "keep")


class TestFetchRankingMock(unittest.TestCase):
    """Mock tests for fetch_ranking (no network required)."""

    @mock.patch("rank_fetcher._fetch_page")
    def test_fetch_ranking_gainers_aggregates_pages(self, mock_fetch_page):
        """fetch_ranking should call _fetch_page for each page and aggregate results."""
        mock_fetch_page.side_effect = [
            [{"f12": "300302", "f14": "同有科技", "f3": 10.01}],
            [{"f12": "000001", "f14": "平安银行", "f3": 9.98}],
        ]

        result = fetch_ranking("gainers")

        # Should have fetched 2 pages
        self.assertEqual(mock_fetch_page.call_count, 2)
        mock_fetch_page.assert_any_call("f3", 1, 1)
        mock_fetch_page.assert_any_call("f3", 1, 2)

        # Results should be parsed and aggregated
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["code"], "300302")
        self.assertEqual(result[0]["name"], "同有科技")
        self.assertEqual(result[0]["change_pct"], 10.01)
        self.assertEqual(result[1]["code"], "000001")
        self.assertEqual(result[1]["name"], "平安银行")

    @mock.patch("rank_fetcher._fetch_page")
    def test_fetch_ranking_losers_uses_correct_sort(self, mock_fetch_page):
        """fetch_ranking('losers') should use ascending sort on f3."""
        mock_fetch_page.return_value = []
        fetch_ranking("losers")
        mock_fetch_page.assert_called_with("f3", -1, 2)

    @mock.patch("rank_fetcher._fetch_page")
    def test_fetch_ranking_active_uses_turnover(self, mock_fetch_page):
        """fetch_ranking('active') should sort by turnover (f6)."""
        mock_fetch_page.return_value = []
        fetch_ranking("active")
        mock_fetch_page.assert_called_with("f6", 1, 2)

    def test_fetch_ranking_invalid_type(self):
        """Unknown rank_type should raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            fetch_ranking("unknown")
        self.assertIn("unknown", str(ctx.exception))


class TestFetchRankingPagination(unittest.TestCase):
    """Mock tests for fetch_ranking pagination / stop logic."""

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher._fetch_page")
    def test_stops_when_both_count_and_pct_met(self, mock_fetch_page, _mock_sleep):
        """Stop when count >= min_count AND last change_pct <= stop_pct."""
        # Page 1: 100 items, change_pct descending from 20.0 to 11.0
        page1 = [
            {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 20.0 - i * 0.09}
            for i in range(100)
        ]
        # Page 2: 100 items, change_pct descending from 10.0 to 2.08
        page2 = [
            {"f12": f"{i + 100:06d}", "f14": f"Stock{i + 100}", "f3": 10.0 - i * 0.08}
            for i in range(100)
        ]
        mock_fetch_page.side_effect = [page1, page2]

        result = fetch_ranking("gainers", min_count=150, stop_pct=8.0)

        self.assertEqual(mock_fetch_page.call_count, 2)
        self.assertEqual(len(result), 200)
        self.assertAlmostEqual(result[-1]["change_pct"], 2.08, places=2)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher._fetch_page")
    def test_continues_when_count_met_but_pct_not_met(self, mock_fetch_page, _mock_sleep):
        """Keep fetching if count >= min_count but last change_pct > stop_pct."""
        page1 = [
            {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 20.0 - i * 0.05}
            for i in range(100)
        ]  # last = 15.05
        page2 = [
            {"f12": f"{i + 100:06d}", "f14": f"Stock{i + 100}", "f3": 15.0 - i * 0.05}
            for i in range(100)
        ]  # last = 10.05
        page3 = []
        mock_fetch_page.side_effect = [page1, page2, page3]

        result = fetch_ranking("gainers", min_count=150, stop_pct=8.0)

        self.assertEqual(mock_fetch_page.call_count, 3)
        self.assertEqual(len(result), 200)
        self.assertGreater(result[-1]["change_pct"], 8.0)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher._fetch_page")
    def test_continues_when_pct_met_but_count_not_met(self, mock_fetch_page, _mock_sleep):
        """Keep fetching if last change_pct <= stop_pct but count < min_count."""
        page1 = [
            {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 10.0 - i * 0.05}
            for i in range(80)
        ]  # last = 6.05 (<= 8.0)
        page2 = [
            {"f12": f"{i + 80:06d}", "f14": f"Stock{i + 80}", "f3": 6.0 - i * 0.05}
            for i in range(80)
        ]  # last = 2.05
        mock_fetch_page.side_effect = [page1, page2]

        result = fetch_ranking("gainers", min_count=150, stop_pct=8.0)

        self.assertEqual(mock_fetch_page.call_count, 2)
        self.assertEqual(len(result), 160)
        self.assertLessEqual(result[-1]["change_pct"], 8.0)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher._fetch_page")
    def test_stops_on_empty_data(self, mock_fetch_page, _mock_sleep):
        """Stop immediately when East Money returns empty diff."""
        page1 = [
            {"f12": f"{i:06d}", "f14": f"Stock{i}", "f3": 10.0}
            for i in range(100)
        ]
        page2 = []
        mock_fetch_page.side_effect = [page1, page2]

        result = fetch_ranking("gainers", min_count=150, stop_pct=8.0)

        self.assertEqual(mock_fetch_page.call_count, 2)
        self.assertEqual(len(result), 100)

    @mock.patch("rank_fetcher.time.sleep")
    @mock.patch("rank_fetcher._fetch_page")
    def test_sequential_fetching_no_overlap(self, mock_fetch_page, _mock_sleep):
        """Pages must be fetched sequentially (1, 2, 3...) with no concurrent calls."""
        page1 = [{"f12": "000001", "f14": "A", "f3": 10.0}]
        page2 = [{"f12": "000002", "f14": "B", "f3": 9.0}]
        page3 = []
        mock_fetch_page.side_effect = [page1, page2, page3]

        fetch_ranking("gainers", min_count=2, stop_pct=5.0)

        calls = mock_fetch_page.call_args_list
        self.assertEqual(len(calls), 3)
        # Verify page numbers are sequential
        self.assertEqual(calls[0], mock.call("f3", 1, 1))
        self.assertEqual(calls[1], mock.call("f3", 1, 2))
        self.assertEqual(calls[2], mock.call("f3", 1, 3))


class TestFetchRankingIntegration(unittest.TestCase):
    """Integration test that hits the real East Money API.

    Skipped if NO_NETWORK=1 is set in the environment.
    """

    @classmethod
    def setUpClass(cls):
        if os.environ.get("NO_NETWORK") == "1":
            raise unittest.SkipTest("NO_NETWORK is set")

    def test_fetch_gainers_contains_300302(self):
        """Real API call: verify stock code 300302 appears in ranking results.

        Skips if the remote API is unreachable.
        """
        import urllib.error

        # Try all rank types with extra pages to maximise chance of finding 300302
        with mock.patch("rank_fetcher.PAGES", 20):
            for rank_type in ("gainers", "losers", "active"):
                try:
                    result = fetch_ranking(rank_type)
                except (urllib.error.URLError, ConnectionError, OSError) as exc:
                    raise unittest.SkipTest(
                        f"East Money API unreachable from this environment: {exc}"
                    )

                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)

                codes = [item["code"] for item in result]
                if "300302" in codes:
                    item = next(item for item in result if item["code"] == "300302")
                    self.assertIn("name", item)
                    self.assertIn("change_pct", item)
                    self.assertIsNotNone(item["name"])
                    return

        self.fail(
            "Stock 300302 not found in top results across gainers, losers, or active."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

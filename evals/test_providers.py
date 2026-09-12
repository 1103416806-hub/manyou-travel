import asyncio
import os
import unittest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from manyou.models import ImportRequest, WeatherRequest
from manyou.providers import ProviderError, fetch_weather, import_source, validate_import_url


class ProviderBoundaries(unittest.IsolatedAsyncioTestCase):
    def test_import_rejects_private_and_spoofed_hosts(self):
        urls = ["http://www.xiaohongshu.com/explore/a", "https://127.0.0.1/a",
                "https://www.xiaohongshu.com.evil.example/a", "https://user:pass@www.douyin.com/a",
                "https://www.douyin.com:8443/a", "https://[::1]/a", "file:///C:/secret",
                "https://evil-douyin.com/a", "https://www.douyin.com\\@evil.example/a"]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ProviderError) as caught:
                validate_import_url(url)
            self.assertEqual(caught.exception.status, 422)

    async def test_manual_text_is_usable_but_never_claimed_platform_verified(self):
        with patch("manyou.providers.request_json", new_callable=AsyncMock) as network:
            result = await import_source(ImportRequest(url="https://www.douyin.com/video/1234567890123456789", text="周末看展，需提前预约。"))
            network.assert_not_called()
        self.assertEqual(result["sources"][0].content_status, "snippet")
        self.assertIn("未与平台原文核对", " ".join(result["warnings"]))

    async def test_shortlink_does_not_follow_redirect_to_private_network(self):
        with patch("manyou.providers.request_json", new_callable=AsyncMock) as network:
            result = await import_source(ImportRequest(url="https://xhslink.com/a/example"))
            network.assert_not_called()
        self.assertEqual(result["sources"], [])
        self.assertTrue(result["warnings"])

    async def test_future_weather_is_unknown_without_network_or_fabricated_values(self):
        start = date.today()+timedelta(days=100)
        req = WeatherRequest(destination="杭州", start_date=start, end_date=start+timedelta(days=2))
        with patch("manyou.providers.request_json", new_callable=AsyncMock) as network:
            result = await fetch_weather(req)
            network.assert_not_called()
        self.assertEqual(len(result["days"]), 3)
        self.assertTrue(all(w.status == "unknown" and w.temp_min is None and w.temp_max is None for w in result["days"]))

    async def test_partial_forecast_keeps_missing_day_unknown(self):
        today = date.today()
        req = WeatherRequest(destination="杭州", start_date=today, end_date=today+timedelta(days=1))
        responses = [{"results":[{"name":"杭州","latitude":30.25,"longitude":120.15,"timezone":"Asia/Shanghai"}]},
                     {"daily":{"time":[today.isoformat()],"temperature_2m_min":[20],"temperature_2m_max":[28],"weather_code":[2],"precipitation_probability_max":[30]}}]
        with patch("manyou.providers.request_json", new_callable=AsyncMock, side_effect=responses):
            result = await fetch_weather(req)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["days"][0].temp_max, 28)
        self.assertEqual(result["days"][1].status, "unknown")
        self.assertIsNone(result["days"][1].temp_max)


if __name__ == "__main__":
    unittest.main()

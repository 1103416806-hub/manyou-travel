import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from manyou.api import app


class ApiContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = dict(destination="杭州", origin="上海", start_date="2026-10-01",
                            end_date="2026-10-03", travelers=2, budget=3000, mode="demo")

    def test_demo_endpoint_is_explicit(self):
        result = self.client.get("/api/demo")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["mode"], "demo")

    def test_user_dates_and_party_survive_generation(self):
        result = self.client.post("/api/plan", json={**self.payload, "travelers":3})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["start_date"], "2026-10-01")
        self.assertEqual(result.json()["travelers"], 3)

    def test_live_without_keys_returns_error_and_no_itinerary(self):
        with patch.dict(os.environ, {}, clear=True):
            result = self.client.post("/api/plan", json={**self.payload, "mode":"live"})
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("days", result.json())
        self.assertIn("detail", result.json())

    def test_unconfigured_social_search_is_not_fake_success(self):
        for platform in ("xiaohongshu", "douyin"):
            with self.subTest(platform=platform), patch.dict(os.environ, {}, clear=True):
                result = self.client.post("/api/search", json={"destination":"杭州", "keyword":"攻略", "platform":platform})
            self.assertEqual(result.status_code, 503)

    def test_invalid_request_is_422(self):
        result = self.client.post("/api/plan", json={**self.payload, "end_date":"2026-09-30"})
        self.assertEqual(result.status_code, 422)

    def test_external_origin_cannot_trigger_generation(self):
        result = self.client.post("/api/plan", json=self.payload, headers={"Origin":"https://unrelated.example"})
        self.assertEqual(result.status_code, 403)

    def test_invalid_import_not_fetched(self):
        result = self.client.post("/api/import", json={"url":"https://127.0.0.1/private", "text":"内容"})
        self.assertEqual(result.status_code, 422)

    def test_future_weather_values_are_null(self):
        result = self.client.post("/api/weather", json={"destination":"杭州", "start_date":"2100-01-01", "end_date":"2100-01-03"})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(all(w["status"]=="unknown" and w["temp_max"] is None for w in result.json()["days"]))


if __name__ == "__main__":
    unittest.main()

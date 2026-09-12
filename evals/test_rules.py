"""Spec-driven synthetic regression; no assertions of live retrieval quality."""
import unittest
from datetime import date, timedelta

from pydantic import ValidationError

from manyou.demo import build_demo
from manyou.models import TripRequest, WeatherRequest, validate_plan


def request(**updates):
    values = dict(destination="杭州", origin="上海", start_date="2026-10-01",
                  end_date="2026-10-03", travelers=2, budget=3000, mode="demo")
    values.update(updates)
    return TripRequest(**values)


class ItineraryRules(unittest.TestCase):
    def test_all_supported_lengths_and_paces_have_consistent_schedule(self):
        for days in range(2, 6):
            for pace in ("relaxed", "balanced", "full"):
                with self.subTest(days=days, pace=pace):
                    req = request(end_date=(date(2026, 10, 1)+timedelta(days=days-1)).isoformat(), pace=pace)
                    plan = build_demo(req)
                    self.assertEqual(len(plan.days), days)
                    self.assertEqual(validate_plan(plan, req), [])

    def test_unsupported_city_not_silently_substituted(self):
        with self.assertRaises(ValidationError):
            request(destination="成都")

    def test_reversed_and_excessive_dates_rejected(self):
        for end in ("2026-09-30", "2026-10-01", "2026-10-06"):
            with self.subTest(end=end), self.assertRaises(ValidationError):
                request(end_date=end)

    def test_invalid_party_and_budget_rejected(self):
        for update in ({"travelers": 0}, {"travelers": 21}, {"budget": -1}):
            with self.subTest(update=update), self.assertRaises(ValidationError):
                request(**update)

    def test_pace_changes_number_of_stops(self):
        slow = build_demo(request(pace="relaxed"))
        full = build_demo(request(pace="full"))
        self.assertLess(len(slow.days[0].activities), len(full.days[0].activities))

    def test_demo_never_claims_live_provenance(self):
        plan = build_demo(request())
        self.assertEqual(plan.mode, "demo")
        self.assertTrue(all(s.content_status == "sample" for s in plan.sources))
        self.assertTrue(all(d.weather.status == "sample" for d in plan.days))
        self.assertFalse(any(a.verified for d in plan.days for a in d.activities))

    def test_low_budget_exposes_overrun(self):
        plan = build_demo(request(budget=100))
        self.assertGreater(sum(c.amount for c in plan.cost_breakdown), plan.budget)
        self.assertTrue(any("超过" in warning and "预算" in warning for warning in plan.warnings))

    def test_more_people_raise_estimated_cost(self):
        one = build_demo(request(travelers=1))
        three = build_demo(request(travelers=3))
        self.assertGreater(sum(c.amount for c in three.cost_breakdown), sum(c.amount for c in one.cost_breakdown))

    def test_unmet_special_request_is_visible(self):
        plan = build_demo(request(must_visit="灵隐寺", notes="带行动不便的老人"))
        self.assertTrue(any("灵隐寺" in warning for warning in plan.warnings))
        self.assertTrue(any("额外要求" in warning for warning in plan.warnings))

    def test_unknown_citation_rejected(self):
        req = request()
        plan = build_demo(req)
        plan.days[0].activities[0].source_ids = ["invented-source"]
        self.assertTrue(any("未知来源" in error for error in validate_plan(plan, req)))

    def test_overlap_rejected(self):
        req = request()
        plan = build_demo(req)
        plan.days[0].activities[1].time = "09:45"
        self.assertTrue(any("冲突" in error for error in validate_plan(plan, req)))

    def test_wrong_date_rejected(self):
        req = request()
        plan = build_demo(req)
        plan.days[0].date = "2026-10-02"
        self.assertTrue(any("日期" in error for error in validate_plan(plan, req)))

    def test_duplicate_activity_id_rejected(self):
        req = request()
        plan = build_demo(req)
        plan.days[1].activities[0].id = plan.days[0].activities[0].id
        self.assertTrue(any("ID 重复" in error for error in validate_plan(plan, req)))

    def test_invalid_weather_range_rejected(self):
        with self.assertRaises(ValidationError):
            WeatherRequest(destination="杭州", start_date="2026-10-02", end_date="2026-10-01")


if __name__ == "__main__":
    unittest.main()

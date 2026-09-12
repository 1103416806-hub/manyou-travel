from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TripRequest(StrictModel):
    destination: str = Field(min_length=1, max_length=80)
    origin: str = Field(default="", max_length=80)
    start_date: date
    end_date: date
    travelers: int = Field(default=2, ge=1, le=20)
    budget: float = Field(default=3000, ge=0, le=1000000)
    pace: Literal["relaxed", "balanced", "full"] = "balanced"
    interests: list[str] = Field(default_factory=list, max_length=12)
    must_visit: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=2000)
    mode: Literal["demo", "live"] = "demo"
    source_materials: list["Source"] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def valid_dates(self):
        if not 2 <= (self.end_date - self.start_date).days + 1 <= 5:
            raise ValueError("第一版支持连续 2–5 天，结束日期须晚于开始日期。")
        if self.mode == "demo" and self.destination.lower() not in {"杭州", "杭州市", "hangzhou"}:
            raise ValueError("离线示例仅支持杭州；其他目的地请配置数据源和模型后使用实时规划。")
        return self

    @property
    def dates(self) -> list[date]:
        return [self.start_date + timedelta(days=i) for i in range((self.end_date - self.start_date).days + 1)]


class Weather(StrictModel):
    date: str
    temp_min: float | None = None
    temp_max: float | None = None
    description: str
    precipitation_probability: float | None = Field(default=None, ge=0, le=100)
    source_url: str
    status: Literal["sample", "forecast", "unknown", "unavailable"]


class Source(StrictModel):
    id: str = Field(max_length=100)
    platform: Literal["xiaohongshu", "douyin", "official", "web", "sample"]
    title: str = Field(max_length=300)
    url: str = Field(max_length=2000)
    excerpt: str = Field(max_length=15000)
    content_status: Literal["full", "snippet", "sample", "unavailable"]
    published_at: str | None = None


class Activity(StrictModel):
    id: str
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    title: str = Field(min_length=1, max_length=200)
    category: Literal["attraction", "food", "transport", "stay"]
    description: str
    duration_minutes: int = Field(ge=1, le=1440)
    cost: float = Field(default=0, ge=0)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    source_ids: list[str] = Field(default_factory=list)
    verified: bool = False
    indoor: bool = False
    transport_note: str = "交通时间待地图核验。"


class Day(StrictModel):
    date: str
    title: str
    description: str
    weather: Weather | None = None
    activities: list[Activity] = Field(min_length=1, max_length=15)


class Cost(StrictModel):
    label: str
    amount: float = Field(ge=0)


class Trace(StrictModel):
    step: str
    status: str
    detail: str


class Plan(StrictModel):
    id: str
    title: str
    destination: str
    origin: str
    start_date: str
    end_date: str
    travelers: int
    budget: float
    mode: Literal["demo", "live", "limited"]
    summary: str
    days: list[Day]
    sources: list[Source]
    tips: list[str]
    warnings: list[str]
    cost_breakdown: list[Cost]
    trace: list[Trace]
    provider_status: dict


class PlanDraft(StrictModel):
    """模型只可提交安排，来源和提供商状态由程序控制。"""
    title: str
    summary: str
    days: list[Day] = Field(min_length=2, max_length=5)
    tips: list[str] = Field(default_factory=list)


class SearchRequest(StrictModel):
    destination: str = Field(min_length=1, max_length=80)
    keyword: str = Field(default="旅游攻略", max_length=120)
    platform: Literal["all", "xiaohongshu", "douyin", "web"] = "all"


class WeatherRequest(StrictModel):
    destination: str = Field(min_length=1, max_length=80)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def valid_dates(self):
        if not 0 <= (self.end_date - self.start_date).days <= 15:
            raise ValueError("天气查询日期顺序错误，或超过 16 天。")
        return self


class ImportRequest(StrictModel):
    url: str = Field(min_length=1, max_length=2000)
    text: str = Field(default="", max_length=15000)


TripRequest.model_rebuild()


def minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def validate_plan(plan: Plan, request: TripRequest) -> list[str]:
    """确定性结构校验；不把结构通过误标为事实已核实。"""
    problems = []
    expected = [d.isoformat() for d in request.dates]
    if (plan.start_date,plan.end_date,plan.travelers,plan.budget) != (request.start_date.isoformat(),request.end_date.isoformat(),request.travelers,request.budget):
        problems.append("行程日期、人数或预算与请求不一致。")
    if [d.date for d in plan.days] != expected:
        problems.append("行程天数或日期与请求不一致。")
    valid_sources = {s.id for s in plan.sources}
    ids = set()
    for day in plan.days:
        if day.weather and day.weather.date != day.date:
            problems.append(f"{day.date} 的天气日期与行程不一致。")
        if sum(a.category == "attraction" for a in day.activities) > {"relaxed":2,"balanced":3,"full":4}[request.pace]:
            problems.append(f"{day.date} 的游览地点超过所选节奏。")
        previous_end = -1
        for activity in day.activities:
            start, end = minutes(activity.time), minutes(activity.end_time)
            if end <= start or end - start != activity.duration_minutes:
                problems.append(f"{day.date} {activity.title} 的时长与时间段不一致。")
            if start < previous_end:
                problems.append(f"{day.date} {activity.title} 与上一项时间冲突。")
            previous_end = end
            if not set(activity.source_ids).issubset(valid_sources):
                problems.append(f"{activity.title} 使用了未知来源。")
            if activity.id in ids:
                problems.append("活动 ID 重复。")
            ids.add(activity.id)
    return problems

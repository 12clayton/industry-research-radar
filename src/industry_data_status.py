"""Read-only V5.3 data status summaries for the research page."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.industry_catalyst_snapshot import read_dynamic_catalyst_snapshot


STATUS_ZH = {
    "available": "可用",
    "no_recent_news": "暂无近期新闻",
    "fetch_failed": "获取失败",
    "not_configured": "未配置",
    "no_market_mapping": "无市场映射",
    "market_data_failed": "市场数据失败",
    "insufficient_data": "数据不足",
    "reinforced": "强化",
    "stable": "待验证",
    "diverging": "分化",
    "weakening": "降温",
    "insufficient_evidence": "待验证",
    "high": "高",
    "medium": "中",
    "low": "低",
    "insufficient": "低",
}


def build_industry_data_status(
    *,
    industry: dict[str, Any],
    market_result: dict[str, Any] | None,
    live_news: dict[str, Any] | None,
    catalyst: dict[str, Any] | None,
    local_summary_generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a read-only data status package without changing V5.1/V5.2 logic."""

    industry_id = str(industry.get("id") or "")
    market_result = market_result or {}
    live_news = live_news or {}
    catalyst = catalyst or {}
    snapshot = read_dynamic_catalyst_snapshot(industry_id) or {}
    generated_at = local_summary_generated_at or datetime.now()
    high_relevance_count = _count_news_by_relevance(live_news, "high")
    low_relevance_count = _to_int(live_news.get("low_relevance_count"))
    freshness_label, freshness_warning = _freshness_label(
        market_available=bool(market_result.get("available")),
        news_status=str(live_news.get("live_news_status") or live_news.get("fetch_status") or ""),
        latest_news_time=live_news.get("latest_news_time"),
        snapshot_updated_at=snapshot.get("snapshot_generated_at"),
        live_news_count_7d=_to_int(live_news.get("live_news_count_7d")),
    )

    return {
        "industry_id": industry_id,
        "industry_name_zh": str(industry.get("nameZh") or industry.get("name") or industry_id),
        "local_summary_generated_at": generated_at.isoformat(timespec="seconds"),
        "market_data_status": _market_status(market_result),
        "market_price_score": market_result.get("score") if market_result.get("available") else None,
        "market_available": bool(market_result.get("available")),
        "news_status": live_news.get("live_news_status") or live_news.get("fetch_status") or "",
        "latest_news_time": live_news.get("latest_news_time") or "",
        "live_news_count_7d": _to_int(live_news.get("live_news_count_7d")),
        "high_relevance_news_count": high_relevance_count,
        "low_relevance_news_count": low_relevance_count,
        "framework_is_override": bool(catalyst.get("is_override")),
        "framework_updated_at": catalyst.get("updated_at") or "",
        "catalyst_snapshot_updated_at": snapshot.get("snapshot_generated_at") or "",
        "catalyst_dynamic_status": snapshot.get("review_status") or "",
        "catalyst_evidence_strength": snapshot.get("evidence_level") or "",
        "data_freshness_label": freshness_label,
        "data_freshness_warning": freshness_warning,
    }


def data_status_display_rows(status: dict[str, Any]) -> list[tuple[str, str]]:
    """Return Chinese display rows for the V5.3 research data status bar."""

    return [
        ("本地摘要生成时间", format_datetime_compact(status.get("local_summary_generated_at"))),
        ("市场价格", _status_label(status.get("market_data_status"))),
        ("市场评分", _format_score(status.get("market_price_score"))),
        ("新闻缓存", _status_label(status.get("news_status"))),
        ("最新新闻", format_datetime_compact(status.get("latest_news_time"))),
        ("7天相关新闻数", str(status.get("live_news_count_7d") or 0)),
        ("高相关新闻数", str(status.get("high_relevance_news_count") or 0)),
        ("低相关新闻数", str(status.get("low_relevance_news_count") or 0)),
        ("催化快照", format_datetime_compact(status.get("catalyst_snapshot_updated_at"))),
        ("催化状态", _status_label(status.get("catalyst_dynamic_status"))),
        ("证据强度", _status_label(status.get("catalyst_evidence_strength"))),
        ("使用更新后框架", "是" if status.get("framework_is_override") else "否"),
        ("框架更新时间", format_datetime_compact(status.get("framework_updated_at"))),
        ("数据状态", str(status.get("data_freshness_label") or "缺失")),
    ]


def format_datetime_compact(value: object) -> str:
    """Format ISO-like timestamps for compact Chinese UI display."""

    raw = str(value or "").strip()
    if not raw:
        return "暂无"
    parsed = _parse_datetime(raw)
    if not parsed:
        return raw[:16]
    return parsed.strftime("%Y-%m-%d %H:%M")


def _market_status(market_result: dict[str, Any]) -> str:
    if market_result.get("available"):
        return "available"
    return str(market_result.get("reason_code") or "insufficient_data")


def _freshness_label(
    *,
    market_available: bool,
    news_status: str,
    latest_news_time: object,
    snapshot_updated_at: object,
    live_news_count_7d: int,
) -> tuple[str, str]:
    latest_news = _parse_datetime(latest_news_time)
    snapshot_time = _parse_datetime(snapshot_updated_at)
    now = datetime.now(latest_news.tzinfo if latest_news and latest_news.tzinfo else None)

    missing_major_data = not market_available and news_status not in {"available", "no_recent_news"} and not snapshot_time
    if missing_major_data:
        return "缺失", "部分关键数据缺失；当前摘要只能作为本地框架预读，需先补充或刷新数据后再复核。"

    stale_news = False
    if news_status != "available" or live_news_count_7d <= 0:
        stale_news = True
    elif latest_news:
        stale_news = (now - latest_news.replace(tzinfo=now.tzinfo) if latest_news.tzinfo is None else now - latest_news).days >= 3

    if stale_news or not snapshot_time:
        return "需刷新", "新闻缓存或催化快照可能不够新；建议先在单行业页面刷新新闻并生成催化快照，再回到本页查看摘要。"

    return "较新", "当前摘要基于缓存新闻和本地规则生成，最终判断仍需人工复核。"


def _count_news_by_relevance(live_news: dict[str, Any], relevance: str) -> int:
    items = live_news.get("items") if isinstance(live_news.get("items"), list) else []
    return sum(1 for item in items if isinstance(item, dict) and item.get("relevance", "high") == relevance)


def _status_label(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "暂无"
    return STATUS_ZH.get(raw, raw)


def _format_score(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.1f}"
    return "暂无"


def _parse_datetime(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is timezone.utc:
        return parsed.astimezone().replace(tzinfo=None)
    return parsed


def _to_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0

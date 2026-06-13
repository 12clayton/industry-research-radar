"""Build V5.2 AI research input prompts without calling any AI API."""

from __future__ import annotations

from datetime import date
from typing import Any


def build_ai_research_prompt(
    *,
    summary: dict[str, Any],
    live_news: dict[str, Any] | None,
    lang: str = "zh",
    prompt_date: date | None = None,
) -> str:
    """Return a Markdown prompt package for manual ChatGPT research review."""

    live_news = live_news or {}
    prompt_date = prompt_date or date.today()
    if lang == "en":
        return _build_english_prompt(summary, live_news, prompt_date)
    return _build_chinese_prompt(summary, live_news, prompt_date)


def build_ai_research_prompt_filename(industry_id: str, prompt_date: date | None = None) -> str:
    """Return a stable Markdown download filename for the V5.2 prompt."""

    safe_industry_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in industry_id)
    safe_industry_id = safe_industry_id.strip("_") or "industry"
    prompt_date = prompt_date or date.today()
    return f"ai_research_prompt_{safe_industry_id}_{prompt_date.isoformat()}.md"


def _build_chinese_prompt(summary: dict[str, Any], live_news: dict[str, Any], prompt_date: date) -> str:
    industry_name = _text(summary.get("industry_name") or summary.get("industry_id"))
    update = _dict(summary.get("suggest_framework_update"))
    evidence = _dict(summary.get("evidence"))
    trend_health = _dict(summary.get("trend_health"))
    resonance = _dict(summary.get("price_news_resonance"))
    news_items = _news_items(live_news)

    lines = [
        f"# AI 研究输入包：{industry_name}",
        "",
        "## 使用说明",
        "请基于以下结构化材料进行研究复核。不要直接给买卖建议，不要输出交易指令，不要把材料解释为确定性预测。",
        "请优先区分：已由本地规则确认的事实、需要外部验证的信息、以及你基于材料做出的推理。",
        "",
        "## 行业与日期",
        f"- 行业名称：{industry_name}",
        f"- 行业 ID：{_text(summary.get('industry_id'))}",
        f"- Prompt 生成日期：{prompt_date.isoformat()}",
        "",
        "## V5.1 本地研究摘要",
        f"- 趋势健康度：{_label_with_score(trend_health)}",
        f"- 健康度解读：{_text(trend_health.get('note'))}",
        f"- 价格与新闻是否共振：{_label_with_score(resonance)}",
        f"- 共振解读：{_text(resonance.get('note'))}",
        "",
        "## 当前催化主线",
        *_bullet_lines(_split_mainline(summary.get("current_catalyst_mainline"))),
        "",
        "## 高相关新闻摘要",
        *_news_lines(news_items, empty="暂无高相关新闻缓存。"),
        "",
        "## 风险信号",
        *_bullet_lines(summary.get("risk_signals") or [], empty="暂无。"),
        "",
        "## 待验证问题",
        *_bullet_lines(summary.get("pending_questions") or [], empty="暂无。"),
        "",
        "## 人工复核建议",
        f"- 是否建议人工复核：{'是' if update.get('recommended') else '否'}",
        f"- 复核理由：{_text(update.get('reason'))}",
        "",
        "## 数据来源说明",
        "- 本输入包来自本地 V5.1 规则摘要、行业趋势框架、市场价格确认数据、催化框架和缓存新闻证据。",
        f"- 本地证据：{_format_mapping(evidence)}",
        f"- 新闻来源：{_format_list(live_news.get('source_names') or live_news.get('source') or [])}",
        f"- 新闻状态：{_text(live_news.get('live_news_status') or live_news.get('fetch_status'))}",
        "- 当前 V5.2 不接 API，不调用 OpenAI，不读取 API key，不自动生成结论。",
        "",
        "## 请 ChatGPT 输出",
        "请按以下结构输出，保持研究复核口吻：",
        "1. 核心结论",
        "2. 支撑证据",
        "3. 反方证据",
        "4. 关键风险",
        "5. 下一步验证清单",
        "6. 哪些信息还缺",
        "7. 是否值得人工深入研究",
        "8. 置信度",
        "9. 免责声明：供研究复核，不构成投资建议。",
    ]
    return "\n".join(lines).strip() + "\n"


def _build_english_prompt(summary: dict[str, Any], live_news: dict[str, Any], prompt_date: date) -> str:
    industry_name = _text(summary.get("industry_name") or summary.get("industry_id"))
    update = _dict(summary.get("suggest_framework_update"))
    evidence = _dict(summary.get("evidence"))
    trend_health = _dict(summary.get("trend_health"))
    resonance = _dict(summary.get("price_news_resonance"))
    news_items = _news_items(live_news)

    lines = [
        f"# AI Research Input Package: {industry_name}",
        "",
        "## Instructions",
        "Use the structured material below for research review. Do not give direct buy/sell advice, do not output trading instructions, and do not treat the material as a deterministic forecast.",
        "Separate local rule-based facts, externally verifiable information, and your own inference.",
        "",
        "## Industry and Date",
        f"- Industry name: {industry_name}",
        f"- Industry ID: {_text(summary.get('industry_id'))}",
        f"- Prompt date: {prompt_date.isoformat()}",
        "",
        "## V5.1 Local Research Summary",
        f"- Trend health: {_label_with_score(trend_health)}",
        f"- Health read: {_text(trend_health.get('note'))}",
        f"- Price-news resonance: {_label_with_score(resonance)}",
        f"- Resonance read: {_text(resonance.get('note'))}",
        "",
        "## Current Catalyst Mainline",
        *_bullet_lines(_split_mainline(summary.get("current_catalyst_mainline"))),
        "",
        "## High-Relevance News Summary",
        *_news_lines(news_items, empty="No high-relevance cached news."),
        "",
        "## Risk Signals",
        *_bullet_lines(summary.get("risk_signals") or [], empty="None."),
        "",
        "## Pending Validation Questions",
        *_bullet_lines(summary.get("pending_questions") or [], empty="None."),
        "",
        "## Manual Review Suggestion",
        f"- Manual review suggested: {'Yes' if update.get('recommended') else 'No'}",
        f"- Reason: {_text(update.get('reason'))}",
        "",
        "## Data Source Notes",
        "- This package uses the local V5.1 rule-based summary, industry trend framework, market price confirmation, catalyst framework, and cached news evidence.",
        f"- Local evidence: {_format_mapping(evidence)}",
        f"- News sources: {_format_list(live_news.get('source_names') or live_news.get('source') or [])}",
        f"- News status: {_text(live_news.get('live_news_status') or live_news.get('fetch_status'))}",
        "- V5.2 currently does not connect to any API, call OpenAI, read API keys, or auto-generate conclusions.",
        "",
        "## Required ChatGPT Output",
        "Please respond in this structure:",
        "1. Core conclusion",
        "2. Supporting evidence",
        "3. Opposing evidence",
        "4. Key risks",
        "5. Next validation checklist",
        "6. Missing information",
        "7. Whether this deserves deeper human research",
        "8. Confidence level",
        "9. Disclaimer: for research review only, not investment advice.",
    ]
    return "\n".join(lines).strip() + "\n"


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: object, fallback: str = "N/A") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _label_with_score(payload: dict[str, Any]) -> str:
    label = _text(payload.get("label_zh") or payload.get("label"))
    score = payload.get("score")
    if isinstance(score, (int, float)):
        return f"{label} ({score:.1f})"
    return label


def _split_mainline(value: object) -> list[str]:
    text = _text(value, "")
    if not text:
        return []
    primary = text.split("|", maxsplit=1)[0]
    delimiter = "->" if "->" in primary else "、"
    return [part.strip() for part in primary.split(delimiter) if part.strip()]


def _bullet_lines(items: object, empty: str = "N/A") -> list[str]:
    values = [str(item).strip() for item in items if str(item).strip()] if isinstance(items, list) else []
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def _news_items(live_news: dict[str, Any]) -> list[dict[str, Any]]:
    items = live_news.get("items") if isinstance(live_news.get("items"), list) else []
    return [
        item
        for item in items
        if isinstance(item, dict) and item.get("relevance", "high") in {"high", "medium"}
    ][:5]


def _news_lines(items: list[dict[str, Any]], empty: str) -> list[str]:
    if not items:
        return [f"- {empty}"]
    lines = []
    for item in items:
        title = _text(item.get("title"))
        publisher = _text(item.get("publisher"), "")
        published_at = _text(item.get("published_at"), "")
        relevance = _text(item.get("relevance"), "")
        reason = _text(item.get("relevance_reason"), "")
        suffix = " | ".join(part for part in [publisher, published_at, relevance, reason] if part)
        lines.append(f"- {title}" + (f" ({suffix})" if suffix else ""))
    return lines


def _format_mapping(value: dict[str, Any]) -> str:
    if not value:
        return "N/A"
    return "; ".join(f"{key}={_text(item)}" for key, item in value.items())


def _format_list(value: object) -> str:
    if isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(values) if values else "N/A"
    return _text(value)

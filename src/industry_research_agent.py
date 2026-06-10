"""Local V5.1 rule-based research summaries.

The research agent is intentionally deterministic. It reads the existing
industry framework, market confirmation, catalyst framework, and cached news
watch data, then produces a compact research summary without calling any LLM
or mutating catalyst frameworks.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.industry_catalyst_framework_store import get_effective_catalyst_framework
from src.industry_market_data import get_market_confirmation_data
from src.industry_news_provider import read_industry_news
from src.industry_trend_search import find_industry_trend


CORE_RESEARCH_INDUSTRIES = {
    "semiconductor",
    "memory",
    "cpo_optical_module",
    "ai_compute",
    "gold",
    "sic",
}

RESEARCH_AGENT_TEXT = {
    "zh": {
        "view_title": "V5.1 Research Agent 本地规则版",
        "view_subtitle": "基于现有行业框架、价格确认、催化框架和缓存新闻做规则汇总；不接 OpenAI API，不给交易指令，不自动修改行业框架。",
        "search_placeholder": "输入核心行业或主题...",
        "coverage": "覆盖范围",
        "covered": "已覆盖核心行业",
        "not_covered": "V5.1 第一版暂只覆盖核心行业；当前行业仍可查看原有趋势页。",
        "trend_health": "趋势健康度",
        "price_news_resonance": "价格与新闻是否共振",
        "current_catalyst_mainline": "当前催化主线",
        "risk_signals": "风险信号",
        "pending_questions": "待验证问题",
        "framework_update": "是否建议更新行业框架",
        "update_yes": "建议更新",
        "update_no": "暂不建议更新",
        "reason": "理由",
        "evidence": "本地证据",
        "none": "暂无",
    },
    "en": {
        "view_title": "V5.1 Research Agent (Local Rules)",
        "view_subtitle": "Rule-based summary from the existing framework, price confirmation, catalyst framework, and cached news. No OpenAI API, no trading instructions, no automatic framework edits.",
        "search_placeholder": "Search core industry or theme...",
        "coverage": "Coverage",
        "covered": "Covered core industry",
        "not_covered": "V5.1 first version only covers core industries. Use the existing trend page for this industry.",
        "trend_health": "Trend Health",
        "price_news_resonance": "Price-News Resonance",
        "current_catalyst_mainline": "Current Catalyst Mainline",
        "risk_signals": "Risk Signals",
        "pending_questions": "Pending Questions",
        "framework_update": "Suggested Framework Update",
        "update_yes": "Update suggested",
        "update_no": "No update suggested",
        "reason": "Reason",
        "evidence": "Local Evidence",
        "none": "None",
    },
}

INDUSTRY_PENDING_QUESTIONS = {
    "semiconductor": [
        "Can AI chip, HBM, foundry, and equipment signals remain aligned instead of splitting further?",
        "Does cloud capex translate into broad supply-chain orders rather than only leader performance?",
    ],
    "memory": [
        "Are HBM strength and DRAM / NAND pricing moving together or separating by product tier?",
        "Is supplier capex discipline still supportive for the next pricing cycle?",
    ],
    "cpo_optical_module": [
        "Are 800G / 1.6T upgrades translating into broad module demand rather than isolated leader strength?",
        "Is CPO / silicon photonics validation improving at the product-route level?",
    ],
    "ai_compute": [
        "Is AI infrastructure capex still expanding beyond GPU leaders into servers, networking, power, and cooling?",
        "Can utilization and revenue validation keep pace with high market attention?",
    ],
    "gold": [
        "Are real-rate, dollar, and central-bank demand signals pointing in the same direction?",
        "Is gold price strength supported by macro hedging demand rather than only short-term risk-off flow?",
    ],
    "sic": [
        "Is SiC demand improving in EV inverters and power electronics despite auto-cycle pressure?",
        "Are pricing and utilization signals stabilizing after capacity expansion?",
    ],
}


def build_research_summary(
    industry: dict[str, Any],
    market_result: dict[str, Any] | None,
    catalyst: dict[str, Any] | None,
    live_news: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a local V5.1 research summary for one industry."""

    industry_id = str(industry.get("id") or "")
    covered = industry_id in CORE_RESEARCH_INDUSTRIES
    market_result = market_result or {}
    catalyst = catalyst or {}
    live_news = live_news or {}
    price_score = _market_price_score(industry, market_result)
    heat_score = _to_float(catalyst.get("heat_score"))
    trend_score = _to_float(industry.get("trendScore"))
    validation = _to_float(industry.get("fundamentalValidation"))
    valuation = _to_float(industry.get("valuationPressure"))
    live_news_count = _to_int(live_news.get("live_news_count_7d"))

    health = _trend_health(
        trend_score=trend_score,
        price_score=price_score,
        heat_score=heat_score,
        validation=validation,
        valuation=valuation,
        covered=covered,
    )
    resonance = _price_news_resonance(
        price_score=price_score,
        heat_score=heat_score,
        live_news_count=live_news_count,
        market_available=bool(market_result.get("available")),
        news_status=str(live_news.get("live_news_status") or live_news.get("fetch_status") or ""),
        covered=covered,
    )
    risks = _risk_signals(industry, market_result, live_news, valuation, covered)
    questions = _pending_questions(industry_id, market_result, live_news, resonance["status"], covered)
    update = _framework_update_judgement(
        industry_id=industry_id,
        catalyst=catalyst,
        live_news=live_news,
        resonance_status=resonance["status"],
        covered=covered,
    )

    return {
        "industry_id": industry_id,
        "industry_name": industry.get("name") or industry_id,
        "covered": covered,
        "trend_health": health,
        "price_news_resonance": resonance,
        "current_catalyst_mainline": _current_catalyst_mainline(industry, catalyst, covered),
        "risk_signals": risks,
        "pending_questions": questions,
        "suggest_framework_update": update,
        "evidence": {
            "trend_score": trend_score,
            "price_score": price_score,
            "heat_score": heat_score,
            "live_news_count_7d": live_news_count,
            "market_available": bool(market_result.get("available")),
            "news_status": live_news.get("live_news_status") or live_news.get("fetch_status") or "",
            "framework_is_override": bool(catalyst.get("is_override")),
        },
        "guardrails": {
            "openai_api_used": False,
            "trading_instruction": False,
            "auto_framework_update": False,
        },
    }


def render_research_agent_page(lang: str | None = None) -> None:
    """Render the lightweight V5.1 local research-agent view."""

    lang = lang or "zh"
    text = RESEARCH_AGENT_TEXT[lang]
    st.markdown(f"## {text['view_title']}")
    st.caption(text["view_subtitle"])

    query = st.text_input(
        text["search_placeholder"],
        value="Semiconductor",
        placeholder=text["search_placeholder"],
        label_visibility="collapsed",
        key="research_agent_query",
    )
    industry, matched = find_industry_trend(query)
    industry_id = str(industry.get("id") or "")
    st.caption(f"{text['coverage']}: {text['covered'] if industry_id in CORE_RESEARCH_INDUSTRIES else text['not_covered']}")
    if not matched:
        st.info(text["not_covered"])
        return

    market_result = get_market_confirmation_data(industry_id)
    catalyst = get_effective_catalyst_framework(industry_id)
    live_news = read_industry_news(industry_id)
    summary = build_research_summary(industry, market_result, catalyst, live_news)
    if not summary["covered"]:
        st.info(text["not_covered"])
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(text["trend_health"], _localized_value(summary["trend_health"], lang))
    with c2:
        st.metric(text["price_news_resonance"], _localized_value(summary["price_news_resonance"], lang))
    with c3:
        update = summary["suggest_framework_update"]
        st.metric(text["framework_update"], text["update_yes"] if update["recommended"] else text["update_no"])

    st.markdown(f"**{text['current_catalyst_mainline']}**")
    st.write(summary["current_catalyst_mainline"] or text["none"])
    st.markdown(f"**{text['risk_signals']}**")
    st.write(summary["risk_signals"] or [text["none"]])
    st.markdown(f"**{text['pending_questions']}**")
    st.write(summary["pending_questions"] or [text["none"]])
    st.markdown(f"**{text['reason']}**")
    st.write(update["reason"])

    with st.expander(text["evidence"], expanded=False):
        st.dataframe(pd.DataFrame([summary["evidence"]]), width="stretch", hide_index=True)


def _trend_health(
    *,
    trend_score: float | None,
    price_score: float | None,
    heat_score: float | None,
    validation: float | None,
    valuation: float | None,
    covered: bool,
) -> dict[str, Any]:
    if not covered:
        return {"status": "not_covered", "label": "Not covered", "label_zh": "暂未覆盖", "score": None}
    values = [value for value in [trend_score, price_score, heat_score, validation] if value is not None]
    if len(values) < 3:
        return {"status": "insufficient_data", "label": "Insufficient data", "label_zh": "数据不足", "score": None}
    score = sum(values) / len(values)
    if valuation is not None and valuation >= 7.5:
        score -= 0.5
    score = round(max(0.0, min(10.0, score)), 1)
    if score >= 7.0:
        status, label, label_zh = "healthy", "Healthy / supported", "健康 / 有支撑"
    elif score >= 5.5:
        status, label, label_zh = "watch", "Watch / mixed", "观察 / 分化"
    else:
        status, label, label_zh = "weak", "Weak / needs validation", "偏弱 / 待验证"
    return {"status": status, "label": label, "label_zh": label_zh, "score": score}


def _price_news_resonance(
    *,
    price_score: float | None,
    heat_score: float | None,
    live_news_count: int,
    market_available: bool,
    news_status: str,
    covered: bool,
) -> dict[str, str]:
    if not covered:
        return {"status": "not_covered", "label": "Not covered", "label_zh": "暂未覆盖"}
    if price_score is None or heat_score is None:
        return {"status": "insufficient_data", "label": "Insufficient data", "label_zh": "数据不足"}
    if price_score >= 6.5 and heat_score >= 6.5:
        return {"status": "aligned", "label": "Aligned", "label_zh": "形成共振"}
    if heat_score >= 7.0 and price_score < 5.0:
        return {"status": "news_leads_price", "label": "News heat leads price", "label_zh": "新闻热度领先价格"}
    if price_score >= 6.0 and live_news_count == 0 and news_status != "available":
        return {"status": "price_leads_news", "label": "Price leads cached news", "label_zh": "价格领先缓存新闻"}
    if not market_available and heat_score >= 6.5:
        return {"status": "news_only", "label": "News / framework only", "label_zh": "仅新闻或框架线索"}
    return {"status": "mixed", "label": "Mixed", "label_zh": "分化"}


def _current_catalyst_mainline(industry: dict[str, Any], catalyst: dict[str, Any], covered: bool) -> str:
    if not covered:
        return ""
    summary = str(catalyst.get("summary") or industry.get("summary") or industry.get("overview") or "")
    event_titles = [
        str(event.get("title") or "")
        for event in (catalyst.get("events") or [])[:2]
        if isinstance(event, dict) and event.get("title")
    ]
    drivers = [
        str(driver.get("name") or "")
        for driver in (industry.get("keyDrivers") or [])[:2]
        if isinstance(driver, dict) and driver.get("name")
    ]
    parts = [summary, *event_titles, *drivers]
    return " | ".join(part for part in parts if part)[:700]


def _risk_signals(
    industry: dict[str, Any],
    market_result: dict[str, Any],
    live_news: dict[str, Any],
    valuation: float | None,
    covered: bool,
) -> list[str]:
    if not covered:
        return []
    risks = [str(item) for item in industry.get("riskSignals", []) if item]
    price_score = _market_price_score(industry, market_result)
    ma50 = _to_float(market_result.get("above_ma50_ratio"))
    if price_score is not None and price_score < 4.5:
        risks.append("Market-price confirmation is weak relative to the framework.")
    if ma50 is not None and ma50 < 0.35:
        risks.append("Representative ticker breadth is weak below MA50.")
    if valuation is not None and valuation >= 7.0:
        risks.append("Valuation / expectation pressure is elevated.")
    if _to_int(live_news.get("live_news_count_7d")) == 0:
        risks.append("Cached high-relevance news evidence is limited.")
    return _unique(risks)[:6]


def _pending_questions(
    industry_id: str,
    market_result: dict[str, Any],
    live_news: dict[str, Any],
    resonance_status: str,
    covered: bool,
) -> list[str]:
    if not covered:
        return []
    questions = list(INDUSTRY_PENDING_QUESTIONS.get(industry_id, []))
    if not market_result.get("available"):
        questions.append("Can price confirmation be rechecked after market data becomes available?")
    if _to_int(live_news.get("live_news_count_7d")) == 0:
        questions.append("Do external news sources confirm the current catalyst line beyond the local framework?")
    if resonance_status in {"news_leads_price", "mixed", "news_only"}:
        questions.append("Will price breadth and relative strength catch up with the catalyst narrative?")
    return _unique(questions)[:5]


def _framework_update_judgement(
    *,
    industry_id: str,
    catalyst: dict[str, Any],
    live_news: dict[str, Any],
    resonance_status: str,
    covered: bool,
) -> dict[str, Any]:
    if not covered:
        return {"recommended": False, "reason": "V5.1 first version does not cover this industry."}
    live_news_count = _to_int(live_news.get("live_news_count_7d"))
    heat_direction = str(catalyst.get("heat_direction") or "")
    event_count = len(catalyst.get("events") or [])
    if live_news_count >= 3 and heat_direction == "Rising" and resonance_status in {"aligned", "news_leads_price"}:
        return {
            "recommended": True,
            "reason": "Cached news evidence, rising catalyst heat, and price/news alignment suggest the framework should be reviewed for a possible update. The agent does not apply the update automatically.",
        }
    if event_count < 2:
        return {
            "recommended": True,
            "reason": "The local catalyst framework has too few events for this core industry, so a manual framework review is suggested. The agent does not apply the update automatically.",
        }
    return {
        "recommended": False,
        "reason": f"{industry_id} already has a usable local catalyst framework; current evidence is not strong enough for an automatic framework change.",
    }


def _market_price_score(industry: dict[str, Any], market_result: dict[str, Any]) -> float | None:
    if market_result.get("available"):
        return _to_float(market_result.get("score"))
    return _to_float(industry.get("marketConfirmation"))


def _localized_value(payload: dict[str, Any], lang: str) -> str:
    label = payload.get("label_zh") if lang == "zh" else payload.get("label")
    score = payload.get("score")
    return f"{label} ({score:.1f})" if isinstance(score, float) else str(label or "")


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _unique(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        clean = value.strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        output.append(clean)
    return output

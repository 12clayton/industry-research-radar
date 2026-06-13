"""Local V5.1.1 rule-based research summaries.

The research agent is intentionally deterministic. It reads the existing
industry framework, market confirmation, catalyst framework, and cached news
watch data, then produces a compact research summary without calling any LLM,
issuing trading instructions, or mutating catalyst frameworks.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.industry_ai_prompt_builder import build_ai_research_prompt, build_ai_research_prompt_filename
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

INDUSTRY_LABELS = {
    "semiconductor": {"en": "Semiconductor", "zh": "半导体"},
    "memory": {"en": "Memory", "zh": "存储"},
    "cpo_optical_module": {"en": "CPO / Optical Module", "zh": "CPO / 光模块"},
    "ai_compute": {"en": "AI Compute", "zh": "AI 算力"},
    "gold": {"en": "Gold", "zh": "黄金"},
    "sic": {"en": "SiC", "zh": "碳化硅"},
}

RESEARCH_AGENT_TEXT = {
    "zh": {
        "view_title": "V5.1 本地研究摘要 / V5.2 AI 研究备忘录",
        "view_subtitle": "V5.1 是本地规则版研究摘要生成器，用于输出系统初判；V5.2 将作为未来接入大模型的 AI 研究备忘录。",
        "local_section_title": "V5.1 本地研究摘要",
        "local_section_note": "该模块为本地规则版研究摘要生成器，基于趋势评分、价格确认、催化热度、缓存新闻和行业框架生成系统初判；不接入大模型，不构成投资建议，最终结论需要人工复核。",
        "ai_section_title": "V5.2 AI 研究备忘录",
        "ai_disabled": "AI 研究备忘录暂未启用。后续将基于 V5.1 本地摘要、高相关新闻、催化主题、风险信号和待验证问题生成供人工复核的研究备忘录。",
        "ai_placeholder_note": "当前阶段不接 API、不读取 API key、不生成真实模型输出。",
        "ai_placeholder_value": "暂未启用",
        "ai_memo_fields": [
            "核心结论",
            "支撑证据",
            "反方证据",
            "关键风险",
            "下一步验证清单",
            "变化点",
            "人工复核建议",
            "置信度",
            "免责声明",
        ],
        "industry_selector": "\u9009\u62e9\u6838\u5fc3\u884c\u4e1a",
        "search_placeholder": "\u9009\u62e9\u6838\u5fc3\u884c\u4e1a...",
        "coverage": "\u8986\u76d6\u8303\u56f4",
        "covered": "\u5df2\u8986\u76d6\u6838\u5fc3\u884c\u4e1a",
        "not_covered": "V5.1.1 \u6682\u53ea\u8986\u76d6\u6838\u5fc3\u884c\u4e1a\uff1b\u5f53\u524d\u884c\u4e1a\u4ecd\u53ef\u67e5\u770b\u539f\u6709\u8d8b\u52bf\u9875\u3002",
        "trend_health": "\u8d8b\u52bf\u5065\u5eb7\u5ea6",
        "price_news_resonance": "\u4ef7\u683c\u4e0e\u65b0\u95fb\u662f\u5426\u5171\u632f",
        "current_catalyst_mainline": "\u5f53\u524d\u50ac\u5316\u4e3b\u7ebf",
        "risk_signals": "\u98ce\u9669\u4fe1\u53f7",
        "pending_questions": "\u5f85\u9a8c\u8bc1\u95ee\u9898",
        "framework_update": "人工复核建议",
        "update_yes": "\u5efa\u8bae\u4eba\u5de5\u590d\u6838",
        "update_no": "\u6682\u4e0d\u5efa\u8bae\u66f4\u65b0",
        "health_note": "\u5065\u5eb7\u5ea6\u89e3\u8bfb",
        "resonance_note": "\u5171\u632f\u89e3\u8bfb",
        "reason": "人工复核理由",
        "evidence": "\u672c\u5730\u8bc1\u636e",
        "none": "\u6682\u65e0",
    },
    "en": {
        "view_title": "V5.1 Local Research Summary / V5.2 AI Research Memo",
        "view_subtitle": "V5.1 is a local rule-based summary for system pre-read. V5.2 is reserved for a future AI research memo.",
        "local_section_title": "V5.1 Local Research Summary",
        "local_section_note": "This module is a local rule-based research-summary generator. It uses trend scores, price confirmation, catalyst heat, cached news, and the industry framework to produce a system pre-read. It does not call an LLM, is not investment advice, and requires human review.",
        "ai_section_title": "V5.2 AI Research Memo",
        "ai_disabled": "AI research memo is not enabled yet. A future version will use the V5.1 local summary, high-relevance news, catalyst themes, risk signals, and validation questions to generate a memo for human review.",
        "ai_placeholder_note": "This stage does not call any API, read any API key, or generate real model output.",
        "ai_placeholder_value": "Not enabled",
        "ai_memo_fields": [
            "Core View",
            "Supporting Evidence",
            "Opposing Evidence",
            "Key Risks",
            "Next Validation Checklist",
            "What Changed",
            "Manual Review Suggestion",
            "Confidence Level",
            "Disclaimer",
        ],
        "industry_selector": "Select core industry",
        "search_placeholder": "Search core industry or theme...",
        "coverage": "Coverage",
        "covered": "Covered core industry",
        "not_covered": "V5.1.1 only covers core industries. Use the existing trend page for this industry.",
        "trend_health": "Trend Health",
        "price_news_resonance": "Price-News Resonance",
        "current_catalyst_mainline": "Current Catalyst Mainline",
        "risk_signals": "Risk Signals",
        "pending_questions": "Pending Questions",
        "framework_update": "Manual Review Suggestion",
        "update_yes": "Manual review suggested",
        "update_no": "No update suggested",
        "health_note": "Health Read",
        "resonance_note": "Resonance Read",
        "reason": "Manual Review Reason",
        "evidence": "Local Evidence",
        "none": "None",
    },
}

RESEARCH_AGENT_TEXT["zh"].update(
    {
        "view_title": "V5.1 本地研究摘要 / V5.2 AI 研究输入包",
        "view_subtitle": "V5.1 是本地规则版研究摘要生成器，用于输出系统初判；V5.2 当前生成可复制给 ChatGPT 的 Markdown 研究输入包。",
        "ai_section_title": "V5.2 AI 研究输入包",
        "ai_disabled": "V5.2 当前为 AI 研究输入包生成器：系统会把本地摘要、价格确认、新闻证据、催化主线、风险信号和待验证问题整理成可复制给 ChatGPT 的 Prompt。当前不接 API，不自动生成结论。",
        "ai_prompt_button": "生成 ChatGPT 研究 Prompt",
        "ai_prompt_label": "ChatGPT 研究 Prompt / Markdown 输入包",
        "ai_download_label": "下载 Markdown",
    }
)
RESEARCH_AGENT_TEXT["en"].update(
    {
        "view_title": "V5.1 Local Research Summary / V5.2 AI Research Input Package",
        "view_subtitle": "V5.1 is a local rule-based summary. V5.2 now builds a Markdown prompt package for manual ChatGPT research review.",
        "ai_section_title": "V5.2 AI Research Input Package",
        "ai_disabled": "V5.2 is currently an AI research input package generator: it organizes the local summary, price confirmation, news evidence, catalyst mainline, risk signals, and validation questions into a prompt that can be copied to ChatGPT. It does not connect to an API or auto-generate conclusions.",
        "ai_prompt_button": "Generate ChatGPT Research Prompt",
        "ai_prompt_label": "ChatGPT Research Prompt / Markdown Input Package",
        "ai_download_label": "Download Markdown",
    }
)

RESONANCE_NOTE_ZH = {
    "aligned": "价格确认与催化热度均较强，并且有中高相关度缓存新闻作为证据支持。",
    "framework_price_aligned": "价格确认与催化热度方向一致，但缓存新闻证据有限。",
    "news_leads_price": "催化热度较强，但价格走势尚未充分确认。",
    "price_leads_news": "价格确认强于新闻确认。",
    "news_only": "催化框架信号较强，但市场价格确认暂不可完整验证。",
    "noisy_news": "缓存新闻噪音较多，高相关证据不足。",
    "mixed": "价格确认、催化热度与缓存新闻尚未形成同一方向的共振信号。",
}

INDUSTRY_RESEARCH_PROFILES = {
    "semiconductor": {
        "health_focus": "AI compute demand is still supportive, but the healthier read depends on whether HBM, advanced packaging, foundry, and equipment breadth move together.",
        "catalyst_mainline": "AI capex -> HBM / accelerator demand -> advanced packaging and equipment capacity -> broader chip-chain confirmation",
        "risk_overlays": [
            "Headline AI-chip strength may mask dispersion in foundry, equipment, and consumer-electronics demand.",
            "Export controls, capex timing, and inventory turns can quickly change the validation layer.",
        ],
        "questions": [
            "Can AI chip, HBM, foundry, and equipment signals remain aligned instead of splitting further?",
            "Does cloud capex translate into broad supply-chain orders rather than only leader performance?",
        ],
        "update_triggers": [
            "new HBM / advanced-packaging capacity signal",
            "cloud capex guidance change",
            "export-control or equipment-order change",
        ],
    },
    "memory": {
        "health_focus": "The key split is between high-end HBM demand and the broader DRAM / NAND cycle; trend quality improves only when pricing and inventory validation broaden.",
        "catalyst_mainline": "HBM qualification and capacity -> DRAM / NAND price cycle -> enterprise SSD demand -> supplier capex discipline",
        "risk_overlays": [
            "HBM strength can coexist with weaker commodity DRAM or NAND pricing.",
            "Rapid capacity expansion may turn a demand story into a later-cycle supply risk.",
        ],
        "questions": [
            "Are HBM strength and DRAM / NAND pricing moving together or separating by product tier?",
            "Is supplier capex discipline still supportive for the next pricing cycle?",
        ],
        "update_triggers": [
            "HBM qualification or allocation change",
            "DRAM / NAND price-cycle inflection",
            "memory supplier capex discipline change",
        ],
    },
    "cpo_optical_module": {
        "health_focus": "Trend quality depends on whether AI data-center bandwidth upgrades translate into product-route validation beyond a few optical leaders.",
        "catalyst_mainline": "AI cluster bandwidth pressure -> 800G / 1.6T optical module upgrades -> CPO / silicon photonics validation -> module vendor order breadth",
        "risk_overlays": [
            "Ticker strength can be driven by general AI/networking beta rather than optical-module evidence.",
            "CPO timing remains a product-route question; 800G / 1.6T demand does not automatically validate every architecture.",
        ],
        "questions": [
            "Are 800G / 1.6T upgrades translating into broad module demand rather than isolated leader strength?",
            "Is CPO / silicon photonics validation improving at the product-route level?",
        ],
        "update_triggers": [
            "800G / 1.6T order evidence",
            "CPO or silicon-photonics validation milestone",
            "module-vendor margin or capacity signal",
        ],
    },
    "ai_compute": {
        "health_focus": "The industry remains strongest when GPU, server, networking, power, cooling, and cloud capex indicators reinforce one another instead of concentrating in one leader group.",
        "catalyst_mainline": "cloud capex -> GPU / accelerator demand -> AI server and networking buildout -> power and cooling bottlenecks -> utilization validation",
        "risk_overlays": [
            "Capex enthusiasm can run ahead of utilization, revenue conversion, or power availability.",
            "Leadership concentration can make the theme look healthier than the full infrastructure chain.",
        ],
        "questions": [
            "Is AI infrastructure capex still expanding beyond GPU leaders into servers, networking, power, and cooling?",
            "Can utilization and revenue validation keep pace with high market attention?",
        ],
        "update_triggers": [
            "hyperscaler capex revision",
            "accelerator supply or networking bottleneck change",
            "power / cooling constraint evidence",
        ],
    },
    "gold": {
        "health_focus": "Gold is healthiest when price strength is confirmed by real-rate pressure, dollar weakness, central-bank demand, and defensive allocation rather than a single risk-off headline.",
        "catalyst_mainline": "real-rate expectations -> dollar and liquidity conditions -> central-bank demand -> geopolitical / inflation hedge demand",
        "risk_overlays": [
            "A stronger dollar or higher real yields can weaken the macro confirmation layer.",
            "Short-term risk-off flow may fade if central-bank demand or rate expectations do not confirm.",
        ],
        "questions": [
            "Are real-rate, dollar, and central-bank demand signals pointing in the same direction?",
            "Is gold price strength supported by macro hedging demand rather than only short-term risk-off flow?",
        ],
        "update_triggers": [
            "real-yield or dollar regime shift",
            "central-bank buying evidence",
            "geopolitical or inflation-hedge demand change",
        ],
    },
    "sic": {
        "health_focus": "SiC needs both power-semiconductor demand and end-market validation; EV-cycle pressure and pricing utilization are the main checks against the technology story.",
        "catalyst_mainline": "EV inverter and power-electronics demand -> SiC substrate / device capacity -> pricing and utilization stabilization -> industrial and energy applications",
        "risk_overlays": [
            "EV demand softness can offset the long-term power-semiconductor upgrade story.",
            "Capacity additions may pressure pricing before utilization stabilizes.",
        ],
        "questions": [
            "Is SiC demand improving in EV inverters and power electronics despite auto-cycle pressure?",
            "Are pricing and utilization signals stabilizing after capacity expansion?",
        ],
        "update_triggers": [
            "EV inverter demand change",
            "SiC pricing / utilization signal",
            "capacity expansion or substrate supply update",
        ],
    },
}


def build_research_summary(
    industry: dict[str, Any],
    market_result: dict[str, Any] | None,
    catalyst: dict[str, Any] | None,
    live_news: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a local V5.1.1 research summary for one industry."""

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
        industry_id=industry_id,
        trend_score=trend_score,
        price_score=price_score,
        heat_score=heat_score,
        validation=validation,
        valuation=valuation,
        covered=covered,
    )
    resonance = _price_news_resonance(
        industry_id=industry_id,
        price_score=price_score,
        heat_score=heat_score,
        live_news_count=live_news_count,
        low_relevance_count=_to_int(live_news.get("low_relevance_count")),
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
        market_result=market_result,
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
            "low_relevance_count": _to_int(live_news.get("low_relevance_count")),
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
    """Render the lightweight V5.1.1 local research-agent view."""

    lang = lang or "zh"
    text = RESEARCH_AGENT_TEXT[lang]
    st.markdown(f"## {text['view_title']}")
    st.caption(text["view_subtitle"])

    query = st.selectbox(
        text["industry_selector"],
        options=list(INDUSTRY_LABELS),
        index=0,
        format_func=lambda key: INDUSTRY_LABELS.get(key, {}).get(lang, key),
        placeholder=text["search_placeholder"],
        label_visibility="collapsed",
        key="research_agent_industry",
    )
    industry, matched = find_industry_trend(query)
    industry_id = str(industry.get("id") or "")
    coverage_text = text["covered"] if industry_id in CORE_RESEARCH_INDUSTRIES else text["not_covered"]
    st.caption(f"{text['coverage']}: {coverage_text}")
    if not matched:
        st.info(text["not_covered"])
        return

    market_result = get_market_confirmation_data(industry_id)
    catalyst = get_effective_catalyst_framework(industry_id)
    live_news = read_industry_news(industry_id)
    summary = localize_research_summary(build_research_summary(industry, market_result, catalyst, live_news), lang)
    summary["industry_name"] = INDUSTRY_LABELS.get(industry_id, {}).get(lang, summary.get("industry_name"))
    if not summary["covered"]:
        st.info(text["not_covered"])
        return

    st.markdown(f"### {text['local_section_title']}")
    st.caption(text["local_section_note"])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(text["trend_health"], _localized_value(summary["trend_health"], lang))
    with c2:
        st.metric(text["price_news_resonance"], _localized_value(summary["price_news_resonance"], lang))
    with c3:
        update = summary["suggest_framework_update"]
        st.metric(text["framework_update"], text["update_yes"] if update["recommended"] else text["update_no"])

    st.markdown(f"**{text['health_note']}**")
    st.write(normalize_research_display_text(summary["trend_health"].get("note") or text["none"], lang))
    st.markdown(f"**{text['resonance_note']}**")
    st.write(normalize_research_display_text(summary["price_news_resonance"].get("note") or text["none"], lang))
    st.markdown(f"**{text['current_catalyst_mainline']}**")
    _render_bullets(_mainline_items(summary["current_catalyst_mainline"], lang), text["none"])
    st.markdown(f"**{text['risk_signals']}**")
    _render_bullets(_localized_items(summary["risk_signals"], lang), text["none"])
    st.markdown(f"**{text['pending_questions']}**")
    _render_bullets(_localized_items(summary["pending_questions"], lang), text["none"])
    st.markdown(f"**{text['reason']}**")
    st.write(normalize_research_display_text(update["reason"], lang))

    with st.expander(text["evidence"], expanded=False):
        st.dataframe(pd.DataFrame([summary["evidence"]]), width="stretch", hide_index=True)

    st.divider()
    _render_ai_prompt_package(text, summary, live_news, lang)


def _render_ai_prompt_package(
    text: dict[str, Any],
    summary: dict[str, Any],
    live_news: dict[str, Any],
    lang: str,
) -> None:
    st.markdown(f"### {text['ai_section_title']}")
    st.info(text["ai_disabled"])
    if st.button(text["ai_prompt_button"], key=f"ai_prompt_generate_{summary.get('industry_id')}"):
        st.session_state[f"ai_prompt_visible_{summary.get('industry_id')}"] = True

    prompt = build_ai_research_prompt(summary=summary, live_news=live_news, lang=lang)
    visible_key = f"ai_prompt_visible_{summary.get('industry_id')}"
    if st.session_state.get(visible_key, True):
        st.text_area(
            text["ai_prompt_label"],
            value=prompt,
            height=520,
            key=f"ai_research_prompt_{summary.get('industry_id')}_{lang}",
        )
        st.download_button(
            text["ai_download_label"],
            data=prompt,
            file_name=build_ai_research_prompt_filename(str(summary.get("industry_id") or "")),
            mime="text/markdown",
            key=f"ai_research_prompt_download_{summary.get('industry_id')}_{lang}",
        )


def _trend_health(
    *,
    industry_id: str,
    trend_score: float | None,
    price_score: float | None,
    heat_score: float | None,
    validation: float | None,
    valuation: float | None,
    covered: bool,
) -> dict[str, Any]:
    if not covered:
        return {"status": "not_covered", "label": "Not covered", "label_zh": "未覆盖", "score": None}
    values = [value for value in [trend_score, price_score, heat_score, validation] if value is not None]
    if len(values) < 3:
        return {
            "status": "insufficient_data",
            "label": "Insufficient data",
            "label_zh": "数据不足",
            "score": None,
            "note": "The local inputs are not broad enough for a high-confidence rule read.",
        }
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
    profile = INDUSTRY_RESEARCH_PROFILES.get(industry_id, {})
    note = _health_note(profile.get("health_focus"), status, price_score, heat_score, validation, valuation)
    return {"status": status, "label": label, "label_zh": label_zh, "score": score, "note": note}


def _price_news_resonance(
    *,
    industry_id: str,
    price_score: float | None,
    heat_score: float | None,
    live_news_count: int,
    low_relevance_count: int,
    market_available: bool,
    news_status: str,
    covered: bool,
) -> dict[str, str]:
    if not covered:
        return {"status": "not_covered", "label": "Not covered", "label_zh": "未覆盖"}
    if price_score is None or heat_score is None:
        return {
            "status": "insufficient_data",
            "label": "Insufficient data",
            "label_zh": "数据不足",
            "note": "Either price confirmation or catalyst heat is missing.",
        }
    profile = INDUSTRY_RESEARCH_PROFILES.get(industry_id, {})
    if price_score >= 6.5 and heat_score >= 6.5 and live_news_count > 0:
        return _resonance_payload(
            "aligned",
            "Aligned with cached evidence",
            "与缓存证据共振",
            "Price confirmation and catalyst heat are both strong, with high/medium relevance cached news evidence.",
            profile,
        )
    if price_score >= 6.5 and heat_score >= 6.5:
        return _resonance_payload(
            "framework_price_aligned",
            "Framework and price aligned; news evidence thin",
            "框架与价格一致，新闻证据偏薄",
            "Price confirmation and catalyst heat are aligned, but cached high-relevance news is limited.",
            profile,
        )
    if heat_score >= 7.0 and price_score < 5.0:
        return _resonance_payload(
            "news_leads_price",
            "Catalyst heat leads price",
            "催化热度领先价格",
            "The narrative layer is active, but price confirmation has not caught up.",
            profile,
        )
    if price_score >= 6.0 and live_news_count == 0 and news_status != "available":
        return _resonance_payload(
            "price_leads_news",
            "Price leads cached news",
            "价格领先缓存新闻",
            "Representative prices are stronger than the current cached news evidence.",
            profile,
        )
    if not market_available and heat_score >= 6.5:
        return _resonance_payload(
            "news_only",
            "Framework / catalyst only",
            "仅有框架 / 催化信号",
            "Market confirmation is not available, so resonance cannot be fully tested.",
            profile,
        )
    if low_relevance_count > live_news_count and live_news_count == 0:
        return _resonance_payload(
            "noisy_news",
            "News feed noisy, no clear resonance",
            "新闻噪音较多，暂未共振",
            "The cache contains low-relevance items but little high-relevance evidence.",
            profile,
        )
    return _resonance_payload(
        "mixed",
        "Mixed",
        "分化",
        "Price, catalyst heat, and cached news are not yet moving as one signal.",
        profile,
    )


def _current_catalyst_mainline(industry: dict[str, Any], catalyst: dict[str, Any], covered: bool) -> str:
    if not covered:
        return ""
    industry_id = str(industry.get("id") or "")
    profile = INDUSTRY_RESEARCH_PROFILES.get(industry_id, {})
    profile_mainline = str(profile.get("catalyst_mainline") or "")
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
    parts = [profile_mainline, summary, *event_titles, *drivers]
    return " | ".join(part for part in parts if part)[:800]


def _risk_signals(
    industry: dict[str, Any],
    market_result: dict[str, Any],
    live_news: dict[str, Any],
    valuation: float | None,
    covered: bool,
) -> list[str]:
    if not covered:
        return []
    profile = INDUSTRY_RESEARCH_PROFILES.get(str(industry.get("id") or ""), {})
    risks = [str(item) for item in industry.get("riskSignals", []) if item]
    risks.extend(str(item) for item in profile.get("risk_overlays", []) if item)
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
    return _unique(risks)[:7]


def _pending_questions(
    industry_id: str,
    market_result: dict[str, Any],
    live_news: dict[str, Any],
    resonance_status: str,
    covered: bool,
) -> list[str]:
    if not covered:
        return []
    profile = INDUSTRY_RESEARCH_PROFILES.get(industry_id, {})
    questions = list(profile.get("questions", []))
    if not market_result.get("available"):
        questions.append("Can price confirmation be rechecked after market data becomes available?")
    if _to_int(live_news.get("live_news_count_7d")) == 0:
        questions.append("Do external news sources confirm the current catalyst line beyond the local framework?")
    if resonance_status in {"news_leads_price", "mixed", "news_only", "noisy_news"}:
        questions.append("Will price breadth and relative strength catch up with the catalyst narrative?")
    for trigger in profile.get("update_triggers", [])[:2]:
        questions.append(f"Has there been a verified change in {trigger}?")
    return _unique(questions)[:5]


def _framework_update_judgement(
    *,
    industry_id: str,
    catalyst: dict[str, Any],
    live_news: dict[str, Any],
    market_result: dict[str, Any],
    resonance_status: str,
    covered: bool,
) -> dict[str, Any]:
    if not covered:
        return {"recommended": False, "reason": "V5.1.1 only covers core industries."}
    live_news_count = _to_int(live_news.get("live_news_count_7d"))
    heat_direction = str(catalyst.get("heat_direction") or "")
    event_count = len(catalyst.get("events") or [])
    profile = INDUSTRY_RESEARCH_PROFILES.get(industry_id, {})
    trigger_text = ", ".join(profile.get("update_triggers", [])[:2])
    price_score = _to_float(market_result.get("score")) if market_result.get("available") else None
    if live_news_count >= 3 and heat_direction == "Rising" and resonance_status in {
        "aligned",
        "framework_price_aligned",
        "news_leads_price",
    }:
        return {
            "recommended": True,
            "reason": f"Manual review is suggested because cached evidence and rising catalyst heat may indicate a change in {trigger_text or 'the core catalyst line'}. The local summary module only flags this and does not apply any framework update.",
        }
    if price_score is not None and price_score < 4.5 and heat_direction == "Rising":
        return {
            "recommended": True,
            "reason": "Manual review is suggested because catalyst heat is rising while market-price confirmation is weak; the framework may need a divergence note. The local summary module does not apply any framework update.",
        }
    if event_count < 2:
        return {
            "recommended": True,
            "reason": "The local catalyst framework has too few events for this core industry, so a manual framework review is suggested. The local summary module does not apply any framework update.",
        }
    return {
        "recommended": False,
        "reason": f"{industry_id} already has a usable local catalyst framework. Current evidence does not yet justify even a manual update beyond normal monitoring of {trigger_text or 'the core catalyst line'}. No automatic change is made.",
    }


def _market_price_score(industry: dict[str, Any], market_result: dict[str, Any]) -> float | None:
    if market_result.get("available"):
        return _to_float(market_result.get("score"))
    return _to_float(industry.get("marketConfirmation"))


def localize_research_summary(summary: dict[str, Any], lang: str) -> dict[str, Any]:
    """Return a display-only localized copy of a research summary."""

    if lang != "zh":
        return summary
    # Final display pass covers health_note, resonance_note, risk_signals, validation questions, and research_axis.
    localized = dict(summary)
    localized["trend_health"] = _localize_payload(summary.get("trend_health"))
    localized["price_news_resonance"] = _localize_payload(summary.get("price_news_resonance"))
    localized["current_catalyst_mainline"] = normalize_research_display_text(
        summary.get("current_catalyst_mainline"), lang
    )
    localized["risk_signals"] = [
        normalize_research_display_text(item, lang) for item in summary.get("risk_signals", [])
    ]
    localized["pending_questions"] = [
        normalize_research_display_text(item, lang) for item in summary.get("pending_questions", [])
    ]
    update = dict(summary.get("suggest_framework_update") or {})
    update["reason"] = normalize_research_display_text(update.get("reason"), lang)
    localized["suggest_framework_update"] = update
    return localized


def _localize_payload(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    localized = dict(payload)
    if localized.get("status") in RESONANCE_NOTE_ZH:
        localized["note"] = _localized_resonance_note(localized)
        return localized
    for key in ("label", "label_zh", "note"):
        if key in localized:
            localized[key] = normalize_research_display_text(localized[key], "zh")
    return localized


def _localized_resonance_note(payload: dict[str, Any]) -> str:
    note = RESONANCE_NOTE_ZH.get(str(payload.get("status") or ""), "")
    axis = normalize_research_axis(payload.get("research_axis"), "zh")
    if axis:
        return f"{note.rstrip('。')}。研究主线：{axis}。"
    return note


def translate_research_label(value: object, lang: str = "zh") -> str:
    return normalize_research_display_text(value, lang)


def normalize_research_axis(value: object, lang: str = "zh") -> str:
    raw = str(value or "").strip().rstrip(".")
    if not raw:
        return ""
    if "->" in raw:
        parts = raw.split("->")
    else:
        parts = raw.split("|")
    return "、".join(normalize_research_display_text(part, lang).strip() for part in parts if part.strip())


def normalize_research_display_text(value: object, lang: str = "zh") -> str:
    text = fix_mojibake_text(value).strip()
    if lang != "zh" or not text:
        return text
    if text in ZH_TEXT_MAP:
        return fix_mojibake_text(ZH_TEXT_MAP[text])
    if f"{text}." in ZH_TEXT_MAP:
        return fix_mojibake_text(ZH_TEXT_MAP[f"{text}."])
    dynamic_text = _localized_text(text, lang)
    if dynamic_text != text:
        return fix_mojibake_text(dynamic_text)
    translated = text
    for source, target in sorted(ZH_TEXT_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(source, fix_mojibake_text(target))
    if translated != text:
        return fix_mojibake_text(translated)
    return fix_mojibake_text(text)


def _localized_value(payload: dict[str, Any], lang: str) -> str:
    label = payload.get("label_zh") if lang == "zh" else payload.get("label")
    score = payload.get("score")
    display_label = fix_mojibake_text(label)
    return f"{display_label} ({score:.1f})" if isinstance(score, float) else str(display_label or "")


def _render_bullets(items: list[str], empty_text: str) -> None:
    if not items:
        st.markdown(f"- {empty_text}")
        return
    for item in items:
        st.markdown(f"- {fix_mojibake_text(item)}")


def _mainline_items(value: object, lang: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    primary = raw.split("|", maxsplit=1)[0]
    if "->" in primary:
        parts = primary.split("->")
    else:
        parts = [primary]
    return _localized_items(parts[:5], lang)


def _localized_items(items: list[str], lang: str) -> list[str]:
    return [normalize_research_display_text(item, lang) for item in items if str(item).strip()]


def fix_mojibake_text(value: object) -> str:
    """Repair common UTF-8 text that was accidentally decoded as Latin-1/CP1252."""

    text = str(value or "")
    if not text or not _looks_like_mojibake(text):
        return text

    candidates = []
    original_score = _mojibake_score(text)
    for encoding in ("latin1", "cp1252"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if _mojibake_score(repaired) < original_score:
            candidates.append(repaired)

    if not candidates:
        return text
    return min(candidates, key=_mojibake_score)


def _looks_like_mojibake(text: str) -> bool:
    markers = (
        "\u00c3",
        "\u00c2",
        "\u00e3\u20ac",
        "\u00e5",
        "\u00e6",
        "\u00e7",
        "\u00ef\u00bc",
        "\u00e9\u00aa",
        "\u00e8\u00af",
    )
    return any(marker in text for marker in markers)


def _mojibake_score(text: str) -> int:
    markers = (
        "\u00c3",
        "\u00c2",
        "\u00e3\u20ac",
        "\u00e5",
        "\u00e6",
        "\u00e7",
        "\u00ef\u00bc",
        "\u00e9\u00aa",
        "\u00e8\u00af",
        "\ufffd",
    )
    return sum(text.count(marker) for marker in markers)


def _localized_text(value: object, lang: str) -> str:
    text = fix_mojibake_text(value).strip()
    if lang != "zh" or not text:
        return text
    if text in ZH_TEXT_MAP:
        return fix_mojibake_text(ZH_TEXT_MAP[text])
    if f"{text}." in ZH_TEXT_MAP:
        return fix_mojibake_text(ZH_TEXT_MAP[f"{text}."])
    if ". Research axis: " in text:
        note, axis = text.split(". Research axis: ", maxsplit=1)
        axis = axis.removesuffix(".")
        axis_items = normalize_research_axis(axis, "zh")
        note_text = _localized_text(note, lang).rstrip("。.")
        return f"{note_text}。研究主线：{axis_items}。"
    if text.startswith("Has there been a verified change in ") and text.endswith("?"):
        trigger = text.removeprefix("Has there been a verified change in ").removesuffix("?")
        return f"是否已经验证：{_localized_text(trigger, lang)} 出现实质变化？"
    if text.startswith("Manual review is suggested because cached evidence and rising catalyst heat may indicate a change in "):
        trigger = text.removeprefix(
            "Manual review is suggested because cached evidence and rising catalyst heat may indicate a change in "
        ).removesuffix(". The local summary module only flags this and does not apply any framework update.")
        return f"建议人工复核：缓存证据和上行催化热度可能指向「{_localized_trigger_text(trigger)}」变化。本地摘要模块只做提示，不自动修改行业框架。"
    if text.startswith("Manual review is suggested because catalyst heat is rising while market-price confirmation is weak"):
        return "建议人工复核：催化热度上行，但市场价格确认偏弱，行业框架可能需要补充背离说明。本地摘要模块不自动修改行业框架。"
    if text.startswith("The local catalyst framework has too few events"):
        return "建议人工复核：该核心行业的本地催化框架事件数量偏少，需要人工检查是否补充框架。本地摘要模块不自动修改行业框架。"
    if " already has a usable local catalyst framework. Current evidence does not yet justify even a manual update" in text:
        industry_id = text.split(" already has", maxsplit=1)[0]
        label = INDUSTRY_LABELS.get(industry_id, {}).get("zh", industry_id)
        return f"{label} 已有可用的本地催化框架；当前证据尚不足以支持人工更新，只需继续跟踪核心催化线。不会自动修改框架。"
    return fix_mojibake_text(text)


def _localized_trigger_text(text: str) -> str:
    parts = [fix_mojibake_text(part).strip() for part in text.split(",") if part.strip()]
    return "、".join(_localized_text(part, "zh") for part in parts) or "核心催化线"


ZH_TEXT_MAP = {
    "AI compute demand is still supportive, but the healthier read depends on whether HBM, advanced packaging, foundry, and equipment breadth move together.": "AI 算力需求仍有支撑，但趋势健康度取决于 HBM、先进封装、晶圆代工、设备产能等环节能否同步确认。",
    "The key split is between high-end HBM demand and the broader DRAM / NAND cycle; trend quality improves only when pricing and inventory validation broaden.": "核心分歧在高端 HBM 需求与更广泛 DRAM / NAND 周期之间；只有价格和库存验证扩散，趋势质量才会改善。",
    "Trend quality depends on whether AI data-center bandwidth upgrades translate into product-route validation beyond a few optical leaders.": "趋势质量取决于 AI 数据中心带宽升级能否从少数光模块龙头，扩散为更广泛的产品路线验证。",
    "The industry remains strongest when GPU, server, networking, power, cooling, and cloud capex indicators reinforce one another instead of concentrating in one leader group.": "GPU、服务器、网络、电力、散热和云厂商资本开支互相验证时，AI 算力链条最健康；若只集中在少数龙头，质量会下降。",
    "Gold is healthiest when price strength is confirmed by real-rate pressure, dollar weakness, central-bank demand, and defensive allocation rather than a single risk-off headline.": "黄金价格上涨若同时得到实际利率下行、美元走弱、央行购金和防御配置确认，趋势更健康；单一避险事件不足以构成高质量验证。",
    "SiC needs both power-semiconductor demand and end-market validation; EV-cycle pressure and pricing utilization are the main checks against the technology story.": "碳化硅需要功率半导体需求和终端市场同时验证；电动车周期、价格和产能利用率是检验技术叙事的关键变量。",
    "The rule read is constructive, but still depends on continued confirmation across price breadth and fundamental validation.": "本地规则读数偏建设性，但仍需要价格广度和基本面验证继续配合。",
    "The rule read is mixed: at least one of price, catalyst heat, or validation is not yet broad enough.": "本地规则读数偏分化，价格、催化热度或验证层至少有一项还不够充分。",
    "The rule read is cautious because confirmation is not strong enough for a healthy-trend label.": "本地规则读数偏谨慎，当前确认强度还不足以归为健康趋势。",
    "Expectation pressure is elevated, so the summary treats the trend as more fragile.": "估值或预期压力偏高，因此趋势解读按更脆弱处理。",
    "Price and catalyst heat are far enough apart to require follow-up.": "价格确认与催化热度差距较大，需要继续跟踪。",
    "Fundamental validation remains a gating issue.": "基本面验证仍是关键门槛。",
    "Price confirmation and catalyst heat are both strong, with high/medium relevance cached news evidence. Research axis: AI capex -> HBM / accelerator demand -> advanced packaging and equipment capacity -> broader chip-chain confirmation.": "价格确认和催化热度都较强，并有中高相关度缓存新闻支持。研究主线是 AI 资本开支、HBM / 加速器需求、先进封装与设备产能，以及更广泛芯片链确认。",
    "Either price confirmation or catalyst heat is missing.": "价格确认或催化热度数据缺失，暂时无法完整判断共振。",
    "Price confirmation and catalyst heat are both strong, with high/medium relevance cached news evidence.": "价格确认与催化热度均较强，并且有中高相关度缓存新闻作为证据支持。",
    "Price confirmation and catalyst heat are both strong.": "价格确认与催化热度均较强。",
    "Price confirmation is strong, but catalyst heat is not yet confirmed.": "价格确认较强，但催化热度尚未充分确认。",
    "Catalyst heat is strong, but price confirmation is not yet strong.": "催化热度较强，但价格走势尚未充分确认。",
    "Price confirmation and catalyst heat are weak.": "价格确认与催化热度均偏弱。",
    "High/medium relevance cached news evidence is available.": "已有中高相关度缓存新闻证据。",
    "Cached news evidence is limited.": "缓存新闻证据有限。",
    "Price confirmation and catalyst heat are aligned, but cached high-relevance news is limited.": "价格确认与催化热度方向一致，但高相关度缓存新闻偏少。",
    "The narrative layer is active, but price confirmation has not caught up.": "叙事层较活跃，但价格确认尚未跟上。",
    "Representative prices are stronger than the current cached news evidence.": "代表性价格强于当前缓存新闻证据。",
    "Market confirmation is not available, so resonance cannot be fully tested.": "市场确认数据不可用，因此暂时无法完整检验共振。",
    "The cache contains low-relevance items but little high-relevance evidence.": "缓存中低相关内容较多，高相关证据不足。",
    "Price, catalyst heat, and cached news are not yet moving as one signal.": "价格确认、催化热度与缓存新闻尚未形成同一方向的共振信号。",
    "Price, catalyst heat, and cached news are moving as one signal.": "价格确认、催化热度与缓存新闻正在形成同向共振。",
    "Price and news are diverging.": "价格走势与新闻催化出现分化。",
    "Cached news support is thin.": "缓存新闻支持力度较弱。",
    "Catalyst heat is not yet confirmed by price.": "催化热度尚未得到价格走势确认。",
    "Price confirmation is stronger than news confirmation.": "价格确认强于新闻确认。",
    "News confirmation is stronger than price confirmation.": "新闻确认强于价格确认。",
    "AI capex": "AI 资本开支",
    "HBM / accelerator demand": "HBM / 加速器需求",
    "advanced packaging and equipment capacity": "先进封装与设备产能",
    "broader chip-chain confirmation": "更广泛芯片链确认",
    "HBM qualification and capacity": "HBM 认证与产能",
    "DRAM / NAND price cycle": "DRAM / NAND 价格周期",
    "enterprise SSD demand": "企业级 SSD 需求",
    "supplier capex discipline": "供应商资本开支纪律",
    "AI cluster bandwidth pressure": "AI 集群带宽压力",
    "800G / 1.6T optical module upgrades": "800G / 1.6T 光模块升级",
    "CPO / silicon photonics validation": "CPO / 硅光路线验证",
    "module vendor order breadth": "模块厂订单广度",
    "cloud capex": "云厂商资本开支",
    "GPU / accelerator demand": "GPU / 加速器需求",
    "AI server and networking buildout": "AI 服务器与网络建设",
    "power and cooling bottlenecks": "电力与散热瓶颈",
    "utilization validation": "利用率验证",
    "real-rate expectations": "实际利率预期",
    "dollar and liquidity conditions": "美元与流动性环境",
    "central-bank demand": "央行购金需求",
    "geopolitical / inflation hedge demand": "地缘与通胀对冲需求",
    "EV inverter and power-electronics demand": "电动车逆变器与功率电子需求",
    "SiC substrate / device capacity": "SiC 衬底与器件产能",
    "pricing and utilization stabilization": "价格与利用率企稳",
    "industrial and energy applications": "工业与能源应用",
    "Headline AI-chip strength may mask dispersion in foundry, equipment, and consumer-electronics demand.": "AI 芯片表观强势可能掩盖晶圆代工、设备和消费电子需求的分化。",
    "Export controls, capex timing, and inventory turns can quickly change the validation layer.": "出口管制、资本开支节奏和库存周转可能快速改变验证层。",
    "HBM strength can coexist with weaker commodity DRAM or NAND pricing.": "HBM 强势可能与通用 DRAM 或 NAND 价格偏弱同时存在。",
    "Rapid capacity expansion may turn a demand story into a later-cycle supply risk.": "产能快速扩张可能把需求故事转化为后周期供给风险。",
    "Ticker strength can be driven by general AI/networking beta rather than optical-module evidence.": "个股强势可能来自 AI / 网络板块 beta，而不一定来自光模块证据。",
    "CPO timing remains a product-route question; 800G / 1.6T demand does not automatically validate every architecture.": "CPO 节奏仍是产品路线问题；800G / 1.6T 需求不能自动验证所有架构。",
    "Capex enthusiasm can run ahead of utilization, revenue conversion, or power availability.": "资本开支热情可能领先于利用率、收入转化或电力供给。",
    "Leadership concentration can make the theme look healthier than the full infrastructure chain.": "龙头集中度过高可能让主题看起来强于完整基础设施链条。",
    "A stronger dollar or higher real yields can weaken the macro confirmation layer.": "美元走强或实际收益率上行会削弱宏观确认层。",
    "Short-term risk-off flow may fade if central-bank demand or rate expectations do not confirm.": "若央行需求或利率预期不能确认，短期避险资金流可能退潮。",
    "EV demand softness can offset the long-term power-semiconductor upgrade story.": "电动车需求偏弱可能抵消长期功率半导体升级逻辑。",
    "Capacity additions may pressure pricing before utilization stabilizes.": "产能扩张可能在利用率企稳前压制价格。",
    "Valuation pressure": "估值压力",
    "Inventory cycle reversal": "库存周期反转",
    "Capex slowdown": "资本开支放缓",
    "Demand weakening": "需求走弱",
    "Price-news divergence": "价格与新闻分化",
    "Policy uncertainty": "政策不确定性",
    "Crowded trade": "交易拥挤",
    "Earnings miss risk": "业绩不及预期风险",
    "Narrative runs ahead of validation": "叙事领先于验证",
    "Margin or pricing divergence": "利润率或价格分化",
    "Macro conditions reduce visibility": "宏观环境降低可见度",
    "Weak market confirmation": "市场确认偏弱",
    "Limited fundamental validation": "基本面验证不足",
    "Elevated valuation pressure": "估值压力上升",
    "Memory price pullback": "存储价格回落",
    "Overly rapid capex expansion": "资本开支扩张过快",
    "AI server demand below expectations": "AI 服务器需求低于预期",
    "Margin pressure from stronger competition": "竞争加剧导致利润率压力",
    "Wholesale price decline": "批价下行",
    "Rising channel inventory": "渠道库存升高",
    "Weaker-than-expected consumption recovery": "消费修复不及预期",
    "Marketing expense pressure": "费用投放压力",
    "Policy or business-consumption constraints": "政策或商务消费约束",
    "Market-price confirmation is weak relative to the framework.": "市场价格确认弱于行业框架。",
    "Representative ticker breadth is weak below MA50.": "代表性标的站上 MA50 的广度偏弱。",
    "Valuation / expectation pressure is elevated.": "估值或预期压力偏高。",
    "Cached high-relevance news evidence is limited.": "缓存中的高相关度新闻证据有限。",
    "Can AI chip, HBM, foundry, and equipment signals remain aligned instead of splitting further?": "AI 芯片、HBM、晶圆代工和设备信号能否继续一致，而不是进一步分化？",
    "Does cloud capex translate into broad supply-chain orders rather than only leader performance?": "云厂商资本开支能否转化为广泛供应链订单，而不只是龙头表现？",
    "Are HBM strength and DRAM / NAND pricing moving together or separating by product tier?": "HBM 强势与 DRAM / NAND 价格是在同步，还是按产品层级分化？",
    "Is supplier capex discipline still supportive for the next pricing cycle?": "供应商资本开支纪律是否仍支撑下一轮价格周期？",
    "Are 800G / 1.6T upgrades translating into broad module demand rather than isolated leader strength?": "800G / 1.6T 升级是否转化为广泛模块需求，而不是少数龙头强势？",
    "Is CPO / silicon photonics validation improving at the product-route level?": "CPO / 硅光验证是否在产品路线层面改善？",
    "Is AI infrastructure capex still expanding beyond GPU leaders into servers, networking, power, and cooling?": "AI 基础设施资本开支是否从 GPU 龙头继续扩散到服务器、网络、电力和散热？",
    "Can utilization and revenue validation keep pace with high market attention?": "利用率和收入验证能否跟上较高市场关注度？",
    "Are real-rate, dollar, and central-bank demand signals pointing in the same direction?": "实际利率、美元和央行需求信号是否指向同一方向？",
    "Is gold price strength supported by macro hedging demand rather than only short-term risk-off flow?": "黄金强势是否由宏观对冲需求支撑，而不只是短期避险资金？",
    "Is SiC demand improving in EV inverters and power electronics despite auto-cycle pressure?": "在汽车周期压力下，SiC 在电动车逆变器和功率电子中的需求是否改善？",
    "Are pricing and utilization signals stabilizing after capacity expansion?": "产能扩张后，价格和利用率信号是否企稳？",
    "Can price confirmation be rechecked after market data becomes available?": "市场数据可用后，能否重新检查价格确认？",
    "Do external news sources confirm the current catalyst line beyond the local framework?": "本地框架之外，外部新闻是否确认当前催化主线？",
    "Will price breadth and relative strength catch up with the catalyst narrative?": "价格广度和相对强度能否跟上催化叙事？",
    "new HBM / advanced-packaging capacity signal": "新的 HBM / 先进封装产能信号",
    "cloud capex guidance change": "云厂商资本开支指引变化",
    "export-control or equipment-order change": "出口管制或设备订单变化",
    "HBM qualification or allocation change": "HBM 认证或分配变化",
    "DRAM / NAND price-cycle inflection": "DRAM / NAND 价格周期拐点",
    "memory supplier capex discipline change": "存储供应商资本开支纪律变化",
    "800G / 1.6T order evidence": "800G / 1.6T 订单证据",
    "CPO or silicon-photonics validation milestone": "CPO 或硅光验证里程碑",
    "module-vendor margin or capacity signal": "模块厂利润率或产能信号",
    "hyperscaler capex revision": "大云厂资本开支修正",
    "accelerator supply or networking bottleneck change": "加速器供给或网络瓶颈变化",
    "power / cooling constraint evidence": "电力 / 散热约束证据",
    "real-yield or dollar regime shift": "实际收益率或美元环境变化",
    "central-bank buying evidence": "央行购金证据",
    "geopolitical or inflation-hedge demand change": "地缘或通胀对冲需求变化",
    "EV inverter demand change": "电动车逆变器需求变化",
    "SiC pricing / utilization signal": "SiC 价格 / 利用率信号",
    "capacity expansion or substrate supply update": "产能扩张或衬底供应更新",
    "the core catalyst line": "核心催化线",
}


def _health_note(
    focus: object,
    status: str,
    price_score: float | None,
    heat_score: float | None,
    validation: float | None,
    valuation: float | None,
) -> str:
    components = [str(focus or "")]
    if status == "healthy":
        components.append("The rule read is constructive, but still depends on continued confirmation across price breadth and fundamental validation.")
    elif status == "watch":
        components.append("The rule read is mixed: at least one of price, catalyst heat, or validation is not yet broad enough.")
    elif status == "weak":
        components.append("The rule read is cautious because confirmation is not strong enough for a healthy-trend label.")
    if valuation is not None and valuation >= 7.0:
        components.append("Expectation pressure is elevated, so the summary treats the trend as more fragile.")
    if price_score is not None and heat_score is not None and abs(price_score - heat_score) >= 2.0:
        components.append("Price and catalyst heat are far enough apart to require follow-up.")
    if validation is not None and validation < 6.0:
        components.append("Fundamental validation remains a gating issue.")
    return " ".join(component for component in components if component)


def _resonance_payload(
    status: str,
    label: str,
    label_zh: str,
    note: str,
    profile: dict[str, Any],
) -> dict[str, str]:
    mainline = str(profile.get("catalyst_mainline") or "")
    payload = {"status": status, "label": label, "label_zh": label_zh, "note": note, "research_axis": mainline}
    if mainline:
        note = f"{note} Research axis: {mainline}."
        payload["note"] = note
    return payload


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

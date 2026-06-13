"""Standalone Streamlit entrypoint for the Industry Trend Search Engine."""

from __future__ import annotations

import streamlit as st

from src.industry_radar_page import render_industry_radar_page
from src.industry_research_agent import render_research_agent_page
from src.industry_trend_page import render_industry_trend_search_page, render_language_picker


st.set_page_config(
    page_title="AI 辅助行业研究雷达系统",
    layout="wide",
)


def main() -> None:
    """Render the standalone industry research views."""

    lang = render_language_picker()
    product_intro = {
        "zh": "本系统用于行业趋势初筛、新闻催化跟踪、风险识别和 AI 辅助研究复核。系统不提供直接买卖建议，所有输出仅供研究参考。",
        "en": "This system supports industry screening, news catalyst tracking, risk identification, and AI-assisted research review. It does not provide direct buy/sell advice; all outputs are for research reference only.",
    }
    workflow = {
        "zh": "核心流程：行业初筛 → 价格确认 → 新闻催化 → 风险识别 → 本地摘要 → AI 复核输入包",
        "en": "Core workflow: industry screening → price confirmation → news catalysts → risk identification → local summary → AI review input package",
    }
    st.sidebar.markdown("### AI 辅助行业研究雷达系统")
    st.sidebar.caption(product_intro[lang])
    st.sidebar.caption(workflow[lang])
    st.caption(product_intro[lang])
    st.caption(workflow[lang])
    labels = {
        "zh": ("单行业搜索", "行业雷达总览", "研究摘要 / AI 备忘录"),
        "en": ("Single Industry Search", "Industry Radar Overview", "Research Summary / AI Memo"),
    }
    labels["zh"] = ("单行业搜索", "行业雷达总览", "研究摘要 / AI 输入包")
    labels["en"] = ("Single Industry Search", "Industry Radar Overview", "Research Summary / AI Input Package")
    search_label, radar_label, research_label = labels[lang]
    selected_view = st.radio(
        "View",
        [search_label, radar_label, research_label],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_view == radar_label:
        render_industry_radar_page(lang)
    elif selected_view == research_label:
        render_research_agent_page(lang)
    else:
        render_industry_trend_search_page(lang=lang, show_language_picker=False)


if __name__ == "__main__":
    main()

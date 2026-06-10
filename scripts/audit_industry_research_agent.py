"""Read-only audit for V5.1 local research-agent rules."""

from __future__ import annotations

import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if "streamlit" not in sys.modules:
    sys.modules["streamlit"] = types.SimpleNamespace(cache_data=lambda *args, **kwargs: (lambda func: func))

from src.industry_research_agent import CORE_RESEARCH_INDUSTRIES, build_research_summary  # noqa: E402
from src.industry_trend_data import industryTrendData  # noqa: E402


REQUIRED_FIELDS = {
    "trend_health",
    "price_news_resonance",
    "current_catalyst_mainline",
    "risk_signals",
    "pending_questions",
    "suggest_framework_update",
}


def main() -> int:
    issues: list[str] = []
    known_ids = {str(industry.get("id") or "") for industry in industryTrendData}
    missing_core = sorted(CORE_RESEARCH_INDUSTRIES - known_ids)
    if missing_core:
        issues.append(f"core research industries missing from trend data: {missing_core}")

    for industry_id in sorted(CORE_RESEARCH_INDUSTRIES):
        industry = next((item for item in industryTrendData if item.get("id") == industry_id), None)
        if not industry:
            continue
        summary = build_research_summary(industry, sample_market(), sample_catalyst(), sample_news())
        missing_fields = sorted(REQUIRED_FIELDS - set(summary))
        if missing_fields:
            issues.append(f"{industry_id} missing output fields: {missing_fields}")
        if not summary.get("covered"):
            issues.append(f"{industry_id} should be covered")
        guardrails = summary.get("guardrails") or {}
        if guardrails.get("openai_api_used"):
            issues.append(f"{industry_id} should not call OpenAI API")
        if guardrails.get("trading_instruction"):
            issues.append(f"{industry_id} should not output trading instruction")
        if guardrails.get("auto_framework_update"):
            issues.append(f"{industry_id} should not auto-update framework")
        update = summary.get("suggest_framework_update") or {}
        if "recommended" not in update or "reason" not in update:
            issues.append(f"{industry_id} framework update judgement missing recommended/reason")

    print_report("V5.1 RESEARCH AGENT ISSUES", issues)
    return 1 if issues else 0


def sample_market() -> dict:
    return {
        "available": True,
        "score": 7.1,
        "above_ma50_ratio": 0.66,
    }


def sample_catalyst() -> dict:
    return {
        "heat_score": 7.2,
        "heat_level": "High",
        "heat_direction": "Rising",
        "summary": "Audit catalyst summary",
        "events": [
            {"title": "Audit catalyst one", "event_type": "capex", "impact": "positive", "confidence": "medium"},
            {"title": "Audit catalyst two", "event_type": "technology", "impact": "mixed", "confidence": "medium"},
        ],
    }


def sample_news() -> dict:
    return {
        "live_news_count_7d": 3,
        "live_news_status": "available",
        "items": [{"relevance": "high"} for _ in range(3)],
    }


def print_report(title: str, payload: object) -> None:
    print(f"\n## {title}")
    if not payload:
        print("None")
        return
    for item in payload:
        print(f"- {item}")


if __name__ == "__main__":
    raise SystemExit(main())

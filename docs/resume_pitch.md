# Resume Pitch

## 中文简历版

- 设计并迭代一个 AI 辅助行业研究雷达系统，支持行业初筛、单行业研究、市场价格确认、新闻催化跟踪、风险识别、本地摘要和 ChatGPT 研究输入包导出。
- 负责产品需求拆解、研究工作流设计、指标口径定义、行业数据结构设计、页面 Demo 流程收敛和 audit 验证，并通过 Codex 辅助完成工程实现。
- 构建 V3 市场价格确认模块，使用 ETF / 龙头股代理样本计算 MA breadth、median 3M return、relative strength 和市场价格确认分，用于判断行业趋势是否得到价格层面验证。
- 建立 V4 本地催化框架、新闻缓存和动态催化快照，用于观察新闻催化是否强化、分化、降温或待验证。
- 构建 V5.1 本地规则摘要、V5.2 ChatGPT 研究 Prompt 导出器和 V5.3 数据状态栏，把研究材料整理成可解释、可复核、可导出的 AI 研究输入包。
- 新增多层 audit scripts，覆盖催化事件语义、全行业语义质量、新闻 provider schema 和代码编译检查，提升研究数据可维护性。

## English Resume Version

- Designed and iterated an AI-assisted industry research radar system covering industry screening, single-industry research, market-price confirmation, news catalyst tracking, risk identification, local summaries, and ChatGPT research prompt export.
- Owned product requirements, research workflow design, metric definitions, industry data structures, demo flow refinement, and audit validation, with Codex assisting implementation.
- Built a V3 market-price confirmation layer using ETF and representative company proxies to compute MA breadth, median 3M return, relative strength, and market confirmation scores.
- Developed a V4 local catalyst framework, cached news layer, and dynamic catalyst snapshots to track whether industry catalysts are reinforced, diverging, weakening, or still pending validation.
- Added V5.1 local rule-based summaries, a V5.2 ChatGPT prompt exporter, and a V5.3 data status bar to convert structured evidence into explainable AI research input packages.
- Added audit scripts for catalyst-event semantics, cross-industry semantic quality, news-provider schema validation, and compile checks to improve maintainability.

## Interview Framing

This project should be described as a research workflow and product prototype, not as an automated trading system or prediction engine.

Recommended framing:

- It is not a wrapper around ChatGPT. The system first structures local data, price confirmation, news evidence, catalyst signals, and risks, then exports an AI research task brief.
- Trend scores are screening signals, not investment recommendations.
- V5.1 is local deterministic logic, not model output.
- V5.2 does not call OpenAI or any LLM API; it creates a copy-ready prompt for manual ChatGPT review.
- V5.3 makes the data basis visible by showing market, news, catalyst snapshot, and framework freshness.
- The current Streamlit UI is a lightweight research prototype and interview demo surface. It is suitable for screenshots and workflow validation, while a later public-facing frontend could be designed separately in Figma / Next.js.

## Demo Talk Track

1. Start from the industry radar overview to show cross-industry screening.
2. Pick one industry such as Semiconductor, AI Compute, CPO / Optical Module, or Gold.
3. Open the single-industry research page and inspect price confirmation, news catalysts, risk signals, and the industry chain.
4. Explain that the single-industry Markdown export is a raw context/evidence package.
5. Open the research summary / AI input package page.
6. Show the V5.3 data status bar, then the V5.1 local summary.
7. Generate the V5.2 ChatGPT research prompt and explain that this is the AI review input package, not an automatically generated investment conclusion.

Recommended screenshot pages:

- Industry Radar Overview: cross-industry screening and overview cards.
- Single Industry Research: complete context, price confirmation, news catalysts, and risk signals.
- AI Research Input Package: data status, local summary, and ChatGPT prompt export.

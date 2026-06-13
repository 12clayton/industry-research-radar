Industry Research Radar

行业研究雷达是一个独立的本地 Streamlit 研究工具，用于行业趋势初筛、催化剂跟踪、新闻热度观察和行业数据质量审计。项目只输出研究观察、结构解释和风险提示，不生成交易指令。
 Version History / 版本演进

项目从 V1 行业搜索原型逐步演进到 V5.3 数据状态栏。详细版本路线见：

[docs/version_history.md](docs/version_history.md)

核心能力

行业趋势初筛：通过行业名称、主题词或中英文 alias 搜索行业框架。
行业雷达总览：横向比较行业状态、价格确认、新闻热度、催化剂和风险信号。
催化剂跟踪：维护 V4/V5 相关行业催化框架、热度方向和事件线索。
新闻观察：使用公开 Yahoo Finance / yfinance 新闻作为轻量证据层，并保留本地缓存目录。
审计脚本：检查行业字段完整性、语义质量、新闻配置、催化剂框架和导出文本边界。

项目结构

```text
industry-research-radar/
  industry_app.py
  src/industry_*.py
  scripts/audit_industry_*.py
  scripts/audit_all_industry_catalyst_semantics.py
  docs/
  data/
    industry_radar/.gitkeep
    industry_news/.gitkeep
    industry_catalyst/.gitkeep
```

## 本地运行

```powershell
pip install -r requirements.txt
streamlit run industry_app.py
```

审计检查

```powershell
python scripts/audit_industry_trend_data.py
python scripts/audit_industry_catalyst_data.py
python scripts/audit_industry_news_provider.py
python scripts/audit_industry_semantic_quality.py
```

数据与隐私

`data/` 下的 CSV 和 JSON 是运行缓存或本地快照，默认不提交。公开仓库只保留 `.gitkeep`，避免把真实缓存、报告、日志、备份或私有配置带入 GitHub。

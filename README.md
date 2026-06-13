  Industry Research Radar / 行业研究雷达

`industry-research-radar` 是一个本地 Streamlit 行业研究工具，用于行业趋势初筛、市场价格确认、新闻催化跟踪、催化框架复核、本地研究摘要和 ChatGPT 研究输入包导出。

本项目从原 `Global_QDII_Risk_Monitor` 项目中拆分出来，当前仓库专注于行业研究雷达，不包含原 dashboard 的持仓、定投、每日报告和私有配置。

---

  Core Features / 核心功能

   1. 单行业趋势分析

支持按行业名称搜索并查看：

 行业阶段
 趋势评分
 价格确认
 新闻热度
 透支风险
 核心驱动因素
 子行业
 风险信号
 产业链地图

---

   2. 行业雷达总览

支持多行业横向比较，用于快速观察：

 哪些行业趋势更强
 哪些行业新闻热度更高
 哪些行业可能存在高热分化
 哪些行业需要人工复核

---

   3. 市场价格确认

系统使用市场价格代理数据对行业趋势进行辅助验证，包括：

 MA20 / MA50 / MA200
 1M / 3M / 6M 表现
 相对强弱
 市场价格确认分

目标是避免只看概念热度，而是加入市场行为验证。

---

   4. 新闻催化跟踪

系统支持缓存和观察行业相关新闻，包括：

 Yahoo Finance
 Google News RSS
 新闻相关性判断
 high / medium / low relevance 分类
 最新新闻时间
 最近 7 天相关新闻数量

---

   5. 催化框架与动态快照

系统维护本地行业催化框架，并通过新闻证据进行动态复核，包括：

 催化事件
 动态催化快照
 当前活跃催化主题
 新出现催化主题
 降温催化线索
 证据强度
 框架复核建议

---

   6. V5.1 本地研究摘要

V5.1 是本地规则版研究摘要生成器，不是严格意义上的 AI Agent。

它基于趋势评分、价格确认、新闻热度、催化框架和风险模板，生成系统初判，包括：

 趋势健康度
 健康度解读
 价格与新闻是否共振
 共振解读
 当前催化主线
 风险信号
 待验证问题
 人工复核建议

---

   7. V5.2 AI 研究输入包

V5.2 不接 OpenAI API，不自动生成 AI 结论。

它负责生成可复制给 ChatGPT 的结构化研究 Prompt，包括：

 V5.1 本地摘要
 高相关新闻
 当前催化主线
 风险信号
 待验证问题
 人工复核建议
 数据来源说明

目标是让网站负责整理材料，让 ChatGPT 负责深度分析和追问。

---

   8. V5.3 数据状态栏

V5.3 增加当前数据状态显示，用于判断摘要基于什么时间的数据生成，包括：

 本地摘要生成时间
 市场价格状态
 新闻缓存状态
 最新新闻时间
 最近 7 天相关新闻数
 催化快照更新时间
 催化状态
 证据强度
 数据新鲜度

---

  Project Structure / 项目结构

```text
industry-research-radar/
  industry_app.py
  requirements.txt
  README.md
  docs/
    project_overview.md
    system_architecture.md
    roadmap.md
    demo_guide.md
    resume_pitch.md
    version_history.md
  src/
    industry_*.py
  scripts/
    audit_industry_*.py
    audit_all_industry_catalyst_semantics.py
  data/
    industry_radar/.gitkeep
    industry_news/.gitkeep
    industry_catalyst/.gitkeep
```

---

  Run Locally / 本地运行

安装依赖：

```powershell
pip install -r requirements.txt
```

启动网站：

```powershell
streamlit run industry_app.py
```

或指定端口：

```powershell
python -m streamlit run industry_app.py --server.port 8503
```

浏览器打开：

```text
http://localhost:8503
```

---

  Audit / 审计脚本

基础语法检查：

```powershell
python -m compileall industry_app.py src scripts
```

催化事件语义检查：

```powershell
python scripts/audit_industry_catalyst_event_semantics.py
```

全行业催化语义检查：

```powershell
python scripts/audit_all_industry_catalyst_semantics.py
```

新闻 provider 检查：

```powershell
python scripts/audit_industry_news_provider.py
```

---

  Data & Privacy / 数据与隐私

本仓库不会提交真实运行缓存和私有配置。

`.gitignore` 默认排除：

 `.env`
 `.streamlit/secrets.toml`
 `__pycache__/`
 `*.pyc`
 `data/**/*.csv`
 `data/**/*.json`
 `reports/`
 `logs/`
 `backups/`

`data/` 目录中只保留 `.gitkeep`，用于保留目录结构。

---

  Version History / 版本演进

项目从 V1 行业搜索原型逐步演进到 V5.3 数据状态栏。详细版本路线见：

[docs/version_history.md](docs/version_history.md)

---

  Disclaimer / 免责声明

本项目仅用于行业趋势研究、数据整理和研究复核，不提供直接交易指令，不构成投资建议。

所有系统输出均应作为研究辅助材料，最终判断需要人工复核。

<div align="center">

# 🕵️ Intel Briefing - AI 情报聚合引擎

**每天 5 分钟，掌握全球科技圈正在发生什么。**

从 12+ 数据源自动抓取、翻译、分析情报，生成一份中文日报。

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-30%20passed-brightgreen)](tests/)
[![GitHub Stars](https://img.shields.io/github/stars/77AutumN/Intel_Briefing?style=social)](https://github.com/77AutumN/Intel_Briefing)

</div>

---

## 🤔 这是什么？

一个**情报采集+分析引擎**，自动从全网科技信息源抓取数据，用 Gemini 翻译和摘要，生成一份结构化的中文报告。

**适合谁用？**
- 想每天快速了解科技圈动态的开发者
- 做竞品分析、行业研究的产品经理
- 想找灵感和机会的独立开发者 / 创业者

## ✨ 功能概览

### 📊 情报日报
从 12+ 数据源抓取最新信息，生成包含 7 大板块的中文日报：

| 板块 | 数据源 | 你能看到什么 |
|:--|:--|:--|
| 🛠️ 技术趋势 | Hacker News, GitHub Trending | 今天程序员们在聊什么 |
| 💰 资本动向 | 36Kr, WallStreetCN | 谁在融资、谁在并购 |
| 📚 学术前沿 | ArXiv AI/ML, **HF Daily Papers** | 最新 AI 论文，按社区热度排序 |
| 🚀 产品精选 | Product Hunt | 今天发布了什么新产品 |
| 💬 社区热点 | V2EX | 中文开发者社区在讨论什么 |
| 🐦 社交热议 | X (Twitter) via Grok | Twitter 上的技术热话题 |
| 📖 深度洞察 | HN Top Blogs, TechCrunch, MIT TR | AI 巨头工程博客全文分析 |

---

## 🚀 快速开始

### 1. 克隆 & 安装

```bash
git clone https://github.com/77AutumN/Intel_Briefing.git
cd Intel_Briefing
pip install -e .       # 安装为可编辑包（解决所有 import 路径）
```

### 2. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env，填入你自己的 API Key
```

### 3. 运行

```bash
python cli.py              # 生成完整日报
python cli.py --test       # 测试模式（每个源只抓 1 条）
```

报告保存在 `reports/daily_briefings/` 目录下。

### 4. 代理配置（可选）

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

> [!IMPORTANT]
> `httpx` 默认不支持 SOCKS 代理。如果你的代理只提供 SOCKS 端口，需要额外安装：
> ```bash
> pip install httpx[socks]
> ```

---

## 🔑 API 密钥说明

| 密钥 | 用途 | 是否必需 | 费用 |
|:--|:--|:--|:--|
| `GITHUB_TOKEN` | GitHub Trending (GraphQL API) | **必需** | ✅ [免费申请 PAT](https://github.com/settings/tokens) |
| `XAI_API_KEY` | Grok API (X/Twitter 舆情 + PH fallback) | 推荐 | 每月 $25 免费额度 ([申请](https://console.x.ai/)) |
| `PRODUCTHUNT_TOKEN` | Product Hunt 数据 | 可选 | ✅ [免费申请](https://www.producthunt.com/v2/oauth/applications) |
| `GEMINI_API_KEY` | Google Gemini (中文翻译+摘要) | 可选 | ✅ 免费额度充足 ([申请](https://aistudio.google.com/apikey)) |

> ⚠️ **最低要求：拿到 `GITHUB_TOKEN` 就能跑基础日报。** 没有其他 Key 时对应功能会优雅降级（跳过而非崩溃）。

---

## 📁 项目结构

> [!NOTE]
> 数据是从两个地方抓的，你不用关心这个区别——日报里看到的内容都一样。
> - 一批"老牌"信息源（HN、GitHub、36Kr、V2EX、WallStreetCN）走 `src/external/fetch_news.py`
> - 其余每个源各有一个独立的"传感器"文件，放在 `src/sensors/` 里
>
> 这是项目早期演进留下的两套写法，功能上都正常，未来会慢慢合并成一套。

```
Intel_Briefing/
├── cli.py                      # 🎯 主入口
├── pyproject.toml              # 包配置 (pip install -e .)
├── src/
│   ├── config.py               # 统一配置层 (IntelConfig singleton)
│   ├── intel_collector.py      # 情报收集器 (并发调度 + 去重)
│   ├── report_generator.py     # 报告渲染器 (含防幻觉逻辑)
│   ├── sensors/                # Tier 2: 独立数据源传感器
│   │   ├── arxiv_ai.py         # ArXiv AI/ML 论文
│   │   ├── hf_daily_papers.py  # HuggingFace Daily Papers
│   │   ├── hn_blogs.py         # AI 巨头工程博客 RSS (15 源 + 动态 OPML)
│   │   ├── product_hunt.py     # Product Hunt (含 Grok fallback)
│   │   ├── techcrunch_rss.py   # TechCrunch RSS
│   │   ├── mit_tech_review.py  # MIT Technology Review
│   │   ├── x_grok_sensor.py    # X/Twitter via Grok API
│   │   └── horizon.py          # 机会雷达 (独立功能，见下方 scripts/)
│   ├── utils/
│   │   ├── gemini_translator.py # Gemini 中文翻译 + 摘要
│   │   ├── generate_summaries.py # PWA 预烘焙摘要
│   │   ├── jina_reader.py      # 网页全文提取 (含 DDG fallback)
│   │   └── verifier.py         # 链接有效性验证
│   └── external/
│       └── fetch_news.py       # Tier 1: HN/GitHub/36Kr/V2EX/WS 聚合器
├── scripts/                    # 🧰 附带的小工具 (与日报独立)
│   ├── horizon_report.py       # 机会雷达：扫描跨领域的新机会
│   ├── condense_month.py       # 把一个月的日报浓缩成月报
│   └── recurrence_scan.py      # 找出反复出现的热点话题
├── tests/                      # 30 tests (import/行为/降级)
│   ├── test_import_smoke.py    # 12 模块 import 验证
│   ├── test_anti_hallucination.py  # 防幻觉行为测试
│   ├── test_graceful_degradation.py # 优雅降级测试
│   └── test_core.py            # 核心功能测试
├── reports/                    # 📄 生成的报告目录 (gitignored)
└── .env.example                # API 密钥模板
```

---

## ⚙️ 配置

所有配置通过 `src/config.py` 的 `IntelConfig` 单例管理。优先级：环境变量 > `.env` > 默认值。

关键配置项：

| 变量 | 默认值 | 说明 |
|:--|:--|:--|
| `GEMINI_MODEL` | `gemini-2.0-flash` | 翻译/摘要用的 Gemini 模型 |
| `XAI_MODEL` | `x-ai/grok-4-fast` | Grok API 模型 |
| `FETCH_TIMEOUT` | `15` | 网络请求超时 (秒) |
| `LIMIT_PER_SOURCE` | `10` | 每个源抓取上限 |
| `CONTENT_TRUNCATE_LIMIT` | `3000` | 内容截断字符数 |

---

## 🧪 测试

```bash
pip install -e .      # 首次需要
pytest tests/ -v      # 30 tests, <1s
```

测试覆盖三个维度：
- **Import Smoke**: 所有 12 个模块可独立导入
- **Anti-Hallucination**: Grok fallback 产生的猜测 URL 不会作为可点击链接进入报告
- **Graceful Degradation**: 缺失 API key 或空数据时系统不崩溃

---

## 🛡️ 防幻觉机制

当 Product Hunt API 不可用时，系统会 fallback 到 Grok 推断产品数据。此时产生的 URL 是**猜测的 slug**，不是真实链接。

**处理方式**：
- Grok fallback 产品在报告中标记为 `⚠️ 链接未验证 (AI 推断)`
- 不渲染为可点击的 markdown 链接
- 提供 Google 搜索验证链接供人工核实

---

## 🤖 GitHub Actions 自动化

项目自带 `.github/workflows/daily-report.yml`，配置好 Secrets 后每天 UTC 23:51（北京 07:51）自动生成日报。

> **可选投递到前端仓库**：如果你有自己的 PWA / 前端仓库，设置仓库变量 `PWA_REPO`（如 `your-name/your-pwa-repo`）和 Secret `PWA_DEPLOY_TOKEN`，workflow 会自动把日报推送过去；不设置则跳过该步骤，不影响日报生成。

---

## 📝 已知限制

- `fetch_news.py` 和 `sensors/` 两套采集架构并存（Phase 2 收口中）
- 传感器的 `print()` 输出尚未统一到 `logging`（Phase 2 计划）
- Windows 下部分传感器独立运行可能遇到 GBK 编码问题（CI 在 Ubuntu 上无此问题）

---

## 📄 License

MIT — 随便用，改了也不用告诉我。

---

<div align="center">

**如果觉得有用，给个 ⭐ 就是最大的支持。**

</div>

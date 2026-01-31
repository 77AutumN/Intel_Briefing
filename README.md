# 🕵️ Intel Briefing - AI 情报聚合系统

<p align="center">
  <strong>🤖 用 AI 帮你每天追踪 Tech 热点、产品趋势、学术前沿</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Powered%20by-Antigravity-purple" alt="Antigravity">
</p>

---

## ✨ 功能特性

- 📰 **Hacker News** - 每日热门技术讨论
- 🚀 **Product Hunt** - 最新产品发布追踪
- 📚 **arXiv** - AI/ML 前沿论文速递
- 🐙 **GitHub Trending** - 热门开源项目
- 🧩 **Chrome 扩展商店** - 新兴插件雷达
- 💬 **V2EX** - 中文开发者社区动态
- 📕 **小红书** - 趋势话题采集
- 🐦 **X (Twitter)** - 通过 Grok API 分析舆情

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/Intel_Briefing.git
cd Intel_Briefing
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

**需要的 API Key：**
| Key | 用途 | 获取地址 |
|-----|------|----------|
| `PRODUCTHUNT_TOKEN` | Product Hunt 数据 | [PH Developer](https://www.producthunt.com/v2/oauth/applications) |
| `XAI_API_KEY` | X/Grok 舆情分析 | [xAI Console](https://console.x.ai/) |
| `GITHUB_TOKEN` | GitHub Trending | [GitHub Settings](https://github.com/settings/tokens) |

### 4. 运行

```bash
# 获取每日情报简报
python run_mission.py

# 或手动运行单个模块
python -c "from src.sensors.hacker_news import fetch; print(fetch())"
```

---

## 🏗️ 三司架构

| 部门 | 入口脚本 | 输出目录 | 职责 |
|------|----------|----------|------|
| **战略部** | `run_mission.py` | `reports/daily_briefings/` | 每日晨报 |
| **战术部** | `run_bounty_hunter.py` | `reports/tactical/` | Hit List |
| **Web3部** | `run_alpha_radar.py` | `reports/web3/` | Alpha Leak |

---

## 📂 项目结构

```
Intel_Briefing/
├── src/sensors/          # 数据采集模块
├── reports/              # 生成的报告 (git ignored)
├── .agent/               # Antigravity Agent 配置
├── run_mission.py        # 每日情报主入口
├── run_bounty_hunter.py  # 战术狩猎
├── run_alpha_radar.py    # Web3 Alpha 雷达
├── .env.example          # 环境变量模板
└── SKILL.md              # Agent 技能说明
```

---

## 🔧 传感器列表

| 模块 | 数据源 | 更新频率 |
|------|--------|----------|
| `hacker_news.py` | Hacker News | 每日 |
| `product_hunt.py` | Product Hunt | 每日 |
| `arxiv_ai.py` | arXiv AI/ML | 每日 |
| `github_trending.py` | GitHub | 每日 |
| `chrome_radar.py` | Chrome 商店 | 每周 |
| `v2ex_radar.py` | V2EX | 每日 |
| `xhs_radar.py` | 小红书 | 每日 |
| `x_grok_sensor.py` | X (Grok) | 每日 |

---

## 🤝 与 Antigravity Agent 配合使用

本项目设计为 [Google Antigravity](https://idx.dev/antigravity) 的 **Skill**，可以直接对 Agent 说：

```
"给我今日报告"
"看一下今天的晨报，帮我找赚钱机会"
"/daily-report"
```

---

## 📄 License

MIT License - 自由使用，欢迎 PR！

---

<p align="center">
  <strong>⭐ 如果觉得有用，给个 Star 吧！</strong>
</p>

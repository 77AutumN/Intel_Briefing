---
name: intel-briefing
description: 每日商业情报简报生成器，聚合 HN/GitHub/36Kr/ArXiv/ProductHunt 等多源数据，生成结构化 Markdown 报告
metadata:
  openclaw:
    requires:
      bins:
        - python3
      env: []
    config:
      optionalEnv:
        - GITHUB_TOKEN
        - XAI_API_KEY
        - PRODUCTHUNT_TOKEN
      stateDir: reports/daily_briefings
      example: |
        # 可选配置，用于增强数据源
        # GITHUB_TOKEN: 提升 GitHub API 限额
        # XAI_API_KEY: 启用 X/Twitter 舆情分析
        # PRODUCTHUNT_TOKEN: 获取 Product Hunt 数据
license: MIT
tags:
  - intelligence
  - news
  - aggregator
  - briefing
  - tech
---

# Intel Briefing - 情报简报生成器

每日自动聚合全球科技、商业、学术情报，生成结构化简报。

## 使用时机

当用户需要以下内容时激活此技能：
- 每日科技/商业情报简报
- 技术趋势追踪（Hacker News、GitHub Trending）
- 资本动向监控（36Kr、华尔街见闻）
- 学术前沿速递（ArXiv AI/ML 论文）
- 新产品发现（Product Hunt）
- 社交热议分析（X/Twitter）

触发词示例：
- "生成今日情报简报"
- "帮我看看今天科技圈有什么新闻"
- "今日技术趋势"
- "morning briefing"
- "intel report"

## 数据源

| 板块 | 数据源 | 说明 |
|------|--------|------|
| 技术趋势 | Hacker News, GitHub Trending | 开发者社区热点 |
| 资本动向 | 36Kr, 华尔街见闻 | 投融资、市场动态 |
| 学术前沿 | ArXiv | AI/ML 最新论文 |
| 产品精选 | Product Hunt | 每日新产品 |
| 社交热议 | X (Twitter) | 科技圈讨论 |
| 社区热点 | V2EX | 中文开发者社区 |

## 操作步骤

1. **确认用户需求**
   - 默认生成当日简报
   - 如用户指定天数（如"过去7天"），调整 `days` 参数

2. **执行数据采集**
   ```bash
   cd <skill_directory>
   python3 scripts/openclaw_handler.py --days 1
   ```

3. **读取生成的报告**
   - 报告保存在 `reports/daily_briefings/` 目录
   - 文件名格式：`Morning_Report_YYYY-MM-DD.md`

4. **返回报告内容**
   - 将 Markdown 报告内容返回给用户
   - 如果用户配置了推送，OpenClaw 会自动处理

5. **可选：生成 Executive Summary**
   - 如果报告内容较长，可以请求 OpenClaw 生成摘要
   - 提示词："请用 3-5 句话概括这份报告的要点"

## 输出格式

报告为 Markdown 格式，包含以下板块（仅显示有数据的板块）：

```markdown
# 🌐 全球情报日报 (Global Intel Briefing)
**日期:** 2026-02-13
**数据源:** HN, GitHub, 36Kr, ArXiv, PH

---

## 🛠️ 技术趋势 (Tech Trends)
### 1. [标题](链接)
📍 分类 | 🔥 热度 | 🕒 时间

## 💰 资本动向 (Capital Flow)
...

## 📚 学术前沿 (Research)
...

## 💎 产品精选 (Product Gems)
...
```

## 配置说明

此技能无需强制配置即可运行。以下环境变量可增强功能：

| 变量 | 用途 | 必需 |
|------|------|------|
| `GITHUB_TOKEN` | 提升 GitHub API 限额 | 否 |
| `XAI_API_KEY` | 启用 X/Twitter 分析 | 否 |
| `PRODUCTHUNT_TOKEN` | 获取 Product Hunt 数据 | 否 |

## 示例对话

**用户**: 帮我生成今日情报简报
**代理**: 好的，正在为您采集全球科技情报...
*(执行 `python3 scripts/openclaw_handler.py --days 1`)*
**代理**: 简报已生成，以下是今日要点：
[返回 Markdown 报告内容]

**用户**: 生成过去一周的情报汇总
**代理**: 好的，正在生成周报...
*(执行 `python3 scripts/openclaw_handler.py --days 7`)*

## 注意事项

- 首次运行需要安装依赖：`pip install -r requirements.txt`
- 部分数据源可能因网络原因采集失败，报告会自动跳过无数据的板块
- 报告生成可能需要 30-60 秒，取决于数据源响应速度

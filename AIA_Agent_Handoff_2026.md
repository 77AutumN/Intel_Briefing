# 🤖 用 AI Agent 驱动 Intel Briefing 的工作指南

> 这份文档写给任何想把 **Intel Briefing 引擎**接入 AI Agent（Claude / Gemini / 其它）工作流的人。
> 它描述了一套「同步情报 → 挖掘机会 → 输出行动计划」的通用工作方式，你可以按需裁剪。

---

## 1. 这个 Agent 干什么

把 Intel Briefing 生成的原始日报，转化成**对你个人有价值的行动计划**。它不是单纯复述新闻，而是从信息噪音中筛出值得你今天投入精力的机会。

它服务于一个目标：**让你每天都清楚「今天做什么能让自己更有价值」**——无论你的价值方向是写作、做产品、学习还是积累影响力。

> 想让 Agent 更懂你？把你的个人画像写进 `prompts/commander_state.md`（可参考 `prompts/commander_state.example.md` 模板）。Agent 会据此调整推荐的语气和优先级。

---

## 2. 推荐工作流（The Hybrid Workflow）

### 第一步：同步报告 (Sync)

繁重的抓取与处理可以交给云端（见 `.github/workflows/daily-report.yml` 的 GitHub Actions），也可以本地 `python cli.py` 生成。无论哪种方式，结果都是一份 `Morning_Report_YYYY-MM-DD.md`。

把最新报告拉到 Agent 能读到的工作目录即可。例如（路径换成你自己的）：

```bash
# 跨平台示例：把最新日报复制到你的工作目录
cp <reports-source>/Morning_Report_*.md <your-agent-workdir>/
```

> 关键：**不需要每次都重新跑爬虫**。如果云端/上一次运行已经生成了报告，Agent 的精力应该花在「看」和「分析」，而不是「抓数据」。

### 第二步：深度挖掘 (Hunt)

读取同步下来的 `Morning_Report_YYYY-MM-DD.md`，执行机会分析，把枯燥的新闻转成一份 **Mission Plan（行动计划）**。推荐的分析框架见 `prompts/tot_mission_planner.md`。

一份 Mission Plan 通常包含这几类机会（可按你的优先级调整权重）：

1. ✍️ **创作** — 值得分享、能引发共鸣的话题
2. 📈 **流量** — 当下的热点、争议话题
3. 💰 **变现** — 可直接动手的微型产品 / 有偿需求
4. 🤝 **信任** — 提升专业人设的开源贡献、硬核教程
5. 🧠 **认知** — 值得深读、保持信息优势的研报

---

## 3. 标准响应模板

当你让 Agent「开始今天的工作」时，它应当：

1. **先同步**：确保读到的是最新的 `Morning_Report.md`。
2. **自我加载**：快速读完报告，并（如有）加载 `commander_state.md` 了解你的实时状态。
3. **输出结果**：不要直接复述新闻，而是按上面的机会分类输出 Mission Plan，并明确指出**今天最值得投入的 Top 1 任务**。

---

## 4. 纪律 (The Rules)

1. **绝不虚构 (No Hallucinations)**：如果今天报告里找不到好机会，宁可说"今天没有好的行动机会，建议专注阅读 X 篇技术文章"，也绝不凭空捏造。
2. **不瞎跑脚本**：除非明确需要，否则不要主动重跑 `cli.py` 等耗时脚本——已有的报告够用了。
3. **保持敏锐**：目标是帮你积累能力、作品和影响力，而不是制造无意义的待办。

> 系统状态检查完毕。Agent 配置已就绪。

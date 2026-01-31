---
description: 生成情报简报 (Daily/Weekly Intelligence Report)
---

# 情报简报生成器

当用户请求生成情报报告时，按以下步骤执行：

## 识别请求类型

用户可能会说：
- "给我今日报告" / "今日情报" / "daily report" → 执行 **日报模式**
- "给我周报" / "这周报告" / "past 7 days" → 执行 **周报模式**
- "跑一下战术" / "找现金" / "bounty" → 只执行 **战术司** (Hit List)
- "跑一下 Alpha" / "Web3 报告" → 只执行 **工具司** (Alpha Leak)

---

## 日报模式 (Daily)

// turbo-all

1. 运行战略情报 (Morning Briefing):
```powershell
python D:\Intel_Briefing\run_mission.py
```

2. 运行战术情报 (Hit List):
```powershell
python D:\Intel_Briefing\run_bounty_hunter.py
```

3. 运行 Web3 情报 (Alpha Leak):
```powershell
python D:\Intel_Briefing\run_alpha_radar.py
```

4. 汇报生成的文件路径给用户：
   - `D:\Intel_Briefing\reports\daily_briefings\Morning_Report_*.md`
   - `D:\Intel_Briefing\reports\tactical\Hit_List_*.md`
   - `D:\Intel_Briefing\reports\web3\Alpha_Leak_*.md`

5. **[可选] 生成链接摘要 (Link Digest):**
   如果用户想要预览链接内容而不逐个点击，使用 `read_url_content` 工具抓取报告中的外链，然后生成一份 `*_Digest.md` 摘要文件。
   - 目标: Tech Trends (HN), Research (ArXiv)
   - 跳过: 付费墙(Reuters)、动态页面(YouTube/PH)、中文快讯(36Kr/V2EX)
   - 输出: `D:\Intel_Briefing\reports\daily_briefings\*_Digest.md`

---

## 周报模式 (Weekly / Past N Days)

// turbo-all

1. 运行战略情报 (扩展时间范围):
```powershell
python D:\Intel_Briefing\run_mission.py 7
```
> 注意：`7` 是天数参数，可以改成用户指定的天数。

2. 运行战术情报 (扩展时间范围):
```powershell
python D:\Intel_Briefing\run_bounty_hunter.py --days 7
```

3. 运行 Web3 情报:
```powershell
python D:\Intel_Briefing\run_alpha_radar.py
```

4. 汇报生成的文件路径给用户。

5. **[可选] 生成链接摘要 (Link Digest):**
   同日报模式，使用 `read_url_content` 抓取外链并生成摘要。

---

## 完成后

告诉用户报告已生成，并提供文件链接。

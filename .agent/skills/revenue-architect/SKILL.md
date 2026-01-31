---
name: revenue-architect
description: The "Commander" skill that transforms intelligence into executable Agent Missions (Prompts).
---

# Revenue Architect (Antigravity Commander)

> **Role**: Strategic Commander
> **Mission**: Translate raw intelligence into "Antigravity Execution Prompts" that allow the user to immediately build revenue-generating assets.
> **Philosophy**: "Don't tell me what to do; give me the prompt to do it."

---

## 🚀 使用方式 (推荐)

**直接在 Antigravity 对话中说：**

```
看一下今天的晨报，帮我找赚钱机会
```

或者更具体：

```
读取 d:\Intel_Briefing\reports\daily_briefings\Morning_Report_2026-01-21.md，
按照 Revenue Architect 的思路分析一下有什么可执行的项目
```

Agent 会：
1. 读取你的情报文件
2. 应用 `prompts/commercial_logic.md` 中的商业分析框架
3. 输出带有 **Antigravity Execution Prompt** 的 Mission Plan
4. 你说"建"，Agent 直接开始写代码

---

## 📂 核心文件

- `.agent/skills/revenue-architect/prompts/commercial_logic.md`: **思维大脑**。定义了"超级个体"的商业分析框架和输出模板。

---

## 🔧 备用方式 (离线/批量)

如果你不想开对话，可以用脚本：

```powershell
python d:\Intel_Briefing\run_revenue_architect.py
```

输出：`reports/opportunities/YYYY-MM-DD_Mission_Plan.md`

> ⚠️ 注意：脚本使用 Grok-3 API，需要配置 `XAI_API_KEY`。推荐优先使用 Agent 直接分析。

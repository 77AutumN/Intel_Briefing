---
name: aia-command-center
description: 反重力情报局 (A.I.A.) 的作战控制台。
---

# A.I.A. 指挥中心 (战场 Battlefield)

> **角色**: 情报行动指挥官
> **任务**: 执行每日情报收集任务并生成商业报告。
> **位置**: 战场 (`D:\Intel_Briefing`)

---

## 🕹️ 作战指令

你现在处于 **执行环境** 中。使用以下指令驱动情报局工作：

### 🌞 每日例行 (Daily Routine)
*   **"给我今日报告"** / **"Run Daily Briefing"**
    *   **动作**: 运行全套流程 (战略 + 战术 + Web3)。
    *   **细节**: 执行 `.agent/workflows/daily-report.md` 工作流。

### 🌐 全球情报 (Unified Intel V2)
*   **"Run Intel"** / **"给我今日情报"**
    *   **动作**: `python fetch_unified_intel.py`
    *   **来源**: HN, GitHub, 36Kr, WallStreetCN, V2EX, PH, ArXiv, X (Grok), XHS.
    *   **输出**: `reports/daily_briefings/Morning_Report_YYYY-MM-DD.md`

### 🗓️ 每周情报 (Weekly Intel)
*   **"Run Weekly"** / **"给我本周情报"**
    *   **动作**: `python fetch_unified_intel.py --limit 30` (抓取更多数据) + 人工/Agent 综合分析
    *   **说明**: 目前通过增加抓取量覆盖一周热点。

### 🧠 收入架构师 (Revenue Architect)
*   **"找赚钱机会"** / **"Find Money"**
    *   **动作**: `python run_revenue_architect.py`
    *   **逻辑**: 读取最新的 Morning Report → 应用商业分析框架 → 生成 Mission Plan
    *   **输出**: `reports/opportunities/YYYY-MM-DD_Mission_Plan.md`

### 💰 战术部 (Tactical Dept - 找现金)
*   **"Run Tactical"** / **"找现金"** / **"Bounty Hunter"**
    *   **动作**: `python run_bounty_hunter.py`
    *   **输出**: `reports/tactical/Hit_List_YYYY-MM-DD.md`

### ⛏️ Web3 部 (Web3 Dept - 捡金矿)
*   **"Run Alpha"** / **"捡金矿"**
    *   **动作**: `python run_alpha_radar.py`
    *   **输出**: `reports/web3/Alpha_Leak_YYYY-MM-DD.md`

### 🧠 收入架构师 (Revenue Architect - 情报→项目)
*   **"看一下今天的晨报，帮我找赚钱机会"**
    *   **动作**: Agent 直接读取三司报告 + 应用收入架构师思维框架
    *   **输出**: `reports/opportunities/YYYY-MM-DD_Mission_Plan.md`
    *   **注意**: 生成的 Mission Plan 包含可直接执行的 Antigravity Prompt

---

## 📂 文件系统
*   **Reports (报告)**: 所有情报存储在 `reports/` 目录下。
*   **Manual (手册)**: 参见 `AIA_Field_Manual.md` 了解方法论 (建议阅读)。
*   **Source (源码)**: 核心逻辑位于 `src/sensors/` (请勿在此编辑; 请在军火库 `d:\Skills` 中编辑并重新部署)。

<div align="center">

# 🕵️ Intel Briefing — Your Personal Intelligence Officer

[中文](README.md) | **English**

**Don't just doomscroll. Turn each day's global signals — including the ones outside your filter bubble — into an answer to "what should I do today?"**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-30%20passed-brightgreen)](tests/)
[![GitHub Stars](https://img.shields.io/github/stars/77AutumN/Intel_Briefing?style=social)](https://github.com/77AutumN/Intel_Briefing)

</div>

---

## 🤔 What is this?

A **personal intelligence system**. Every day it does three things for you:

1. 📡 **Gather** — Automatically collect, translate, and summarize from 10+ global tech/business sources into a daily briefing.
2. 🔭 **Break the bubble** — A dedicated "cross-domain radar" deliberately feeds you signals from *outside* tech — science, philosophy, geopolitics, design — with zero overlap with the tech sources above, so your view doesn't keep narrowing.
3. 🚀 **Find ideas** — Feed both into a reasoning framework that distills them into a daily **Mission Plan**, answering the question that actually matters:

> 🧭 **What can I do today to become more valuable?**
> And "valuable" isn't confined to your current lane — cognition that crosses boundaries is the ultimate leverage.

**How it differs from a plain news aggregator:** an aggregator gives you *more information*; this gives you *a wider field of view + one actionable answer*.

**Who is it for?**
- Developers who want a fast daily read on the world — without sliding into a filter bubble
- Product managers doing competitive / industry research
- Indie hackers / creators looking for inspiration and opportunities in the daily signal

---

## ✨ Three Layers

### 📊 Layer 1: The Daily Briefing
Pulls from 10+ sources into a 7-section briefing:

| Section | Sources | What you get |
|:--|:--|:--|
| 🛠️ Tech Trends | Hacker News, GitHub Trending | What developers are talking about today |
| 💰 Capital Flow | 36Kr, WallStreetCN | Who's raising, who's acquiring |
| 📚 Research Frontier | ArXiv AI/ML, **HF Daily Papers** | Latest AI papers, ranked by community heat |
| 🚀 Product Picks | Product Hunt | What launched today |
| 💬 Community | V2EX | What the Chinese dev community is discussing |
| 🐦 Social Buzz | X (Twitter) via Grok | Hot technical topics on Twitter |
| 📖 Deep Insights | HN Top Blogs, TechCrunch, MIT TR | Full-text analysis of top engineering blogs |

### 🔭 Layer 2: Horizon — the Anti-Filter-Bubble Radar
The briefing covers the tech / AI / business vertical. But your cognitive boundary shouldn't be limited by the boundary of your data sources.

Horizon is a standalone "cross-domain cognitive radar" that **deliberately pulls only from outside tech**, spanning 5 domains across 9 sources:

| Domain | Sources |
|:--|:--|
| 🔬 Science | Nature, Quanta Magazine |
| 🧠 Philosophy & Humanities | Aeon (Essays / Philosophy) |
| 🌍 Geopolitics & Economics | Reuters, Geopolitical Futures |
| 🔀 Cross-disciplinary | Nautilus, Aeon (Science) |
| 🎨 Design & Aesthetics | Dezeen |

It has built-in "domain diversity" logic — guaranteeing at least one item per domain, so you're never drowned in a single stream.

```bash
python scripts/horizon_report.py        # run a one-off cross-domain scan
```

> Implemented in `src/sensors/horizon.py`. It's a standalone feature — **it does not get mixed into the briefing**. Instead it serves as the "bubble-breaking" input feeding the Mission Plan below.

### 🚀 Layer 3: Mission Plan — the Daily Action Plan
This is where the whole system lands. It hands "briefing + Horizon cross-domain signals" to a **Tree of Thoughts (ToT) framework**, distilling them into a daily action plan with four zones:

| Zone | What it is |
|:--|:--|
| 🔴 Strike Zone | Signals that directly make you "more valuable" → distilled into today's **Top 1 must-do** |
| 🟡 Exploration Zone | Not directly relevant, but with "cross-domain leverage" potential |
| 🔭 Horizon Zone | Cognitive jolts from outside tech, **must be non-empty** — the hard anti-bubble constraint |
| ⚪ Watch Zone | Trends not worth acting on yet, but worth keeping on the radar |

The framework lives in `prompts/tot_mission_planner.md` (a prompt you can feed straight to an LLM). Want it tailored to you? Copy `prompts/commander_state.example.md` and fill in your identity and priorities.

> ⚠️ The Mission Plan is a **prompt-driven** step: you hand the day's briefing and Horizon results, together with this prompt, to an LLM (Claude / Gemini / etc.), which generates it. It is not a one-command script.

---

## 📸 What it looks like

**① Daily briefing (excerpt)**

```markdown
# 🌐 Global Intel Briefing
**Date:** 2026-05-27

## 🛠️ Tech Trends
### 1. [Language Models Need Sleep](https://arxiv.org/abs/...)
📍 Hacker News | 🔥 84 points | 🕒 1 hour ago

## 📚 Research Frontier
### 1. MobileGym: A Verifiable Simulation Platform for Mobile GUI Agents
👤 ... | 📅 2026-05-25
```

**② Mission Plan (structure)**

```markdown
# 🚀 Mission Plan [date]

> ⚡ Today's Top 1: <the one thing to act on now> (⏱️ est. time / 🎯 value to me)

## 🔴 Strike Zone        Main quest / leverage / authentic voice / knowledge edge
## 🟡 Exploration Zone   <signal> → "this might matter to you, because…"
## 🔭 Horizon Zone       <a cognitive jolt from outside tech>   ← must be non-empty
## ⚪ Watch Zone         <trends to keep watching, no action yet>
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/77AutumN/Intel_Briefing.git
cd Intel_Briefing
pip install -e .       # editable install (fixes all import paths)
```

### 2. Configure API keys

```bash
cp .env.example .env
# edit .env and fill in your own API keys
```

### 3. Run

```bash
python cli.py                       # generate the full briefing
python cli.py --test                # test mode (1 item per source)
python scripts/horizon_report.py    # run the cross-domain Horizon scan
```

Briefings are saved under `reports/daily_briefings/`. For a daily action plan, hand the briefing + Horizon results, together with `prompts/tot_mission_planner.md`, to your LLM.

### 4. Proxy (optional)

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

> [!IMPORTANT]
> `httpx` does not support SOCKS proxies by default. If your proxy only exposes a SOCKS port, install:
> ```bash
> pip install httpx[socks]
> ```

---

## 🔑 API Keys

| Key | Purpose | Required? | Cost |
|:--|:--|:--|:--|
| `GITHUB_TOKEN` | GitHub Trending (GraphQL API) | **Required** | ✅ [free PAT](https://github.com/settings/tokens) |
| `XAI_API_KEY` | Grok API (X/Twitter buzz + PH fallback) | Recommended | $25/mo free credit ([apply](https://console.x.ai/)) |
| `PRODUCTHUNT_TOKEN` | Product Hunt data | Optional | ✅ [free](https://www.producthunt.com/v2/oauth/applications) |
| `GEMINI_API_KEY` | Google Gemini (translation + summary) | Optional | ✅ generous free tier ([apply](https://aistudio.google.com/apikey)) |

> ⚠️ **Minimum: with just `GITHUB_TOKEN` you can run a basic briefing.** Without the other keys, those features degrade gracefully (skipped, not crashed). Horizon uses public RSS — zero keys needed.

---

## 📁 Project Structure

> [!NOTE]
> Data is fetched from two places — you don't need to care about the distinction; what you see in the briefing is the same either way.
> - A batch of "legacy" sources (HN, GitHub, 36Kr, V2EX, WallStreetCN) goes through `src/external/fetch_news.py`
> - Every other source has its own standalone "sensor" file under `src/sensors/`
>
> This is two coding styles left over from the project's early evolution; both work fine, and they'll be merged over time.

```
Intel_Briefing/
├── cli.py                      # 🎯 main entry
├── pyproject.toml              # package config (pip install -e .)
├── src/
│   ├── config.py               # unified config (IntelConfig singleton)
│   ├── intel_collector.py      # collector (concurrent scheduling + dedup)
│   ├── report_generator.py     # report renderer (incl. anti-hallucination)
│   ├── sensors/                # Tier 2: standalone source sensors
│   │   ├── arxiv_ai.py         # ArXiv AI/ML papers
│   │   ├── hf_daily_papers.py  # HuggingFace Daily Papers
│   │   ├── hn_blogs.py         # top engineering blogs RSS (15 feeds + dynamic OPML)
│   │   ├── product_hunt.py     # Product Hunt (incl. Grok fallback)
│   │   ├── techcrunch_rss.py   # TechCrunch RSS
│   │   ├── mit_tech_review.py  # MIT Technology Review
│   │   ├── x_grok_sensor.py    # X/Twitter via Grok API
│   │   └── horizon.py          # 🔭 Horizon cross-domain radar (anti-bubble, see scripts/)
│   ├── utils/
│   │   ├── gemini_translator.py # Gemini translation + summary
│   │   ├── generate_summaries.py # PWA pre-baked summaries
│   │   ├── jina_reader.py      # full-text extraction (incl. DDG fallback)
│   │   └── verifier.py         # link validity check
│   └── external/
│       └── fetch_news.py       # Tier 1: HN/GitHub/36Kr/V2EX/WS aggregator
├── prompts/                    # 🧠 analysis-framework prompt templates
│   ├── tot_mission_planner.md  # Mission Plan Tree-of-Thoughts framework
│   └── commander_state.example.md # personalization template (copy & fill in)
├── scripts/                    # 🧰 bundled tools (independent of the briefing)
│   ├── horizon_report.py       # Horizon radar: scan cross-domain signals
│   ├── condense_month.py       # condense a month of briefings into a monthly report
│   └── recurrence_scan.py      # surface recurring hot topics
├── tests/                      # 30 tests (import/behavior/degradation)
│   ├── test_import_smoke.py    # 12-module import check
│   ├── test_anti_hallucination.py  # anti-hallucination behavior test
│   ├── test_graceful_degradation.py # graceful degradation test
│   └── test_core.py            # core functionality test
├── reports/                    # 📄 generated reports (gitignored)
└── .env.example                # API key template
```

---

## ⚙️ Configuration

All config is managed by the `IntelConfig` singleton in `src/config.py`. Priority: env var > `.env` > default.

Key settings:

| Variable | Default | Description |
|:--|:--|:--|
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model for translation/summary |
| `XAI_MODEL` | `x-ai/grok-4-fast` | Grok API model |
| `FETCH_TIMEOUT` | `15` | network request timeout (seconds) |
| `LIMIT_PER_SOURCE` | `10` | max items fetched per source |
| `CONTENT_TRUNCATE_LIMIT` | `3000` | content truncation length (chars) |

---

## 🧪 Tests

```bash
pip install -e .      # first time only
pytest tests/ -v      # 30 tests, <1s
```

Three dimensions covered:
- **Import Smoke**: all 12 modules import independently
- **Anti-Hallucination**: guessed URLs from Grok fallback never enter the report as clickable links
- **Graceful Degradation**: missing API keys or empty data never crash the system

---

## 🛡️ Anti-Hallucination

When the Product Hunt API is unavailable, the system falls back to Grok-inferred product data. The URLs it produces are **guessed slugs**, not real links.

**How it's handled:**
- Grok-fallback products are tagged `⚠️ Link unverified (AI-inferred)` in the report
- They are not rendered as clickable markdown links
- A Google search verification link is provided for manual confirmation

---

## 🤖 GitHub Actions

The project ships with `.github/workflows/daily-report.yml`. Once Secrets are configured, it generates a briefing daily at UTC 23:51 (Beijing 07:51).

> **Optional delivery to a frontend repo:** if you have your own PWA / frontend repo, set the repo variable `PWA_REPO` (e.g. `your-name/your-pwa-repo`) and the Secret `PWA_DEPLOY_TOKEN`, and the workflow will push the briefing there automatically; leave them unset to skip that step without affecting briefing generation.

---

## 📝 Known Limitations

- `fetch_news.py` and `sensors/` are two coexisting collection paths (consolidation planned, Phase 2)
- Sensor `print()` output isn't unified into `logging` yet (Phase 2)
- Some sensors may hit GBK encoding issues when run standalone on Windows (no issue on Ubuntu CI)

---

## 📄 License

MIT — use it however you like, no need to tell me if you change it.

---

<div align="center">

**If you find it useful, a ⭐ is the biggest support.**

</div>

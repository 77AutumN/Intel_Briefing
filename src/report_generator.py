#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator - 报告生成模块
负责将情报数据转换为 Markdown 报告
"""

import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Import from centralized config
try:
    from config import GEMINI_RATE_LIMIT_DELAY
except ImportError:
    try:
        from src.config import GEMINI_RATE_LIMIT_DELAY
    except ImportError:
        GEMINI_RATE_LIMIT_DELAY = 1.5

# --- Gemini Translator ---
try:
    from utils.gemini_translator import translate_to_chinese, summarize_blog_article, generate_executive_summary
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        from src.utils.gemini_translator import translate_to_chinese, summarize_blog_article, generate_executive_summary
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

# --- Jina Reader (Full Content Fetcher) ---
try:
    from utils.jina_reader import fetch_full_content
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False
    logger.info("Jina Reader not available, using RSS description only.")

if not GEMINI_AVAILABLE:
    logger.info("Gemini translator not available, using English summaries.")
    def translate_to_chinese(text, max_chars=100):
        return text[:max_chars] + "..." if len(text) > max_chars else text

    def summarize_blog_article(content, mode="brief"):
        return ""

    def generate_executive_summary(intel):
        return ""


def generate_report(intel: dict, date_str: str) -> str:
    """Generate magazine-style markdown report with executive summary and hidden empty sections."""

    # 计算活跃数据源
    active_sources = []
    if intel.get("tech_trends"):
        active_sources.append("HN")
        active_sources.append("GitHub")
    if intel.get("capital_flow"):
        active_sources.append("36Kr")
        active_sources.append("WallStreetCN")
    if intel.get("community"):
        active_sources.append("V2EX")
    if intel.get("product_gems"):
        active_sources.append("PH")
    if intel.get("research"):
        active_sources.append("ArXiv")
    if intel.get("social"):
        active_sources.append("X")
    if intel.get("insights"):
        active_sources.append("Blogs")

    sources_str = ", ".join(active_sources) if active_sources else "无"

    lines = [
        f"# 🌐 全球情报日报 (Global Intel Briefing)",
        f"**日期:** {date_str}",
        f"**生成时间:** {datetime.now().strftime('%H:%M')}",
        f"**数据源:** {sources_str}",
        "",
    ]

    # --- Executive Summary (AI 生成) ---
    exec_summary = generate_executive_summary(intel)
    if exec_summary:
        lines.append("## 📌 今日要点 (Executive Summary)")
        lines.append("")
        lines.append(exec_summary)
        lines.append("")

    lines.append("---")
    lines.append("")

    # --- Tech Trends (仅在有数据时显示) ---
    if intel.get("tech_trends"):
        lines.append("## 🛠️ 技术趋势 (Tech Trends)")
        lines.append("> Hacker News + GitHub Trending\n")
        for i, item in enumerate(intel["tech_trends"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            time_str = item.get("time", "")
            cat = item.get("category", "")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"📍 {cat} | 🔥 {heat} | 🕒 {time_str}")
            lines.append("")

    # --- Capital Flow (仅在有数据时显示) ---
    if intel.get("capital_flow"):
        lines.append("## 💰 资本动向 (Capital Flow)")
        lines.append("> 36Kr + 华尔街见闻\n")
        for i, item in enumerate(intel["capital_flow"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            time_str = item.get("time", "")
            cat = item.get("category", "")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"📍 {cat} | 🕒 {time_str}")
            lines.append("")

    # --- Research (ArXiv) (仅在有数据时显示) ---
    if intel.get("research"):
        lines.append("## 📚 学术前沿 (Research)")
        lines.append("> ArXiv AI/ML Papers\n")
        for i, item in enumerate(intel["research"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            authors = item.get("authors", "")
            time_str = item.get("time", "")
            summary = item.get("summary", "").replace("\n", " ")

            brief_cn = translate_to_chinese(summary[:200], max_chars=80) if summary else ""
            if GEMINI_AVAILABLE and summary:
                time.sleep(GEMINI_RATE_LIMIT_DELAY)
            detail_cn = translate_to_chinese(summary, max_chars=2000) if summary else ""

            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")

            lines.append(f"👤 {authors} | 📅 {time_str}")

            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")

            lines.append("")

    # --- Product Gems (仅在有数据时显示) ---
    if intel.get("product_gems"):
        lines.append("## 💎 产品精选 (Product Gems)")
        lines.append("> Product Hunt Today\n")
        for i, item in enumerate(intel["product_gems"][:8], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            tagline = item.get("tagline", "")
            grok_review = item.get("grok_review")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"> {tagline}")
            lines.append(f"🔥 {heat}")
            lines.append("")

            if grok_review:
                lines.append(f"> **🦅 Grok 舆情核查**: {grok_review}")
                lines.append("")

    # --- Social (X/Twitter) (仅在有数据时显示) ---
    if intel.get("social"):
        lines.append("## 🐦 社交热议 (Social)")
        lines.append("> X (Twitter) - AI/Tech Discussions\n")
        for item in intel["social"]:
            if item.get("type") == "markdown_report":
                lines.append(f"> 来源: {item.get('source', 'X')}\n")
                lines.append(item.get("content", "*无内容*"))
                lines.append("")
            else:
                title = item.get("title", "")
                url = item.get("url", "#")
                author = item.get("author", "")
                heat = item.get("heat", "")

                lines.append(f"### {author}")
                lines.append(f"> {title}")
                lines.append(f"❤️ {heat} | 🔗 [Link]({url})")
                lines.append("")

    # --- Community (仅在有数据时显示) ---
    if intel.get("community"):
        lines.append("## 🗣️ 社区热点 (Community)")
        lines.append("> V2EX 热门\n")
        for i, item in enumerate(intel["community"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"💬 {heat}")
            lines.append("")

    # --- XHS Directives (仅在有数据时显示，且过滤掉纯搜索链接) ---
    # 注：XHS Radar 目前只生成搜索链接，价值较低，暂时隐藏
    # 如果后续实现真正的内容抓取，可以取消注释
    # if intel.get("xhs_directives"):
    #     lines.append("## 📕 小红书雷达 (XHS Radar)")
    #     ...

    # --- Insights (HN Top Blogs) (仅在有数据时显示) ---
    if intel.get("insights"):
        lines.append("## 💡 深度洞察 (Insights)")
        lines.append("> HN Top Blogs - 精选技术博客\n")
        for i, item in enumerate(intel["insights"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            author = item.get("author", "")
            time_str = item.get("time", "")
            rss_content = item.get("content", "").replace("\n", " ")

            # Jina full-content analysis
            source_text = ""
            if JINA_AVAILABLE and url and url.startswith("http"):
                logger.info(f"[Insights {i}] Fetching full content via Jina...")
                full_content = fetch_full_content(url)
                if full_content and len(full_content) > 200:
                    source_text = full_content
                    logger.info(f"[Insights {i}] Using Jina full content ({len(source_text)} chars)")

            if not source_text and rss_content:
                source_text = rss_content
                logger.debug(f"[Insights {i}] Fallback to RSS content ({len(source_text)} chars)")

            brief_cn = ""
            detail_cn = ""
            if source_text and GEMINI_AVAILABLE:
                brief_cn = summarize_blog_article(source_text, mode="brief")
                time.sleep(GEMINI_RATE_LIMIT_DELAY)
                detail_cn = summarize_blog_article(source_text, mode="detail")

            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")

            lines.append(f"📍 {author}{' | 📅 ' + time_str if time_str else ''}")

            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")

            lines.append("")

    lines.append("---")
    lines.append("*报告由 Unified Intelligence Engine V2 自动生成*")

    return "\n".join(lines)


__all__ = ['generate_report']

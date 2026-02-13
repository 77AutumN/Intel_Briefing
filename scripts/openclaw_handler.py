#!/usr/bin/env python3
"""
OpenClaw Handler - Intel Briefing 的 OpenClaw 适配层

此脚本作为 OpenClaw Skill 的入口点，负责：
1. 调用核心数据采集逻辑
2. 生成结构化报告（不含 AI 增强，交给 OpenClaw 处理）
3. 输出报告内容供 OpenClaw 进一步处理或推送
"""

import os
import sys
import json
import argparse
import datetime
import logging

# 添加项目根目录到 Python 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from src.intel_collector import fetch_all_sources
from src.config import setup_logging

logger = logging.getLogger(__name__)

# 报告输出目录
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports", "daily_briefings")


def generate_basic_report(intel: dict, date_str: str) -> str:
    """
    生成基础 Markdown 报告（不含 AI 增强）。

    AI 摘要、翻译等功能交给 OpenClaw 的 LLM 处理，
    这里只负责数据结构化和格式化。
    """
    from datetime import datetime as dt

    # 计算活跃数据源
    active_sources = []
    if intel.get("tech_trends"):
        active_sources.extend(["HN", "GitHub"])
    if intel.get("capital_flow"):
        active_sources.extend(["36Kr", "WallStreetCN"])
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
        "# 🌐 全球情报日报 (Global Intel Briefing)",
        f"**日期:** {date_str}",
        f"**生成时间:** {dt.now().strftime('%H:%M')}",
        f"**数据源:** {sources_str}",
        "",
        "---",
        "",
    ]

    # --- Tech Trends ---
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

    # --- Capital Flow ---
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

    # --- Research ---
    if intel.get("research"):
        lines.append("## 📚 学术前沿 (Research)")
        lines.append("> ArXiv AI/ML Papers\n")
        for i, item in enumerate(intel["research"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            authors = item.get("authors", "")
            time_str = item.get("time", "")
            summary = item.get("summary", "").replace("\n", " ")[:200]
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"👤 {authors} | 📅 {time_str}")
            if summary:
                lines.append(f"> {summary}...")
            lines.append("")

    # --- Product Gems ---
    if intel.get("product_gems"):
        lines.append("## 💎 产品精选 (Product Gems)")
        lines.append("> Product Hunt Today\n")
        for i, item in enumerate(intel["product_gems"][:8], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            tagline = item.get("tagline", "")
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"> {tagline}")
            lines.append(f"🔥 {heat}")
            lines.append("")

    # --- Social ---
    if intel.get("social"):
        lines.append("## 🐦 社交热议 (Social)")
        lines.append("> X (Twitter) - AI/Tech Discussions\n")
        for item in intel["social"]:
            if item.get("type") == "markdown_report":
                lines.append(item.get("content", "*无内容*"))
            else:
                title = item.get("title", "")
                url = item.get("url", "#")
                author = item.get("author", "")
                heat = item.get("heat", "")
                lines.append(f"### {author}")
                lines.append(f"> {title}")
                lines.append(f"❤️ {heat} | 🔗 [Link]({url})")
            lines.append("")

    # --- Community ---
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

    # --- Insights ---
    if intel.get("insights"):
        lines.append("## 💡 深度洞察 (Insights)")
        lines.append("> HN Top Blogs\n")
        for i, item in enumerate(intel["insights"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            author = item.get("author", "")
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"📍 {author}")
            lines.append("")

    lines.append("---")
    lines.append("*报告由 Intel Briefing (OpenClaw Skill) 自动生成*")

    return "\n".join(lines)


def run(days: int = 1, output_format: str = "markdown") -> dict:
    """
    执行情报采集并生成报告。

    Args:
        days: 采集天数（1=日报，7=周报）
        output_format: 输出格式 ("markdown" | "json")

    Returns:
        包含报告内容和元数据的字典
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    if days == 1:
        report_title = f"每日商业情报简报: {date_str}"
        file_name = f"Morning_Report_{date_str}.md"
        limit = 15
    else:
        report_title = f"周期性情报简报 (过去 {days} 天): {date_str}"
        file_name = f"Weekly_Report_{days}Days_{date_str}.md"
        limit = 30

    logger.info(f"开始采集情报 - 周期: {days} 天")

    # 1. 数据采集
    intel = fetch_all_sources(limit_per_source=limit)

    # 2. 生成报告
    report_content = generate_basic_report(intel, date_str)
    final_content = f"# {report_title}\n\n" + report_content.replace(
        "# 🌐 全球情报日报 (Global Intel Briefing)", ""
    )

    # 3. 保存报告
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = os.path.join(REPORT_DIR, file_name)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"简报已生成: {report_file}")

    # 4. 返回结果
    result = {
        "success": True,
        "date": date_str,
        "days": days,
        "report_file": report_file,
        "report_title": report_title,
    }

    if output_format == "json":
        result["intel"] = intel
        result["report_content"] = final_content
    else:
        result["report_content"] = final_content

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Intel Briefing - OpenClaw Skill Handler"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=1,
        help="采集天数 (默认: 1)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式 (默认: markdown)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，只输出报告内容"
    )
    args = parser.parse_args()

    result = run(days=args.days, output_format=args.format)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.quiet:
        print(result["report_content"])
    else:
        print(f"\n✅ 报告已生成: {result['report_file']}")
        print(f"📅 日期: {result['date']}")
        print(f"📊 周期: {result['days']} 天")
        print("\n" + "=" * 50)
        print(result["report_content"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified Intelligence Fetcher - Operation Wide-Net V2
Combines news-aggregator-skill with ALL local sensors.
Outputs a magazine-style Morning Report.

Sources:
- External (news-aggregator): HN, GitHub, 36Kr, WallStreetCN, V2EX
- Local: Product Hunt, ArXiv, X (cache), XHS (manual directives)
"""

import sys
import os
import json
from datetime import datetime, timedelta

# --- Path Setup ---
# Add local src for sensors
LOCAL_SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if LOCAL_SRC_PATH not in sys.path:
    sys.path.insert(0, LOCAL_SRC_PATH)

# --- Imports: External (internalized in src/external/) ---
try:
    from external.fetch_news import (
        fetch_hackernews,
        fetch_github,
        fetch_36kr,
        fetch_wallstreetcn,
        fetch_v2ex,
        filter_items
    )
except ImportError as e:
    print(f"[ERROR] Cannot import fetch_news from src/external/: {e}")
    sys.exit(1)

# --- Imports: Local Sensors ---
try:
    from sensors.product_hunt import fetch_trending_products
    PH_AVAILABLE = True
except ImportError:
    PH_AVAILABLE = False
    print("[WARN] Product Hunt sensor not available, skipping.")

try:
    from sensors.arxiv_ai import fetch_ai_papers
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    print("[WARN] ArXiv sensor not available, skipping.")

try:
    from sensors.x_grok_sensor import fetch_grok_intel
    GROK_AVAILABLE = True
except ImportError:
    GROK_AVAILABLE = False
    print("[WARN] Grok (X/Twitter) sensor not available, skipping.")

try:
    from sensors.xhs_radar import XHSRadar
    XHS_AVAILABLE = True
except ImportError:
    XHS_AVAILABLE = False
    print("[WARN] XHS (Xiaohongshu) sensor not available, skipping.")

try:
    from sensors.hn_blogs import fetch_hn_blogs
    HN_BLOGS_AVAILABLE = True
except ImportError:
    HN_BLOGS_AVAILABLE = False
    print("[WARN] HN Top Blogs sensor not available, skipping.")

# --- Gemini Translator ---
try:
    from utils.gemini_translator import translate_to_chinese, summarize_blog_article
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- Jina Reader (Full Content Fetcher) ---
try:
    from utils.jina_reader import fetch_full_content
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False
    print("[WARN] Jina Reader not available, using RSS description only.")
    print("[WARN] Gemini translator not available, using English summaries.")
    def translate_to_chinese(text, max_chars=100):
        return text[:max_chars] + "..." if len(text) > max_chars else text

# --- Anti-Hallucination: Link Verifier ---
try:
    from utils.verifier import verify_link
    import re
    VERIFIER_AVAILABLE = True
except ImportError:
    VERIFIER_AVAILABLE = False
    print("[WARN] Link verifier not available, skipping hallucination checks.")


def validate_grok_report(markdown_content: str) -> str:
    """
    Anti-Hallucination Layer: Extract and validate all links in Grok's output.
    Appends warning to invalid links.
    """
    if not VERIFIER_AVAILABLE:
        return markdown_content
    
    # Extract all markdown links
    link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(link_pattern, markdown_content)
    
    if not matches:
        return markdown_content
    
    print(f"  [*] Validating {len(matches)} links from Grok output...")
    validated_content = markdown_content
    
    for title, url in matches:
        # Skip known-good domains that block HEAD requests
        skip_domains = ['twitter.com', 'x.com', 'weibo.com', 'xiaohongshu.com']
        if any(domain in url for domain in skip_domains):
            continue
        
        is_valid = verify_link(url)
        if not is_valid:
            # Append warning to the link
            old_link = f"[{title}]({url})"
            new_link = f"[{title}]({url}) **(⚠️ 链接验证失败/404)**"
            validated_content = validated_content.replace(old_link, new_link)
            print(f"    ❌ INVALID: {url}")
        else:
            print(f"    ✅ Valid: {url[:50]}...")
    
    return validated_content


def fetch_all_sources(limit_per_source: int = 10) -> dict:
    """Fetch from all configured sources."""
    intel = {
        "tech_trends": [],      # HN + GitHub
        "capital_flow": [],     # 36Kr + WallStreetCN
        "product_gems": [],     # Product Hunt
        "community": [],        # V2EX
        "research": [],         # ArXiv
        "social": [],           # X (Twitter)
        "xhs_directives": [],   # XHS (manual search links)
        "insights": []          # HN Top Blogs (深度洞察)
    }
    
    # ========== EXTERNAL SOURCES (news-aggregator-skill) ==========
    print("[*] Fetching Hacker News...")
    try:
        hn_items = fetch_hackernews(limit=limit_per_source)
        intel["tech_trends"].extend([
            {**item, "category": "Hacker News"} for item in hn_items
        ])
    except Exception as e:
        print(f"  [WARN] HN failed: {e}")
    
    print("[*] Fetching GitHub Trending...")
    try:
        gh_items = fetch_github(limit=limit_per_source)
        intel["tech_trends"].extend([
            {**item, "category": "GitHub"} for item in gh_items
        ])
    except Exception as e:
        print(f"  [WARN] GitHub failed: {e}")
    
    print("[*] Fetching 36Kr...")
    try:
        kr_items = fetch_36kr(limit=limit_per_source)
        intel["capital_flow"].extend([
            {**item, "category": "36Kr"} for item in kr_items
        ])
    except Exception as e:
        print(f"  [WARN] 36Kr failed: {e}")
    
    print("[*] Fetching WallStreetCN...")
    try:
        ws_items = fetch_wallstreetcn(limit=limit_per_source)
        intel["capital_flow"].extend([
            {**item, "category": "WallStreetCN"} for item in ws_items
        ])
    except Exception as e:
        print(f"  [WARN] WallStreetCN failed: {e}")
    
    print("[*] Fetching V2EX Hot...")
    try:
        v2_items = fetch_v2ex(limit=limit_per_source)
        intel["community"].extend([
            {**item, "category": "V2EX"} for item in v2_items
        ])
    except Exception as e:
        print(f"  [WARN] V2EX failed: {e}")
    
    # ========== LOCAL SENSORS ==========
    if PH_AVAILABLE:
        print("[*] Fetching Product Hunt...")
        try:
            ph_products = fetch_trending_products(limit_per_source)
            for i, p in enumerate(ph_products):
                product_data = {
                    "source": "Product Hunt",
                    "category": "Product Hunt",
                    "title": p.name,
                    "url": p.url,
                    "heat": f"{p.votes_count} votes",
                    "time": "Today",
                    "tagline": p.tagline,
                    "grok_review": None  # Will be filled for top 3
                }
                
                # Grok Sentiment Verification for Top 3 Products
                if GROK_AVAILABLE and i < 3:
                    print(f"  [*] Grok 舆情核查: {p.name}...")
                    try:
                        grok_prompt = f"""You are an X (Twitter) analyst. Search X for the product "{p.name}" with tagline "{p.tagline}".
Provide a market sentiment summary in Simplified Chinese (简体中文), including:
1. Overall sentiment (positive/negative/mixed)
2. 3-5 key findings from real users/developers/founders on X
3. Pros and Cons

Format: Use numbered list. For each finding, mention who said it (e.g., @username or role like "a developer").
Keep it concise but informative. If no data found, say "暂无X平台讨论数据"."""
                        grok_result = fetch_grok_intel(f"PH: {p.name}", override_prompt=grok_prompt)
                        if grok_result and "Error" not in grok_result:
                            product_data["grok_review"] = grok_result
                            print(f"    ✅ Grok returned sentiment for {p.name}")
                        else:
                            print(f"    ⚠️ Grok returned no data for {p.name}")
                    except Exception as e:
                        print(f"    ⚠️ Grok failed for {p.name}: {e}")
                
                intel["product_gems"].append(product_data)
        except Exception as e:
            print(f"  [WARN] Product Hunt failed: {e}")
    
    if ARXIV_AVAILABLE:
        print("[*] Fetching ArXiv AI papers...")
        try:
            papers = fetch_ai_papers(limit=limit_per_source)
            for p in papers:
                intel["research"].append({
                    "source": "ArXiv",
                    "category": "ArXiv",
                    "title": p.title,
                    "url": p.url,
                    "authors": ", ".join(p.authors[:2]),
                    "time": p.published,
                    "categories": ", ".join(p.categories[:2]),
                    "summary": p.summary
                })
        except Exception as e:
            print(f"  [WARN] ArXiv failed: {e}")
    
    if GROK_AVAILABLE:
        print("[*] Fetching X (Twitter) via Grok API...")
        try:
            # Query Grok for AI/Tech trends on X
            grok_report = fetch_grok_intel("AI Agents, LLM, Tech Startups")
            if grok_report and "Error" not in grok_report:
                # Anti-Hallucination: Validate all links in Grok's output
                validated_report = validate_grok_report(grok_report)
                intel["social"].append({
                    "source": "X (via Grok)",
                    "category": "X/Grok",
                    "content": validated_report,
                    "type": "markdown_report"
                })
                print("  [INFO] Grok returned X intelligence report (links validated).")
            else:
                print(f"  [WARN] Grok returned no data or error.")
        except Exception as e:
            print(f"  [WARN] Grok API failed: {e}")
    
    if XHS_AVAILABLE:
        print("[*] Generating XHS search directives...")
        try:
            radar = XHSRadar()
            leads = radar.fetch_leads()
            for lead in leads[:8]:  # Top 8 search queries
                intel["xhs_directives"].append({
                    "source": "小红书",
                    "category": "XHS",
                    "title": lead.title,
                    "url": lead.url,
                    "summary": lead.summary
                })
        except Exception as e:
            print(f"  [WARN] XHS failed: {e}")
    
    # ========== HN TOP BLOGS (INSIGHTS) ==========
    if HN_BLOGS_AVAILABLE:
        print("[*] Fetching HN Top Blogs (Insights)...")
        try:
            blog_articles = fetch_hn_blogs(limit=5)
            for article in blog_articles:
                intel["insights"].append({
                    "source": "HN Top Blogs",
                    "category": "HN Blogs",
                    "title": article.title,
                    "url": article.url,
                    "author": article.source,
                    "time": article.pub_date,
                    "content": article.content  # NEW: Article description from RSS
                })
        except Exception as e:
            print(f"  [WARN] HN Blogs failed: {e}")
    
    return intel


def generate_report(intel: dict, date_str: str) -> str:
    """Generate magazine-style markdown report."""
    lines = [
        f"# 🌐 全球情报日报 (Global Intel Briefing)",
        f"**日期:** {date_str}",
        f"**生成时间:** {datetime.now().strftime('%H:%M')}",
        f"**数据源:** HN, GitHub, 36Kr, WallStreetCN, V2EX, PH, ArXiv, X, XHS",
        "",
        "---",
        ""
    ]
    
    # --- Tech Trends ---
    lines.append("## 🛠️ 技术趋势 (Tech Trends)")
    lines.append("> Hacker News + GitHub Trending\n")
    
    if intel.get("tech_trends"):
        for i, item in enumerate(intel["tech_trends"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            time_str = item.get("time", "")
            cat = item.get("category", "")
            
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"📍 {cat} | 🔥 {heat} | 🕒 {time_str}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")
    
    # --- Capital Flow ---
    lines.append("## 💰 资本动向 (Capital Flow)")
    lines.append("> 36Kr + 华尔街见闻\n")
    
    if intel.get("capital_flow"):
        for i, item in enumerate(intel["capital_flow"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            time_str = item.get("time", "")
            cat = item.get("category", "")
            
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"📍 {cat} | 🕒 {time_str}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")
    
    # --- Research (ArXiv) ---
    lines.append("## 📚 学术前沿 (Research)")
    lines.append("> ArXiv AI/ML Papers\n")
    
    if intel.get("research"):
        for i, item in enumerate(intel["research"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            authors = item.get("authors", "")
            time_str = item.get("time", "")
            summary = item.get("summary", "").replace("\n", " ")
            
            # Two-Tier Summary Logic (Chinese Translation)
            # 1. Brief: Translate first ~100 chars to Chinese (~80 汉字)
            brief_cn = translate_to_chinese(summary[:200], max_chars=80) if summary else ""
            
            # 添加延迟以避免 API 限速 (每篇论文间隔1.5秒)
            import time
            time.sleep(1.5)
            
            # 2. Detail: Translate full summary to Chinese (allow complete translation)
            detail_cn = translate_to_chinese(summary, max_chars=2000) if summary else ""
            
            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")
            
            lines.append(f"👤 {authors} | 📅 {time_str}")
            
            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")
            
            lines.append("")
    else:
        lines.append("*暂无数据*\n")
    
    # --- Product Gems ---
    lines.append("## 💎 产品精选 (Product Gems)")
    lines.append("> Product Hunt Today\n")
    
    if intel.get("product_gems"):
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
            
            # Add Grok sentiment review if available (for top 3)
            if grok_review:
                lines.append(f"> **🦅 Grok 舆情核查**: {grok_review}")
                lines.append("")
    else:
        lines.append("*暂无数据 (Product Hunt API 可能需要配置)*\n")
    
    # --- Social (X/Twitter) ---
    lines.append("## 🐦 社交热议 (Social)")
    lines.append("> X (Twitter) - AI/Tech Discussions\n")
    
    if intel.get("social"):
        for item in intel["social"]:
            # Check if it's a Grok markdown report
            if item.get("type") == "markdown_report":
                lines.append(f"> 来源: {item.get('source', 'X')}\n")
                lines.append(item.get("content", "*无内容*"))
                lines.append("")
            else:
                # Old format (individual posts)
                title = item.get("title", "")
                url = item.get("url", "#")
                author = item.get("author", "")
                heat = item.get("heat", "")
                
                lines.append(f"### {author}")
                lines.append(f"> {title}")
                lines.append(f"❤️ {heat} | 🔗 [Link]({url})")
                lines.append("")
    else:
        lines.append("*暂无数据 (需要配置 XAI_API_KEY)*\n")
    
    # --- Community ---
    lines.append("## 🗣️ 社区热点 (Community)")
    lines.append("> V2EX 热门\n")
    
    if intel.get("community"):
        for i, item in enumerate(intel["community"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"💬 {heat}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")
    
    # --- XHS Directives (Manual) ---
    lines.append("## 📕 小红书雷达 (XHS Radar)")
    lines.append("> 手动搜索指令 (点击链接进入搜索页)\n")
    
    if intel.get("xhs_directives"):
        for i, item in enumerate(intel["xhs_directives"][:6], 1):
            title = item.get("title", "")
            url = item.get("url", "#")
            summary = item.get("summary", "")
            
            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"> {summary[:80]}...")
            lines.append("")
    else:
        lines.append("*XHS 传感器不可用*\n")
    
    # --- Insights (HN Top Blogs) ---
    lines.append("## 💡 深度洞察 (Insights)")
    lines.append("> HN Top Blogs - 精选技术博客\n")
    
    if intel.get("insights"):
        for i, item in enumerate(intel["insights"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            author = item.get("author", "")
            time_str = item.get("time", "")
            rss_content = item.get("content", "").replace("\n", " ")
            
            # === JINA FULL-CONTENT ANALYSIS ===
            # Try to fetch full article content via Jina Reader
            source_text = ""
            if JINA_AVAILABLE and url and url.startswith("http"):
                print(f"  [Insights {i}] Fetching full content via Jina...")
                full_content = fetch_full_content(url)
                if full_content and len(full_content) > 200:
                    source_text = full_content
                    print(f"  [Insights {i}] Using Jina full content ({len(source_text)} chars)")
            
            # Fallback to RSS description if Jina failed
            if not source_text and rss_content:
                source_text = rss_content
                print(f"  [Insights {i}] Fallback to RSS content ({len(source_text)} chars)")
            
            # Two-Tier Summary Logic (Deep Analysis)
            brief_cn = ""
            detail_cn = ""
            if source_text and GEMINI_AVAILABLE:
                import time
                
                # 1. Brief: One-sentence Chinese hook
                brief_cn = summarize_blog_article(source_text, mode="brief")
                time.sleep(1.5)  # Rate limit protection
                
                # 2. Detail: Structured intelligence-style analysis
                detail_cn = summarize_blog_article(source_text, mode="detail")
            
            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")
            
            lines.append(f"📍 {author}{' | 📅 ' + time_str if time_str else ''}")
            
            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")
            
            lines.append("")
    else:
        lines.append("*暂无数据 (HN Blogs 传感器不可用)*\n")
    
    lines.append("---")
    lines.append("*报告由 Unified Intelligence Engine V2 自动生成*")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unified Intel Fetcher V2")
    parser.add_argument("--limit", type=int, default=10, help="Items per source")
    parser.add_argument("--test", action="store_true", help="Test mode (1 item per source)")
    parser.add_argument("--output", type=str, help="Custom output path")
    args = parser.parse_args()
    
    limit = 1 if args.test else args.limit
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'='*50}")
    print(f"  Unified Intelligence Fetcher V2")
    print(f"  Date: {date_str} | Limit: {limit}/source")
    print(f"  Sources: HN, GitHub, 36Kr, WS, V2EX, PH, ArXiv, X, XHS")
    print(f"{'='*50}\n")
    
    # Fetch
    intel = fetch_all_sources(limit_per_source=limit)
    
    # Generate report
    report = generate_report(intel, date_str)
    
    # Save
    if args.output:
        output_path = args.output
    else:
        reports_dir = os.path.join(os.path.dirname(__file__), "reports", "daily_briefings")
        os.makedirs(reports_dir, exist_ok=True)
        
        if args.test:
            output_path = os.path.join(reports_dir, "Morning_Report_TEST.md")
        else:
            output_path = os.path.join(reports_dir, f"Morning_Report_{date_str}.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n[SUCCESS] Report saved to: {output_path}")
    

    
    print(f"\n--- Preview (first 40 lines) ---\n")
    for line in report.split("\n")[:40]:
        print(line)
    

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intel Collector - 数据采集模块
负责从所有传感器收集情报数据

从 fetch_unified_intel.py 重构而来
"""

import sys
import os
import re

# --- Path Setup ---
# Add local src for sensors
LOCAL_SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
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

# --- Anti-Hallucination: Link Verifier ---
try:
    from utils.verifier import verify_link
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


__all__ = ['fetch_all_sources', 'validate_grok_report']

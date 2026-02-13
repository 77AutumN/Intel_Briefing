#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intel Collector - 数据采集模块（唯一入口）
负责从所有传感器并行收集情报数据

优化点:
- 使用 logging 替代 print
- 使用 concurrent.futures 并行化 API 调用
- 统一错误处理
- 去重逻辑
"""

import sys
import os
import re
import logging
import concurrent.futures
from typing import Dict, List

logger = logging.getLogger(__name__)

# --- Path Setup ---
LOCAL_SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
if LOCAL_SRC_PATH not in sys.path:
    sys.path.insert(0, LOCAL_SRC_PATH)

# --- Imports: External ---
try:
    from external.fetch_news import (
        fetch_hackernews,
        fetch_github,
        fetch_36kr,
        fetch_wallstreetcn,
        fetch_v2ex,
    )
except ImportError as e:
    logger.error(f"Cannot import fetch_news from src/external/: {e}")
    sys.exit(1)

# --- Imports: Local Sensors (graceful degradation) ---
PH_AVAILABLE = False
ARXIV_AVAILABLE = False
GROK_AVAILABLE = False
XHS_AVAILABLE = False
HN_BLOGS_AVAILABLE = False
VERIFIER_AVAILABLE = False

try:
    from sensors.product_hunt import fetch_trending_products
    PH_AVAILABLE = True
except ImportError:
    logger.info("Product Hunt sensor not available, skipping.")

try:
    from sensors.arxiv_ai import fetch_ai_papers
    ARXIV_AVAILABLE = True
except ImportError:
    logger.info("ArXiv sensor not available, skipping.")

try:
    from sensors.x_grok_sensor import fetch_grok_intel
    GROK_AVAILABLE = True
except ImportError:
    logger.info("Grok (X/Twitter) sensor not available, skipping.")

try:
    from sensors.xhs_radar import XHSRadar
    XHS_AVAILABLE = True
except ImportError:
    logger.info("XHS (Xiaohongshu) sensor not available, skipping.")

try:
    from sensors.hn_blogs import fetch_hn_blogs
    HN_BLOGS_AVAILABLE = True
except ImportError:
    logger.info("HN Top Blogs sensor not available, skipping.")

try:
    from utils.verifier import verify_link
    VERIFIER_AVAILABLE = True
except ImportError:
    logger.info("Link verifier not available, skipping hallucination checks.")


def validate_grok_report(markdown_content: str) -> str:
    """Anti-Hallucination Layer: Extract and validate all links in Grok's output."""
    if not VERIFIER_AVAILABLE:
        return markdown_content

    link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(link_pattern, markdown_content)
    if not matches:
        return markdown_content

    logger.info(f"Validating {len(matches)} links from Grok output...")
    validated_content = markdown_content
    skip_domains = ['twitter.com', 'x.com', 'weibo.com', 'xiaohongshu.com']

    for title, url in matches:
        if any(domain in url for domain in skip_domains):
            continue
        is_valid = verify_link(url)
        if not is_valid:
            old_link = f"[{title}]({url})"
            new_link = f"[{title}]({url}) **(⚠️ 链接验证失败/404)**"
            validated_content = validated_content.replace(old_link, new_link)
            logger.warning(f"INVALID link: {url}")
        else:
            logger.debug(f"Valid link: {url[:50]}...")

    return validated_content


def _fetch_external_sources(limit: int) -> Dict[str, List]:
    """并行抓取所有外部数据源（HN, GitHub, 36Kr, WallStreetCN, V2EX）。"""
    results = {"tech_trends": [], "capital_flow": [], "community": []}

    source_tasks = {
        "hn": (fetch_hackernews, "tech_trends", "Hacker News"),
        "github": (fetch_github, "tech_trends", "GitHub"),
        "36kr": (fetch_36kr, "capital_flow", "36Kr"),
        "wallstreetcn": (fetch_wallstreetcn, "capital_flow", "WallStreetCN"),
        "v2ex": (fetch_v2ex, "community", "V2EX"),
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {}
        for key, (func, category, name) in source_tasks.items():
            future = executor.submit(func, limit=limit)
            future_map[future] = (category, name)

        for future in concurrent.futures.as_completed(future_map):
            category, name = future_map[future]
            try:
                items = future.result()
                results[category].extend([{**item, "category": name} for item in items])
                logger.info(f"{name}: fetched {len(items)} items")
            except Exception as e:
                logger.warning(f"{name} failed: {e}")

    return results


def _fetch_product_hunt(limit: int) -> List[Dict]:
    """Fetch Product Hunt with optional Grok sentiment analysis."""
    if not PH_AVAILABLE:
        return []
    products_data = []
    try:
        ph_products = fetch_trending_products(limit)
        for i, p in enumerate(ph_products):
            product_data = {
                "source": "Product Hunt", "category": "Product Hunt",
                "title": p.name, "url": p.url,
                "heat": f"{p.votes_count} votes", "time": "Today",
                "tagline": p.tagline, "grok_review": None,
            }
            if GROK_AVAILABLE and i < 3:
                logger.info(f"Grok sentiment check: {p.name}...")
                try:
                    grok_prompt = (
                        f'You are an X (Twitter) analyst. Search X for the product "{p.name}" '
                        f'with tagline "{p.tagline}". Provide a market sentiment summary in '
                        f'Simplified Chinese, including: 1. Overall sentiment 2. 3-5 key findings '
                        f'3. Pros and Cons. Keep it concise. If no data, say "暂无X平台讨论数据".'
                    )
                    grok_result = fetch_grok_intel(f"PH: {p.name}", override_prompt=grok_prompt)
                    if grok_result and "Error" not in grok_result:
                        product_data["grok_review"] = grok_result
                except Exception as e:
                    logger.warning(f"Grok failed for {p.name}: {e}")
            products_data.append(product_data)
    except Exception as e:
        logger.warning(f"Product Hunt failed: {e}")
    return products_data


def _fetch_arxiv(limit: int) -> List[Dict]:
    if not ARXIV_AVAILABLE:
        return []
    research = []
    try:
        papers = fetch_ai_papers(limit=limit)
        for p in papers:
            research.append({
                "source": "ArXiv", "category": "ArXiv",
                "title": p.title, "url": p.url,
                "authors": ", ".join(p.authors[:2]),
                "time": p.published,
                "categories": ", ".join(p.categories[:2]),
                "summary": p.summary,
            })
    except Exception as e:
        logger.warning(f"ArXiv failed: {e}")
    return research


def _fetch_grok_social() -> List[Dict]:
    if not GROK_AVAILABLE:
        return []
    social = []
    try:
        grok_report = fetch_grok_intel("AI Agents, LLM, Tech Startups")
        if grok_report and "Error" not in grok_report:
            validated_report = validate_grok_report(grok_report)
            social.append({
                "source": "X (via Grok)", "category": "X/Grok",
                "content": validated_report, "type": "markdown_report",
            })
            logger.info("Grok returned X intelligence report (links validated).")
    except Exception as e:
        logger.warning(f"Grok API failed: {e}")
    return social


def _fetch_xhs() -> List[Dict]:
    if not XHS_AVAILABLE:
        return []
    directives = []
    try:
        radar = XHSRadar()
        leads = radar.fetch_leads()
        for lead in leads[:8]:
            directives.append({
                "source": "小红书", "category": "XHS",
                "title": lead.title, "url": lead.url, "summary": lead.summary,
            })
    except Exception as e:
        logger.warning(f"XHS failed: {e}")
    return directives


def _fetch_hn_blogs(limit: int) -> List[Dict]:
    if not HN_BLOGS_AVAILABLE:
        return []
    insights = []
    try:
        blog_articles = fetch_hn_blogs(limit=limit)
        for article in blog_articles:
            insights.append({
                "source": "HN Top Blogs", "category": "HN Blogs",
                "title": article.title, "url": article.url,
                "author": article.source, "time": article.pub_date,
                "content": article.content,
            })
    except Exception as e:
        logger.warning(f"HN Blogs failed: {e}")
    return insights


def _dedup_items(items: List[Dict], key: str = "title") -> List[Dict]:
    """去重：基于标题去除重复条目。"""
    seen = set()
    unique = []
    for item in items:
        title = item.get(key, "").strip().lower()
        if title and title not in seen:
            seen.add(title)
            unique.append(item)
        elif not title:
            unique.append(item)
    return unique


def fetch_all_sources(limit_per_source: int = 10) -> dict:
    """
    从所有配置的数据源并行抓取情报。
    使用 ThreadPoolExecutor 并行化独立的数据源请求。
    """
    logger.info(f"Starting fetch from all sources (limit={limit_per_source})...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_external = executor.submit(_fetch_external_sources, limit_per_source)
        future_ph = executor.submit(_fetch_product_hunt, limit_per_source)
        future_arxiv = executor.submit(_fetch_arxiv, limit_per_source)
        future_social = executor.submit(_fetch_grok_social)
        future_xhs = executor.submit(_fetch_xhs)
        future_blogs = executor.submit(_fetch_hn_blogs, 5)

        external = future_external.result()
        ph_data = future_ph.result()
        arxiv_data = future_arxiv.result()
        social_data = future_social.result()
        xhs_data = future_xhs.result()
        blog_data = future_blogs.result()

    intel = {
        "tech_trends": _dedup_items(external.get("tech_trends", [])),
        "capital_flow": _dedup_items(external.get("capital_flow", [])),
        "product_gems": ph_data,
        "community": _dedup_items(external.get("community", [])),
        "research": arxiv_data,
        "social": social_data,
        "xhs_directives": xhs_data,
        "insights": blog_data,
    }

    total = sum(len(v) for v in intel.values())
    logger.info(f"Fetch complete: {total} total items collected")
    return intel


__all__ = ['fetch_all_sources', 'validate_grok_report']
